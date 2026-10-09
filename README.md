# 📄 Overleaf LaTeX MCP Server for Claude

An end-to-end [Model Context Protocol (MCP)](https://modelcontextprotocol.io/) server that connects **Claude** (Claude Web or Claude Desktop) directly to **Overleaf**.

With this MCP server, you can give Claude a **Job Description (JD)**, and Claude will automatically:
1. Open your resume project in Overleaf via authenticated browser automation.
2. Read your current LaTeX resume code.
3. Tailor experience bullets, skills, and keywords for the JD (while preserving formatting and escaping special LaTeX characters).
4. Update the Overleaf editor.
5. Recompile the project and check for syntax errors.
6. Download the compiled PDF to your local computer.

---

## 🛠️ Architecture

```
┌─────────────────┐       SSE / HTTP or stdio       ┌────────────────────────┐
│ Claude Web /    │ ──────────────────────────────> │ Overleaf MCP Server    │
│ Claude Desktop  │ <────────────────────────────── │ (FastMCP / Playwright) │
└─────────────────┘                                 └───────────┬────────────┘
                                                                │ Persistent Context
                                                                ▼
                                                    ┌────────────────────────┐
                                                    │  Overleaf Web Editor   │
                                                    │  (CodeMirror / Ace)    │
                                                    └────────────────────────┘
```

- **Persistent Session**: Your login cookies and credentials are saved locally in `./browser_data`. You only log in to Overleaf once.
- **Bi-directional Editing**: Directly interacts with Overleaf's modern editor (CodeMirror 6 / Ace) with automatic change dispatch and typing fallback.
- **Instant Feedback**: Claude triggers "Recompile", checks error logs, and fixes any broken syntax automatically.

---

## 🚀 Quick Start Guide

### 1. Installation

The environment is already configured in `.venv/`. If setting up on a new machine:

```bash
git clone <repo-url> latex_mcp
cd latex_mcp
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
playwright install chromium
```

---

### 2. One-Time Overleaf Login

Because Overleaf requires authentication (and may present CAPTCHAs or Google OAuth), run the one-time authentication script:

```bash
./setup_auth.py
# or: python3 setup_auth.py
```

1. A Chromium browser window will open to `https://www.overleaf.com/login`.
2. Log in using your email, Google account, or SSO.
3. Once you reach your Overleaf projects dashboard, return to the terminal and press **Enter**.
4. Your session is now saved in `./browser_data/`. All future MCP automation runs headlessly using this authenticated session!

---

### 3. Start the MCP Server

#### For Claude Web (SSE Transport - Default):
```bash
./run_server.sh
# Server starts on http://127.0.0.1:8000/sse
```

#### For Claude Desktop (stdio Transport):
```bash
./run_server.sh --transport stdio
```

---

## 🌐 Connecting to Claude

### Option A: Connecting to Claude Web (`claude.ai`)

Claude Web connects to remote MCP servers over HTTPS. You can expose your local SSE endpoint using **Cloudflare Tunnel** (free, no account needed) or **ngrok**:

#### Using Cloudflare Tunnel:
```bash
brew install cloudflare/cloudflare/cloudflared
cloudflared tunnel --url http://127.0.0.1:8000
```
This gives you a public HTTPS URL like:
`https://random-subdomain.trycloudflare.com`

Your SSE endpoint for Claude will be:
`https://random-subdomain.trycloudflare.com/sse`

#### Using ngrok:
```bash
ngrok http 8000
```
Then use: `https://your-ngrok-id.ngrok-free.app/sse`

In **Claude.ai** (Team/Enterprise or via custom MCP connectors / MCP Chrome extension):
- Add MCP Server URL: `https://your-subdomain.trycloudflare.com/sse`

---

### Option B: Connecting to Claude Desktop

If you use Claude Desktop, add this to your `claude_desktop_config.json`:

**macOS Path**: `~/Library/Application Support/Claude/claude_desktop_config.json`

```json
{
  "mcpServers": {
    "overleaf": {
      "command": "/Users/aryanraj/latex_mcp/.venv/bin/python3",
      "args": [
        "/Users/aryanraj/latex_mcp/main.py",
        "--transport",
        "stdio"
      ]
    }
  }
}
```

Restart Claude Desktop, and the hammer icon (tools) will show all Overleaf tools.

---

## 🧰 Available MCP Tools

| Tool | Description |
| :--- | :--- |
| `overleaf_status` | Verifies whether the persistent session is logged in and ready. |
| `overleaf_open_project` | Opens an Overleaf project by URL (e.g., `https://www.overleaf.com/project/<id>`) or ID. |
| `overleaf_list_files` | Lists files in the left sidebar tree (e.g. `main.tex`, `resume.cls`). |
| `overleaf_open_file` | Clicks a specific file in the sidebar to open it in the editor. |
| `overleaf_get_latex` | Reads and returns the complete LaTeX source code from the active editor. |
| `overleaf_set_latex` | Replaces the editor content with updated/tailored LaTeX code. |
| `overleaf_recompile` | Clicks "Recompile", waits for compilation, and parses any LaTeX errors. |
| `overleaf_download_pdf` | Downloads the compiled PDF to `./output/<filename>.pdf`. |
| `overleaf_take_screenshot` | Takes a screenshot of the Overleaf window for visual verification. |
| `tailor_resume_instructions` | Provides best-practice guidelines for LaTeX syntax and ATS resume tailoring. |

---

## 💡 Example Prompt for Claude

Once connected to Claude, you can simply paste a prompt like this:

> **Claude Prompt:**
> "I want to apply for this job. Here is the Job Description:
> 
> ```
> [Paste Job Description here]
> ```
> 
> My Overleaf resume project URL is:
> `https://www.overleaf.com/project/YOUR_PROJECT_ID`
> 
> Please:
> 1. Open my project and read my current LaTeX resume.
> 2. Analyze the key skills, keywords, and qualifications required in the JD.
> 3. Update my experience bullet points and skills section to highlight those qualifications (ensuring valid LaTeX syntax and escaping special characters).
> 4. Update the LaTeX in Overleaf and recompile.
> 5. Make sure there are no compile errors, and download the finished PDF for me.
> 6. Summarize the changes you made and the keywords added."

---

## 🛡️ Safety & LaTeX Formatting Safeguards

The MCP server and prompts enforce:
- **Escape Character Protection**: Automatically guards against unescaped LaTeX characters (`%`, `&`, `_`, `$`, `#`).
- **Layout Preservation**: Maintains the existing template margins, fonts, and itemize structures without causing multi-page overflow.
- **ATS Bullet Structure**: Aligns bullet points with action verbs and quantifiable results (Google XYZ formula).
- **Auto-Correction**: If Overleaf returns a compile error after updating, Claude receives the exact line error and can correct it immediately.
