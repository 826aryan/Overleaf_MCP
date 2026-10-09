import json
from typing import Optional, Dict, Any
from starlette.responses import HTMLResponse, FileResponse
from mcp.server.mcpserver import MCPServer
from overleaf_browser import OverleafBrowserManager
from config import HEADLESS, OVERLEAF_OUTPUT_DIR

# Initialize MCP server
mcp = MCPServer(
    name="overleaf-latex-mcp",
    version="1.0.0",
    description="MCP server connecting Claude to Overleaf to automate resume tailoring, LaTeX editing, compilation, and PDF retrieval."
)

@mcp.custom_route("/download/{filename}", methods=["GET"])
async def download_file(request):
    """Serve downloaded PDF files so users can click and download them from Claude."""
    filename = request.path_params.get("filename")
    file_path = OVERLEAF_OUTPUT_DIR / filename
    if file_path.exists() and file_path.is_file():
        return FileResponse(
            path=str(file_path),
            filename=filename,
            media_type="application/pdf"
        )
    return HTMLResponse("<h3>File not found</h3>", status_code=404)

@mcp.custom_route("/", methods=["GET"])
async def root_dashboard(request):
    """Interactive dashboard for manually testing the Overleaf MCP server in the browser."""
    html_content = """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Overleaf MCP Server - Test Console</title>
        <style>
            * { box-sizing: border-box; }
            body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; background: #0f172a; color: #f8fafc; margin: 0; padding: 30px 20px; display: flex; justify-content: center; }
            .container { max-width: 800px; width: 100%; background: #1e293b; border-radius: 12px; padding: 28px; box-shadow: 0 10px 30px rgba(0,0,0,0.5); border: 1px solid #334155; }
            h1 { margin-top: 0; color: #38bdf8; font-size: 24px; display: flex; align-items: center; justify-content: space-between; }
            .badge { background: #10b981; color: #022c22; font-size: 13px; font-weight: 700; padding: 4px 12px; border-radius: 9999px; }
            .endpoint-card { background: #0f172a; border-left: 4px solid #38bdf8; padding: 14px 16px; margin: 18px 0; border-radius: 6px; font-family: monospace; font-size: 14px; word-break: break-all; }
            .section { background: #0f172a; border-radius: 8px; padding: 18px; margin-top: 20px; border: 1px solid #334155; }
            h2 { font-size: 16px; color: #94a3b8; margin-top: 0; text-transform: uppercase; letter-spacing: 0.05em; }
            button { background: #2563eb; color: white; border: none; padding: 10px 18px; border-radius: 6px; font-weight: 600; cursor: pointer; transition: all 0.2s; }
            button:hover { background: #1d4ed8; }
            button:disabled { opacity: 0.5; cursor: not-allowed; }
            input { width: 100%; padding: 10px 14px; background: #1e293b; border: 1px solid #475569; border-radius: 6px; color: white; font-size: 14px; margin-bottom: 12px; }
            pre { background: #020617; padding: 14px; border-radius: 6px; overflow-x: auto; color: #38bdf8; font-size: 13px; max-height: 250px; }
            .status-indicator { display: inline-block; width: 10px; height: 10px; border-radius: 50%; background: #10b981; margin-right: 8px; }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>
                <span>📄 Overleaf MCP Server</span>
                <span class="badge"><span class="status-indicator"></span>ONLINE</span>
            </h1>
            
            <p style="color: #94a3b8; margin-bottom: 8px;">Claude MCP Streamable HTTP Endpoint (Use this in Claude Web):</p>
            <div class="endpoint-card">
                <span id="sse-url">Loading...</span>
            </div>

            <!-- Manual Test 1: Check Auth -->
            <div class="section">
                <h2>🧪 Test 1: Overleaf Login Status</h2>
                <p style="color: #cbd5e1; font-size: 14px;">Verify that the persistent browser profile is authenticated into Overleaf.</p>
                <button id="btn-auth" onclick="testAuth()">Check Overleaf Login Status</button>
                <pre id="auth-output" style="display:none;"></pre>
            </div>

            <!-- Manual Test 2: Project Read -->
            <div class="section">
                <h2>🧪 Test 2: Live Project Read Test</h2>
                <p style="color: #cbd5e1; font-size: 14px;">Enter an Overleaf project URL to test opening it and reading the LaTeX source code.</p>
                <input type="text" id="project-url" placeholder="https://www.overleaf.com/project/6705f4..." />
                <button id="btn-project" onclick="testProject()">Open & Read LaTeX</button>
                <pre id="project-output" style="display:none;"></pre>
            </div>
        </div>

        <script>
            const mcpUrl = window.location.origin + '/mcp';
            document.getElementById('sse-url').innerText = mcpUrl;

            async function testAuth() {
                const btn = document.getElementById('btn-auth');
                const out = document.getElementById('auth-output');
                btn.disabled = true;
                btn.innerText = 'Checking...';
                out.style.display = 'block';
                out.innerText = 'Checking Overleaf session in browser...';
                try {
                    const res = await fetch('/api/test-auth');
                    const data = await res.json();
                    out.innerText = JSON.stringify(data, null, 2);
                } catch(e) {
                    out.innerText = 'Error: ' + e.message;
                }
                btn.disabled = false;
                btn.innerText = 'Check Overleaf Login Status';
            }

            async function testProject() {
                const input = document.getElementById('project-url').value.trim();
                const btn = document.getElementById('btn-project');
                const out = document.getElementById('project-output');
                if (!input) {
                    alert('Please enter an Overleaf project URL first.');
                    return;
                }
                btn.disabled = true;
                btn.innerText = 'Opening project...';
                out.style.display = 'block';
                out.innerText = 'Launching browser, navigating to Overleaf project and extracting LaTeX...';
                try {
                    const res = await fetch('/api/test-project', {
                        method: 'POST',
                        headers: {'Content-Type': 'application/json'},
                        body: JSON.stringify({ project_url: input })
                    });
                    const data = await res.json();
                    out.innerText = JSON.stringify(data, null, 2);
                } catch(e) {
                    out.innerText = 'Error: ' + e.message;
                }
                btn.disabled = false;
                btn.innerText = 'Open & Read LaTeX';
            }
        </script>
    </body>
    </html>
    """
    return HTMLResponse(html_content)

