# 📄 Overleaf LaTeX MCP Server for Claude

An end-to-end [Model Context Protocol (MCP)](https://modelcontextprotocol.io/) server that connects **Claude** (Claude.ai Web or Claude Desktop) directly to **Overleaf** for autonomous resume tailoring.

---

## ⚡ Features

- **Automated Overleaf Workflow**: Reads your actual `.tex` code from Overleaf, tailors keywords/experience to match a Job Description, writes the updated LaTeX back, compiles it, and downloads the PDF.
- **Modern MCP Protocol**: Built with native **Streamable HTTP** (`/mcp`) for Claude.ai custom connectors and SSE (`/sse`) for legacy clients.
- **Persistent Cloud Authentication**: Zero-login cloud deployment using an exported session state (`OVERLEAF_STORAGE_STATE_B64`).
- **One-Click Clickable Downloads**: Claude gives you a clickable direct download link (`/download/<filename>`) to immediately save the PDF from the server.
- **Interactive Web Console**: Built-in visual dashboard on `/` to test your connection and inspect projects in the browser.

---

## 🚂 1-Click Cloud Deployment to Railway

### Step 1: Export Your Overleaf Session String
If you've logged in once locally with `./setup_auth.py`, export your session:
```bash
python3 export_session.py
```
This prints your base64 session string: `OVERLEAF_STORAGE_STATE_B64`. Copy it!

### Step 2: Push to GitHub & Deploy on Railway
1. Push this repository to GitHub:
   ```bash
   git add .
   git commit -m "Deploy to Railway"
   git remote add origin https://github.com/<your-username>/latex_mcp.git
   git push -u origin master
   ```
2. Go to [Railway.app](https://railway.app) → **New Project** → **Deploy from GitHub repo**.
3. In Railway **Settings** → **Variables**, add:
   - `OVERLEAF_STORAGE_STATE_B64`: *(paste your base64 string from Step 1)*
   - `MCP_TRANSPORT`: `streamable-http`
4. In Railway **Settings** → **Networking**, click **Generate Domain**. You will get a domain like:
   `https://latex-mcp-production.up.railway.app`

### Step 3: Add Connector in Claude.ai
1. Go to **Claude.ai** → **Settings** → **Connectors** (or Integrations) → **Add Custom Connector**.
2. **Name**: `overleaf_mcp`
3. **URL**: `https://your-domain.up.railway.app/mcp`
4. Click **Add**! Claude will connect, load all 10 tools, and you're ready to tailor resumes anytime from any device!

---

## 💻 Local Quickstart

### 1. Initial Setup
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
playwright install chromium
```

### 2. One-Time Overleaf Login
```bash
./setup_auth.py
```
Log in to Overleaf in the visible browser window, then press `Enter` in the terminal to save your session permanently.

### 3. Run the Server
```bash
./run_server.sh
```
Server runs on `http://127.0.0.1:8000`.

---

## 🧰 Available MCP Tools

| Tool | Purpose |
| :--- | :--- |
| `overleaf_status` | Check if session is logged into Overleaf |
| `overleaf_open_project` | Open project by URL or ID |
| `overleaf_get_latex` | Read full LaTeX code of active document |
| `overleaf_set_latex` | Update Overleaf editor with modified LaTeX |
| `overleaf_recompile` | Trigger recompile and check for compilation errors |
| `overleaf_download_pdf` | Download PDF and return clickable download link |
| `overleaf_list_files` | List project files (`main.tex`, etc.) |
| `overleaf_open_file` | Switch to a specific file in the sidebar |
| `overleaf_take_screenshot`| Take screenshot of Overleaf for visual inspection |
| `tailor_resume_instructions` | Return best practices for LaTeX formatting & ATS |

---

## 📝 Example Claude Prompt

```markdown
Here is the Job Description:
"""
[Paste Job Description here]
"""

My Overleaf resume project URL is:
https://www.overleaf.com/project/<YOUR_PROJECT_ID>

Please:
1. Open my project and read the full LaTeX code.
2. Tailor my experience bullets, skills, and summary for this role.
3. Update the LaTeX code in Overleaf and recompile.
4. Verify there are no compilation errors and download the final PDF.
5. Provide a summary of the improvements and keywords you added.
```
