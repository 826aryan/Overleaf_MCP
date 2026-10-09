# 📄 Overleaf LaTeX MCP Server for Claude

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](https://opensource.org/licenses/MIT)
[![Python 3.12+](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/downloads/)
[![Model Context Protocol](https://img.shields.io/badge/MCP-Streamable%20HTTP%20%7C%20SSE-green.svg)](https://modelcontextprotocol.io/)

An open-source [Model Context Protocol (MCP)](https://modelcontextprotocol.io/) server that connects **Claude** (Claude.ai Web or Claude Desktop) directly to **Overleaf** for autonomous, high-accuracy resume tailoring.

Provide a **Job Description (JD)** to Claude, and Claude will automatically:
1. Open your LaTeX resume project in Overleaf.
2. Read the full source code (preserving document structure and escaping special characters).
3. Tailor bullets, metrics, and technical skills to match the job requirements.
4. Update the Overleaf editor and trigger a recompile.
5. Provide a direct, clickable link to download the compiled PDF!

---

## 🚀 1-Click Cloud Deployment (Railway)

[![Deploy on Railway](https://railway.app/button.svg)](https://railway.app/new)

Deploy your own private, 24/7 cloud instance on Railway with your Overleaf account in under 2 minutes:

### 1. Get Your Overleaf Credentials (Pick One):

- **Method A: Quick Cookie (Zero-Install)**  
  1. Open [Overleaf.com](https://www.overleaf.com) in Chrome/Brave and make sure you are logged in.
  2. Press `F12` (Inspect) → **Application** (or Storage) → **Cookies** → `https://www.overleaf.com`.
  3. Copy the value of the **`overleaf_session`** cookie.
  4. In Railway, set:
     - `OVERLEAF_SESSION_COOKIE` = `your_cookie_value`

- **Method B: Full Session Export**  
  If you clone the repo locally, run:
  ```bash
  ./setup_auth.py       # logs in once via Chromium
  python3 export_session.py
  ```
  Copy the printed `OVERLEAF_STORAGE_STATE_B64` string and set it in Railway.

### 2. Deploy & Connect to Claude:
1. Fork or push this repository to your GitHub.
2. In [Railway.app](https://railway.app), click **New Project** → **Deploy from GitHub repo**.
3. Under **Variables**, add:
   - `OVERLEAF_SESSION_COOKIE` *(from Method A)* **OR** `OVERLEAF_STORAGE_STATE_B64` *(from Method B)*
   - `MCP_TRANSPORT` = `streamable-http`
4. Under **Settings** → **Networking**, click **Generate Domain** (e.g. `https://latex-mcp-production.up.railway.app`).
5. In **Claude.ai** → **Settings** → **Connectors** → **Add Custom Connector**:
   - **Name**: `overleaf_mcp`
   - **URL**: `https://your-domain.up.railway.app/mcp`

---

## 💻 Local Quickstart

### 1. Installation
```bash
git clone https://github.com/<your-username>/latex_mcp.git
cd latex_mcp
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
playwright install chromium
```

### 2. One-Time Login
```bash
./setup_auth.py
```
A Chromium window will open. Log into your Overleaf account (Email, Google, or SSO). Press `Enter` in the terminal once you reach the dashboard. Your session will be saved locally in `./browser_data`.

### 3. Start Server
```bash
./run_server.sh
```
- Streamable HTTP endpoint: `http://127.0.0.1:8000/mcp`
- Web Test Console: `http://127.0.0.1:8000/`

---

## 🧰 Available MCP Tools

| Tool | Purpose |
| :--- | :--- |
| `overleaf_status` | Check if session is authenticated in Overleaf |
| `overleaf_open_project` | Open project by URL or ID |
| `overleaf_get_latex` | Read full LaTeX source code from editor |
| `overleaf_set_latex` | Update Overleaf editor with tailored LaTeX |
| `overleaf_recompile` | Trigger recompile and check for LaTeX errors |
| `overleaf_download_pdf` | Download compiled PDF and return clickable download link |
| `overleaf_list_files` | List project files (`main.tex`, `resume.cls`, etc.) |
| `overleaf_open_file` | Switch to a specific file in the sidebar |
| `overleaf_take_screenshot` | Capture screenshot of Overleaf for visual inspection |
| `tailor_resume_instructions` | Returns LaTeX syntax safeguards and ATS optimization formulas |

---

## 📝 Example Prompt for Claude

Paste this in your chat once the connector is added:

```markdown
Here is the Job Description:
"""
[Paste Job Description here]
"""

My Overleaf resume project URL is:
https://www.overleaf.com/project/<YOUR_PROJECT_ID>

Please:
1. Open my project with `overleaf_open_project` and inspect the LaTeX code with `overleaf_get_latex`.
2. Tailor my experience bullets, skills, and summary for this role (preserve formatting & escape special characters).
3. Update the LaTeX in Overleaf with `overleaf_set_latex`.
4. Recompile with `overleaf_recompile` and verify zero errors.
5. Download the PDF with `overleaf_download_pdf` and give me the download link.
6. Provide a summary of the improvements and keywords you added.
```

---

## 🤝 Contributing

Contributions, bug reports, and suggestions are welcome! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for local development guidelines.

## 📄 License

This project is licensed under the [MIT License](LICENSE).