@mcp.custom_route("/api/test-auth", methods=["GET"])
async def api_test_auth(request):
    """Direct API to test auth status from browser dashboard."""
    from starlette.responses import JSONResponse
    res = await browser.check_auth_status()
    return JSONResponse(res)

@mcp.custom_route("/api/test-project", methods=["POST"])
async def api_test_project(request):
    """Direct API to open project and read LaTeX from browser dashboard."""
    from starlette.responses import JSONResponse
    data = await request.json()
    project_url = data.get("project_url", "")
    open_res = await browser.open_project(project_url)
    if not open_res.get("success"):
        return JSONResponse(open_res)
    latex_res = await browser.get_latex_content()
    # Return summary + preview of LaTeX
    full_latex = latex_res.get("latex") or ""
    return JSONResponse({
        "open_result": open_res,
        "latex_success": latex_res.get("success"),
        "line_count": len(full_latex.splitlines()),
        "latex_preview": full_latex[:600] + ("\n... [truncated for display]" if len(full_latex) > 600 else "")
    })

# Global browser manager instance
browser = OverleafBrowserManager(headless=HEADLESS)

@mcp.tool()
async def overleaf_status() -> str:
    """
    Check the connection status and whether the user is authenticated in Overleaf.
    Call this first to verify that your session is ready.
    """
    res = await browser.check_auth_status()
    return json.dumps(res, indent=2)

@mcp.tool()
async def overleaf_open_project(project_url_or_id: str) -> str:
    """
    Open an Overleaf project by its URL or 24-character Project ID.
    Example: 'https://www.overleaf.com/project/6705f4...' or '6705f4...'
    Returns project title, current open file name, and status.
    """
    res = await browser.open_project(project_url_or_id)
    return json.dumps(res, indent=2)

@mcp.tool()
async def overleaf_list_files() -> str:
    """
    List all the files and folders in the currently open Overleaf project file tree.
    Useful for locating 'main.tex', 'resume.cls', or modular section files.
    """
    res = await browser.list_files()
    return json.dumps(res, indent=2)

