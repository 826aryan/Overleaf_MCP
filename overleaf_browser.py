import asyncio
import os
import re
import time
from pathlib import Path
from typing import Dict, Any, List, Optional
from playwright.async_api import async_playwright, BrowserContext, Page, Playwright
from config import OVERLEAF_PROFILE_DIR, OVERLEAF_OUTPUT_DIR, HEADLESS, BASE_DIR

class OverleafBrowserManager:
    """
    Manages Playwright browser automation for Overleaf with persistent authentication.
    """
    def __init__(self, headless: bool = HEADLESS):
        self.headless = headless
        self._playwright: Optional[Playwright] = None
        self._context: Optional[BrowserContext] = None
        self._page: Optional[Page] = None
        self._current_project_id: Optional[str] = None
        self._lock = asyncio.Lock()

    async def _ensure_browser(self) -> Page:
        """Initializes or returns existing browser session supporting cloud deployment state."""
        if self._page and not self._page.is_closed():
            return self._page

        if not self._playwright:
            self._playwright = await async_playwright().start()

        chromium_args = [
            "--no-sandbox",
            "--disable-setuid-sandbox",
            "--disable-dev-shm-usage",
            "--disable-gpu",
            "--disable-blink-features=AutomationControlled",
        ]

        # 1. Check for simple session cookie (Zero-install deployment)
        session_cookie = os.getenv("OVERLEAF_SESSION_COOKIE")
        if session_cookie:
            browser_instance = await self._playwright.chromium.launch(
                headless=self.headless,
                args=chromium_args
            )
            self._context = await browser_instance.new_context(
                viewport={"width": 1440, "height": 900},
                accept_downloads=True,
            )
            
            # Robust cookie parser: strips whitespace, semicolons, quotes, handles key=value pairs
            raw = session_cookie.strip('\"\' \n\r\t')
            parsed_cookies = []
            parts = [p.strip() for p in raw.split(';') if p.strip()]
            for part in parts:
                if '=' in part:
                    k, v = part.split('=', 1)
                    k, v = k.strip(), v.strip('\"\' \n\r\t')
                    if k and v:
                        parsed_cookies.append({'name': k, 'value': v, 'url': 'https://www.overleaf.com'})
                else:
                    v = part.strip('\"\' \n\r\t')
                    if v:
                        parsed_cookies.append({'name': 'overleaf_session', 'value': v, 'url': 'https://www.overleaf.com'})
                        parsed_cookies.append({'name': 'v1_session', 'value': v, 'url': 'https://www.overleaf.com'})

            if parsed_cookies:
                await self._context.add_cookies(parsed_cookies)

            self._page = await self._context.new_page()
            return self._page

        # 2. Check for base64 storage state
        state_file_path = BASE_DIR / "storage_state.json"
        b64_env = os.getenv("OVERLEAF_STORAGE_STATE_B64")
        if b64_env and not state_file_path.exists():
            import base64
            try:
                decoded = base64.b64decode(b64_env).decode("utf-8")
                state_file_path.write_text(decoded, encoding="utf-8")
            except Exception as e:
                print(f"Warning: Failed to decode OVERLEAF_STORAGE_STATE_B64: {e}")

        # If a storage_state.json exists (cloud deployment)
        if state_file_path.exists():
            browser_instance = await self._playwright.chromium.launch(
                headless=self.headless,
                args=chromium_args
            )
            # Sanitize storage state: keep only overleaf cookies and fix invalid sameSite combos
            sanitized_state = self._sanitize_storage_state(state_file_path)
            self._context = await browser_instance.new_context(
                storage_state=sanitized_state,
                viewport={"width": 1440, "height": 900},
                accept_downloads=True,
            )
            self._page = await self._context.new_page()
            return self._page

        # Fallback to persistent profile
        self._context = await self._playwright.chromium.launch_persistent_context(
            user_data_dir=str(OVERLEAF_PROFILE_DIR),
            headless=self.headless,
            args=chromium_args,
            viewport={"width": 1440, "height": 900},
            accept_downloads=True,
        )

        pages = self._context.pages
        self._page = pages[0] if pages else await self._context.new_page()
        return self._page

    def _sanitize_storage_state(self, state_file_path: Path) -> Dict[str, Any]:
        """
        Reads storage_state.json and returns a sanitized dict safe for Playwright.
        - Filters cookies to only overleaf.com domain
        - Fixes invalid sameSite + secure combinations
        - Ensures required cookie fields are present
        """
        import json
        raw = json.loads(state_file_path.read_text(encoding="utf-8"))
        
        valid_same_sites = {"Strict", "Lax", "None"}
        sanitized_cookies = []
        
        for cookie in raw.get("cookies", []):
            domain = cookie.get("domain", "")
            # Only keep Overleaf cookies
            if "overleaf.com" not in domain:
                continue
            
            # Ensure required fields exist
            if not cookie.get("name") or cookie.get("value") is None:
                continue

            # Fix sameSite: "None" must have secure=true per spec
            same_site = cookie.get("sameSite", "Lax")
            if same_site not in valid_same_sites:
                same_site = "Lax"
            if same_site == "None":
                cookie["secure"] = True
            cookie["sameSite"] = same_site
            
            # Ensure domain+path present (Playwright requires either url or domain+path)
            if not cookie.get("path"):
                cookie["path"] = "/"
            
            sanitized_cookies.append(cookie)
        
        return {
            "cookies": sanitized_cookies,
            "origins": raw.get("origins", [])
        }

    async def check_auth_status(self) -> Dict[str, Any]:
        """Checks if the user has an active authenticated session on Overleaf."""
        async with self._lock:
            try:
                page = await self._ensure_browser()
                await page.goto("https://www.overleaf.com/project", wait_until="domcontentloaded", timeout=45000)
                await asyncio.sleep(2)
                url = page.url
                if "/login" in url:
                    return {
                        "authenticated": False,
                        "url": url,
                        "message": "User is not logged in. Set OVERLEAF_STORAGE_STATE_B64 or OVERLEAF_SESSION_COOKIE in Railway Variables."
                    }
                return {
                    "authenticated": True,
                    "url": url,
                    "message": "Authenticated successfully with Overleaf."
                }
            except Exception as e:
                import traceback
                return {
                    "authenticated": False,
                    "error": str(e),
                    "traceback": traceback.format_exc(),
                    "message": f"Browser navigation error: {e}"
                }
            return {
                "authenticated": True,
                "url": url,
                "message": "Authenticated successfully with Overleaf."
            }

    async def open_project(self, project_url_or_id: str) -> Dict[str, Any]:
        """
        Navigates to an Overleaf project by URL or Project ID.
        """
        async with self._lock:
            page = await self._ensure_browser()

            # Clean project ID / URL
            match = re.search(r"([0-9a-f]{24}|[0-9a-zA-Z_-]{16,})", project_url_or_id)
            if not match:
                target_url = project_url_or_id if project_url_or_id.startswith("http") else f"https://www.overleaf.com/project/{project_url_or_id}"
            else:
                proj_id = match.group(1)
                target_url = f"https://www.overleaf.com/project/{proj_id}"

            await page.goto(target_url, wait_until="domcontentloaded", timeout=45000)

            # Check if redirected to login
            if "/login" in page.url:
                return {
                    "success": False,
                    "error": "Redirected to login. Please run `python setup_auth.py` once to authenticate."
                }

            # Wait for editor elements to load
            try:
                await page.wait_for_selector(
                    ".cm-content, .cm-editor, .ace_editor, [role='region'][aria-label*='editor' i]",
                    timeout=20000
                )
            except Exception:
                # Might still be loading or viewing PDF
                pass

            await asyncio.sleep(2)
            title = await page.title()

            # Extract project ID from current URL
            current_match = re.search(r"/project/([0-9a-f]{24}|[0-9a-zA-Z_-]+)", page.url)
            if current_match:
                self._current_project_id = current_match.group(1)

            current_file = await self._get_current_filename(page)

            return {
                "success": True,
                "url": page.url,
                "project_title": title,
                "current_file": current_file,
                "project_id": self._current_project_id
            }

    async def _get_current_filename(self, page: Page) -> Optional[str]:
        """Attempts to find the name of the currently active file in the editor."""
        try:
            filename = await page.evaluate("""
                () => {
                    const activeTreeItem = document.querySelector('.file-tree-item.selected, [role="treeitem"][aria-selected="true"]');
                    if (activeTreeItem) {
                        const match = activeTreeItem.innerText.match(/[a-zA-Z0-9_-]+\\.[a-zA-Z0-9]+/);
                        if (match) return match[0];
                        return activeTreeItem.innerText.trim();
                    }
                    const activeTab = document.querySelector('.editor-tabs .active, [data-testid="file-name"]');
                    if (activeTab) {
                        return activeTab.innerText.trim();
                    }
                    return 'main.tex';
                }
            """)
            return filename
        except Exception:
            return "main.tex"

    async def list_files(self) -> Dict[str, Any]:
        """Lists actual project files (main.tex, cls, etc.) in the project file tree."""
        async with self._lock:
            page = await self._ensure_browser()
            try:
                files = await page.evaluate("""
                    () => {
                        const fileTree = document.querySelector('.file-tree, [aria-label*="File tree" i]');
                        const scope = fileTree || document;
                        const items = Array.from(scope.querySelectorAll('.file-tree-item, .entity-name, [role="treeitem"]'));
                        const names = [];
                        for (const el of items) {
                            const raw = (el.innerText || el.getAttribute('aria-label') || '').trim();
                            const match = raw.match(/[a-zA-Z0-9_.-]+\\.(tex|cls|bib|sty|pdf|png|jpg|jpeg)/i);
                            if (match && !names.includes(match[0])) {
                                names.push(match[0]);
                            }
                        }
                        if (names.length === 0) {
                            names.push('main.tex');
                        }
                        return names;
                    }
                """)
                return {"success": True, "files": files}
            except Exception as e:
                return {"success": False, "error": str(e)}

    async def open_file(self, filename: str) -> Dict[str, Any]:
        """Clicks a file in the project file tree to open it in the editor."""
        async with self._lock:
            page = await self._ensure_browser()
            try:
                selector = f"[role='treeitem']:has-text('{filename}'), .file-tree-item:has-text('{filename}')"
                el = await page.query_selector(selector)
                if not el:
                    items = await page.query_selector_all("[role='treeitem'], .file-tree-item")
                    for item in items:
                        text = (await item.inner_text()).strip()
                        if filename.lower() in text.lower():
                            el = item
                            break

                if el:
                    await el.click()
                    await asyncio.sleep(1.5)
                    return {"success": True, "message": f"Opened file '{filename}'"}
                else:
                    return {"success": False, "error": f"File '{filename}' not found in file tree."}
            except Exception as e:
                return {"success": False, "error": str(e)}

    async def get_latex_content(self) -> Dict[str, Any]:
        """
        Retrieves the complete LaTeX content currently displayed in the editor.
        Directly queries CodeMirror 6 EditorView (cmContent.cmView) to avoid DOM virtualization truncation.
        """
        async with self._lock:
            page = await self._ensure_browser()
            try:
                result = await page.evaluate("""
                    () => {
                        // 1. Check CodeMirror 6 on .cm-content (Overleaf modern editor view)
                        const cmContent = document.querySelector('.cm-content');
                        if (cmContent && cmContent.cmView && cmContent.cmView.view) {
                            const view = cmContent.cmView.view;
                            if (view.state && view.state.doc) {
                                return {
                                    content: view.state.doc.toString(),
                                    lines: view.state.doc.lines,
                                    engine: 'codemirror6-view'
                                };
                            }
                        }

                        // 2. Check CodeMirror 6 on .cm-editor
                        const cmEditorEl = document.querySelector('.cm-editor');
                        if (cmEditorEl && cmEditorEl.cmView && cmEditorEl.cmView.view) {
                            const view = cmEditorEl.cmView.view;
                            if (view.state && view.state.doc) {
                                return {
                                    content: view.state.doc.toString(),
                                    lines: view.state.doc.lines,
                                    engine: 'codemirror6-editor-view'
                                };
                            }
                        }

                        // 3. Check Ace Editor
                        const aceEl = document.querySelector('.ace_editor');
                        if (aceEl && window.ace) {
                            try {
                                const editor = window.ace.edit(aceEl);
                                const val = editor.getValue();
                                return {
                                    content: val,
                                    lines: val.split('\\n').length,
                                    engine: 'ace'
                                };
                            } catch (e) {}
                        }

                        // 4. CodeMirror DOM lines fallback
                        if (cmContent) {
                            const lines = Array.from(cmContent.querySelectorAll('.cm-line'));
                            if (lines.length > 0) {
                                const txt = lines.map(l => l.innerText).join('\\n');
                                return {
                                    content: txt,
                                    lines: lines.length,
                                    engine: 'codemirror6-dom-lines'
                                };
                            }
                            return {
                                content: cmContent.innerText,
                                lines: cmContent.innerText.split('\\n').length,
                                engine: 'codemirror6-innertext'
                            };
                        }

                        return {
                            content: null,
                            lines: 0,
                            engine: 'not-found'
                        };
                    }
                """)

                if result.get("content") is not None:
                    return {
                        "success": True,
                        "latex": result["content"],
                        "engine": result["engine"],
                        "line_count": result.get("lines", len(result["content"].splitlines()))
                    }
                else:
                    return {
                        "success": False,
                        "error": "Could not extract editor content. Ensure an editable LaTeX file is open."
                    }
            except Exception as e:
                return {"success": False, "error": str(e)}

    async def set_latex_content(self, latex_code: str) -> Dict[str, Any]:
        """
        Updates the editor with the new LaTeX code.
        Dispatches full document replacement directly into CodeMirror 6 (cmContent.cmView).
        """
        async with self._lock:
            page = await self._ensure_browser()
            try:
                update_result = await page.evaluate("""
                    (newContent) => {
                        // 1. CodeMirror 6 on .cm-content
                        const cmContent = document.querySelector('.cm-content');
                        if (cmContent && cmContent.cmView && cmContent.cmView.view) {
                            const view = cmContent.cmView.view;
                            const currentLen = view.state.doc.length;
                            view.dispatch({
                                changes: { from: 0, to: currentLen, insert: newContent }
                            });
                            return { success: true, method: 'cm6_content_view_dispatch' };
                        }

                        // 2. CodeMirror 6 on .cm-editor
                        const cmEditorEl = document.querySelector('.cm-editor');
                        if (cmEditorEl && cmEditorEl.cmView && cmEditorEl.cmView.view) {
                            const view = cmEditorEl.cmView.view;
                            const currentLen = view.state.doc.length;
                            view.dispatch({
                                changes: { from: 0, to: currentLen, insert: newContent }
                            });
                            return { success: true, method: 'cm6_editor_view_dispatch' };
                        }

                        // 3. Ace Editor
                        const aceEl = document.querySelector('.ace_editor');
                        if (aceEl && window.ace) {
                            try {
                                const editor = window.ace.edit(aceEl);
                                editor.setValue(newContent, -1);
                                return { success: true, method: 'ace_setValue' };
                            } catch (e) {}
                        }

                        return { success: false, method: 'js_injection_failed' };
                    }
                """, latex_code)

                if update_result.get("success"):
                    # Wait for Overleaf to debounce autosave
                    await asyncio.sleep(2)
                    return {
                        "success": True,
                        "method": update_result.get("method"),
                        "message": "LaTeX content updated successfully."
                    }

                # Attempt 2: Keyboard typing fallback
                editor_sel = ".cm-content, .cm-editor, .ace_editor"
                await page.click(editor_sel)
                is_mac = "mac" in (await page.evaluate("navigator.platform")).lower()
                cmd_key = "Meta" if is_mac else "Control"
                await page.keyboard.press(f"{cmd_key}+A")
                await asyncio.sleep(0.3)
                await page.keyboard.insert_text(latex_code)
                await asyncio.sleep(2)

                return {
                    "success": True,
                    "method": "keyboard_insert_text",
                    "message": "LaTeX content replaced via editor typing."
                }
            except Exception as e:
                return {"success": False, "error": str(e)}

    async def recompile(self, timeout_seconds: int = 40) -> Dict[str, Any]:
        """
        Triggers document recompile and waits for completion.
        Returns compile status (success or errors/warnings).
        """
        async with self._lock:
            page = await self._ensure_browser()
            try:
                # 1. Click Recompile button using Playwright locator or keyboard shortcut
                clicked = False
                try:
                    btn = page.locator("button:has-text('Recompile'), .btn-recompile, [aria-label*='Recompile' i]").first
                    if await btn.is_visible(timeout=3000):
                        await btn.click()
                        clicked = True
                except Exception:
                    pass

                if not clicked:
                    # Fallback shortcut: Ctrl+Enter or Cmd+Enter
                    is_mac = "mac" in (await page.evaluate("navigator.platform")).lower()
                    cmd_key = "Meta" if is_mac else "Control"
                    await page.keyboard.press(f"{cmd_key}+Enter")

                # Wait 1.5s for compile process to start
                await asyncio.sleep(1.5)

                start_time = time.time()
                compiling = True

                # Wait for compilation to complete (valid browser DOM check)
                while compiling and (time.time() - start_time < timeout_seconds):
                    await asyncio.sleep(1)
                    compiling = await page.evaluate("""
                        () => {
                            const buttons = Array.from(document.querySelectorAll('button, .btn'));
                            const btn = buttons.find(b => {
                                const t = (b.innerText || b.getAttribute('aria-label') || '').toLowerCase();
                                return t.includes('recompile') || b.classList.contains('btn-recompile');
                            });
                            if (btn && (btn.disabled || btn.classList.contains('compiling') || btn.innerText.toLowerCase().includes('compiling'))) {
                                return true;
                            }
                            const spinner = document.querySelector('.fa-spinner, .loading-spinner, [aria-label*=\"compiling\" i]');
                            return !!spinner;
                        }
                    """)

                # Collect compilation result (check for error modals, logs, or badge)
                compile_info = await page.evaluate("""
                    () => {
                        const errorBadge = document.querySelector('.btn-recompile-error, .badge-danger, [aria-label*=\"error\" i], [aria-label*=\"errors\" i]');
                        const errorCount = errorBadge ? errorBadge.innerText.trim() : null;

                        const logErrors = Array.from(document.querySelectorAll('.log-entry-message, .error-message, .alert-danger'))
                            .map(el => el.innerText.trim())
                            .filter(Boolean);

                        const hasPdfViewer = !!document.querySelector('.pdf-viewer, #pdf-viewer, iframe[src*=\"pdf\"], canvas.pdf-page');

                        return {
                            has_pdf: hasPdfViewer,
                            error_badge: errorCount,
                            log_errors: logErrors.slice(0, 5)
                        };
                    }
                """)

                has_errors = bool(
                    compile_info.get("log_errors") or 
                    (compile_info.get("error_badge") and "error" in str(compile_info.get("error_badge")).lower())
                )

                return {
                    "success": not has_errors,
                    "compiled": True,
                    "error_badge": compile_info.get("error_badge"),
                    "errors": compile_info.get("log_errors"),
                    "pdf_viewer_active": compile_info.get("has_pdf"),
                    "message": "Compilation finished successfully." if not has_errors else "Compilation completed with errors."
                }
            except Exception as e:
                return {"success": False, "error": str(e)}

    async def download_pdf(self, custom_filename: Optional[str] = None) -> Dict[str, Any]:
        """
        Downloads the compiled PDF from Overleaf and saves it locally.
        Uses the dynamic build URL from the Overleaf viewer.
        """
        async with self._lock:
            page = await self._ensure_browser()
            filename = custom_filename or f"resume_{int(time.time())}.pdf"
            if not filename.endswith(".pdf"):
                filename += ".pdf"
            dest_path = OVERLEAF_OUTPUT_DIR / filename

            try:
                # 1. Extract dynamic output.pdf href from the Overleaf UI
                pdf_href = await page.evaluate("""
                    () => {
                        const a = document.querySelector('a[href*="output.pdf"], a[aria-label*="Download PDF" i], a[download]');
                        return a ? a.getAttribute('href') : null;
                    }
                """)

                if pdf_href:
                    full_url = f"https://www.overleaf.com{pdf_href}" if pdf_href.startswith('/') else pdf_href
                    response = await page.context.request.get(full_url)
                    if response.status == 200:
                        body = await response.body()
                        if len(body) > 1000 and body.startswith(b"%PDF"):
                            dest_path.write_bytes(body)
                            return {
                                "success": True,
                                "file_path": str(dest_path),
                                "file_name": filename,
                                "size_bytes": len(body),
                                "message": f"PDF successfully downloaded to {dest_path}"
                            }

                # 2. UI button download fallback
                download_sel = "a[aria-label*='Download PDF' i], a[href*='output.pdf']"
                btn = page.locator(download_sel).first
                if await btn.is_visible(timeout=3000):
                    async with page.expect_download(timeout=10000) as download_info:
                        await btn.click()
                    download = await download_info.value
                    await download.save_as(str(dest_path))
                    return {
                        "success": True,
                        "file_path": str(dest_path),
                        "file_name": filename,
                        "size_bytes": dest_path.stat().st_size,
                        "message": f"PDF successfully downloaded to {dest_path}"
                    }

                return {
                    "success": False,
                    "error": "Could not download PDF. The project may need to be recompiled first."
                }
            except Exception as e:
                return {"success": False, "error": str(e)}

    async def take_screenshot(self, filename: Optional[str] = None) -> Dict[str, Any]:
        """Captures a screenshot of the current Overleaf page."""
        async with self._lock:
            page = await self._ensure_browser()
            try:
                name = filename or f"overleaf_screen_{int(time.time())}.png"
                if not name.endswith(".png"):
                    name += ".png"
                path = OVERLEAF_OUTPUT_DIR / name
                await page.screenshot(path=str(path), full_page=False)
                return {
                    "success": True,
                    "screenshot_path": str(path)
                }
            except Exception as e:
                return {"success": False, "error": str(e)}

    async def close(self):
        """Closes browser session cleanly."""
        async with self._lock:
            if self._context:
                await self._context.close()
                self._context = None
                self._page = None
            if self._playwright:
                await self._playwright.stop()
                self._playwright = None
