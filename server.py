import json
from typing import Optional, Dict, Any
from mcp.server.mcpserver import MCPServer
from overleaf_browser import OverleafBrowserManager
from config import HEADLESS

# Initialize MCP server
mcp = MCPServer(
    name="overleaf-latex-mcp",
    version="1.0.0",
    description="MCP server connecting Claude to Overleaf to automate resume tailoring, LaTeX editing, compilation, and PDF retrieval."
)

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
    Download the freshly compiled PDF resume from Overleaf to the local machine.
    Returns the absolute path to the saved PDF file.
    """
    res = await browser.download_pdf(custom_filename=filename)
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