@mcp.tool()
async def overleaf_open_file(filename: str) -> str:
    """
    Switch the editor to a specific file in the project (e.g., 'main.tex', 'experience.tex').
    """
    res = await browser.open_file(filename)
    return json.dumps(res, indent=2)

@mcp.tool()
async def overleaf_get_latex() -> str:
    """
    Read and return the complete LaTeX source code currently open in the Overleaf editor.
    Claude should call this to fetch the resume LaTeX code before analyzing and tailoring it.
    """
    res = await browser.get_latex_content()
    return json.dumps(res, indent=2)

@mcp.tool()
async def overleaf_set_latex(latex_code: str) -> str:
    """
    Replace the editor content with the updated LaTeX code.
    Pass the complete modified LaTeX code with tailored keywords, bullets, and skills.
    Overleaf will automatically synchronize and autosave the changes.
    """
    res = await browser.set_latex_content(latex_code)
    return json.dumps(res, indent=2)

@mcp.tool()
async def overleaf_recompile(timeout_seconds: int = 35) -> str:
    """
    Trigger the 'Recompile' action in Overleaf and check for compilation errors or warnings.
    Always call this after updating LaTeX code to ensure there are no syntax or formatting errors.
    If errors exist, Claude can inspect the returned errors and fix them in overleaf_set_latex.
    """
    res = await browser.recompile(timeout_seconds=timeout_seconds)
    return json.dumps(res, indent=2)

@mcp.tool()
async def overleaf_download_pdf(filename: Optional[str] = None) -> str:
    """
    Download the freshly compiled PDF resume from Overleaf to the server.
    Returns the file name, download URL endpoint (/download/<filename>), and Overleaf build URL.
    Claude should provide a clickable Markdown link in the chat so the user can download it with one click:
    Example: [Download Tailored Resume PDF](/download/<filename>)
    """
    res = await browser.download_pdf(custom_filename=filename)
    if res.get("success") and "file_name" in res:
        res["server_download_path"] = f"/download/{res['file_name']}"
        res["action_for_claude"] = f"Provide a clickable markdown link in your response: [Download Tailored Resume PDF](/download/{res['file_name']})"
    return json.dumps(res, indent=2)

@mcp.tool()
async def overleaf_take_screenshot(filename: Optional[str] = None) -> str:
    """
    Take a screenshot of the Overleaf page (editor or preview) and save it locally.
    Useful for inspecting visual layout or debugging issues.
    """
    res = await browser.take_screenshot(filename=filename)
    return json.dumps(res, indent=2)

@mcp.tool()
def tailor_resume_instructions() -> str:
    """
    Returns guidance and best practices for tailoring a LaTeX resume to a Job Description (JD).
    """
    instructions = {
        "latex_safety": [
            "Always escape special LaTeX characters: &, %, $, #, _, {, }, ~, ^",
            "Keep LaTeX environment tags matched: \\begin{itemize} ... \\end{itemize}",
            "Preserve page constraints (usually strict 1 page or 2 pages) by avoiding excessive line additions",
            "Maintain typography commands (e.g. \\textbf, \\textit, \\small, \\hfill) according to the template"
        ],
        "tailoring_strategy": [
            "Extract top 5-10 technical and domain keywords from the JD (technologies, methodologies, leadership words)",
            "Weave keywords naturally into existing experience bullets rather than keyword-stuffing",
            "Use the Google XYZ bullet formula: 'Accomplished [X] as measured by [Y], by doing [Z]'",
            "Update the Skills section to prioritize tech stack items that match the JD requirements",
            "Customize the Summary/Header subtitle (if present) to align with the target job title"
        ],
        "workflow": [
            "1. Call overleaf_open_project with user's project URL",
            "2. Call overleaf_get_latex to retrieve source resume",
            "3. Analyze JD against the resume and draft tailored changes",
            "4. Call overleaf_set_latex with the complete updated LaTeX code",
            "5. Call overleaf_recompile to verify zero compile errors",
            "6. Call overleaf_download_pdf to deliver the final PDF path to the user",
            "7. Return a summary of tailored keywords, updated bullets, and ATS optimization score"
        ]
    }
    return json.dumps(instructions, indent=2)
