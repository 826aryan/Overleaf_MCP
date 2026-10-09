# Contributing to Overleaf LaTeX MCP Server

Thank you for your interest in contributing! This project connects Claude to Overleaf to automate resume tailoring, LaTeX editing, compiling, and PDF generation.

---

## 🛠️ Local Development Setup

1. **Fork and clone the repository:**
   ```bash
   git clone https://github.com/<your-username>/latex_mcp.git
   cd latex_mcp
   ```

2. **Create a virtual environment:**
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   playwright install chromium
   ```

3. **Authenticate once with Overleaf:**
   ```bash
   ./setup_auth.py
   ```

4. **Run the MCP server locally:**
   ```bash
   ./run_server.sh
   ```

5. **Run End-to-End Tests:**
   ```bash
   python3 test_e2e.py
   ```

---

## 🚀 Submitting Pull Requests

1. Create a feature branch: `git checkout -b feature/my-new-tool`
2. Commit your changes: `git commit -am 'Add new Overleaf tool'`
3. Push to your branch: `git push origin feature/my-new-tool`
4. Open a Pull Request on GitHub.

All contributions, bug fixes, and feature requests are welcome!
