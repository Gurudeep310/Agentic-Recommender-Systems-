# server.py
from mcp.server.fastmcp import FastMCP
import os

# Create an MCP server
mcp = FastMCP("AI Sticky Notes")

# Having notes in my current directory
NOTES_FILE = os.path.join(os.path.dirname(__file__), "notes.txt")

def ensure_file():
    if not os.path.exists(NOTES_FILE):
        with open(NOTES_FILE, "w") as f:
            f.write("")
# Add an addition tool
@mcp.tool()
def add_note(message: str) -> str:
    """
    Add a note to the notes file.
    Args:
        message: The message to add to the notes file.
    Returns:
        A success message.
    """
    ensure_file()
    with open(NOTES_FILE, "a") as f:
        f.write(message + "\n")
    return "Note added successfully"

@mcp.tool()
def read_notes() -> str:
    """
    Read the notes from the notes file.
    Returns:
        The notes from the notes file.
    """
    ensure_file()   
    with open(NOTES_FILE, "r") as f:
        content = f.read().strip()
    return content or "No notes found"

@mcp.tool()
def get_latest_note() -> str:
    """
    Get the latest note from the notes file.
    Returns:
        The latest note from the notes file.
    """
    ensure_file()
    with open(NOTES_FILE, "r") as f:
        lines = f.readlines()
    return lines[-1].strip() if lines else "No notes yet"

@mcp.tool()
def summarize_notes() -> str:
    """
    Summarize the notes from the notes file.
    Args:
        notes: The notes to summarize.
    Returns:
        A summary of the notes.
    """
    ensure_file()
    with open(NOTES_FILE, "r") as f:
        content = f.read().strip()

    if not content:
        return "No notes yet"
    
    return f"Summarize the the following notes: {content}"


# Resources and Prompts are not working in Cursor's Claude
# References
'''
https://github.com/modelcontextprotocol/python-sdk?tab=readme-ov-file
https://smithery.ai/server/@openags/paper-search-mcp
https://docs.astral.sh/uv/getting-started/installation/#shell-autocompletion
https://modelcontextprotocol.io/introduction
https://github.com/modelcontextprotocol/python-sdk
https://github.com/QuantGeekDev/coincap-mcp
'''