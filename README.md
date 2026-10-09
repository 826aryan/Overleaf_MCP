# Overleaf MCP Server for Claude

Connect Claude to your Overleaf account. Give Claude a job description and it will open your resume, tailor the LaTeX, recompile, and return a download link.

---

## How It Works

1. Claude receives a job description from you
2. It opens your Overleaf project via browser automation
3. It reads your LaTeX source, makes targeted edits, and recompiles
4. You get a summary of changes + a PDF download link

---

## Setup (Cloud — Recommended)

### Step 1 — Fork & Deploy

1. Fork this repo to your GitHub
2. Go to [railway.app](https://railway.app) → **New Project** → **Deploy from GitHub repo** → select your fork
3. Under **Settings → Networking**, click **Generate Domain** — copy the URL

### Step 2 — Get Your Overleaf Session

Run locally to export your Overleaf session:

```bash
git clone https://github.com/<your-username>/Overleaf_MCP.git
cd Overleaf_MCP
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
playwright install chromium

python3 setup_auth.py       # opens a browser — log in to Overleaf, then press Enter
python3 export_session.py   # prints your session as a base64 string
```

Copy the printed `OVERLEAF_STORAGE_STATE_B64` string.

### Step 3 — Set Environment Variable

In Railway → your service → **Variables** tab, add:

| Variable | Value |
| --- | --- |
| `OVERLEAF_STORAGE_STATE_B64` | *(paste the base64 string)* |
| `MCP_TRANSPORT` | `streamable-http` |

Railway will redeploy automatically.

### Step 4 — Connect to Claude

**Claude.ai (Web):**
Settings → Integrations → Add Integration → paste your Railway URL:
```
https://your-app.up.railway.app/mcp
```

**Claude Desktop:**
Add to `~/Library/Application Support/Claude/claude_desktop_config.json`:
```json
{
  "mcpServers": {
    "overleaf": {
      "url": "https://your-app.up.railway.app/mcp"
    }
  }
}
```
Restart Claude Desktop.

---

## Setup (Local)

```bash
git clone https://github.com/<your-username>/Overleaf_MCP.git
cd Overleaf_MCP
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
playwright install chromium

python3 setup_auth.py   # log in to Overleaf once
./run_server.sh         # starts server at http://127.0.0.1:8000/mcp
```

In Claude Desktop config, set the URL to `http://127.0.0.1:8000/mcp`.

---

## Example Prompt

```
Here is the job description:
"""
[Paste JD here]
"""

My Overleaf resume URL: https://www.overleaf.com/project/<YOUR_PROJECT_ID>

Please open my project, tailor the LaTeX to match this JD, recompile, and give me the PDF download link.
```

---

## Available Tools

| Tool | Description |
| --- | --- |
| `overleaf_status` | Check authentication status |
| `overleaf_open_project` | Open a project by URL or ID |
| `overleaf_get_latex` | Read LaTeX source from the editor |
| `overleaf_set_latex` | Write updated LaTeX to the editor |
| `overleaf_recompile` | Recompile and check for errors |
| `overleaf_download_pdf` | Download the compiled PDF |
| `overleaf_list_files` | List files in the project |
| `overleaf_open_file` | Switch to a specific file |

---

## Notes

- Your session cookie expires periodically. Re-run `setup_auth.py` + `export_session.py` and update the Railway env variable when it does.
- This uses browser automation (Playwright) — no Overleaf API key needed.

## License

[MIT](LICENSE)
