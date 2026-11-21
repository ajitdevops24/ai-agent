from fastmcp import FastMCP
import os
import shutil

# Create the MCP server and give it a name
mcp = FastMCP("DevOps Helper Server")

# The logs folder next to this file. The log tools can never read outside it.
LOG_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), "logs")

GIB = 1024 ** 3

# The docstring of each tool is the description the AI planner reads.
# All tools are READ-ONLY: they look at the system, they never change it.


@mcp.tool()
def disk_usage() -> str:
    """Return total, used and free disk space of the root filesystem in GiB."""

    total, used, free = shutil.disk_usage("/")
    percent = used / total * 100

    return (
        f"Disk /: total {total / GIB:.1f} GiB, used {used / GIB:.1f} GiB "
        f"({percent:.0f}% used), free {free / GIB:.1f} GiB"
    )


@mcp.tool()
def list_log_files() -> str:
    """List the names of the available log files."""

    if not os.path.isdir(LOG_FOLDER):
        return "No logs folder found."

    files = sorted(f for f in os.listdir(LOG_FOLDER) if f.endswith(".log"))

    return "Log files: " + ", ".join(files)


@mcp.tool()
def read_log(filename: str, lines: int = 15) -> str:
    """Read the last lines of one log file. Use list_log_files first to get the file name."""

    # Keep only the file name, so this tool can never read files outside logs/
    filename = os.path.basename(filename)
    path = os.path.join(LOG_FOLDER, filename)

    if not os.path.exists(path):
        return f"Log file '{filename}' not found. Use list_log_files to see the available files."

    count = max(1, min(lines, 50))

    with open(path, "r", encoding="utf-8") as file:
        content = file.readlines()

    return "".join(content[-count:]).strip()


if __name__ == "__main__":
    # No print() here: the client and server talk through standard output.
    mcp.run()
