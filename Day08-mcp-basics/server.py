import platform
import os
import socket

from fastmcp import FastMCP

# Create the MCP server and give it a name
mcp = FastMCP("Devops Helper Server")

# The docstring of each tool is the description the AI planner reads.
# Write it clearly: it is how the AI knows what the tool does.

@mcp.tool()
def memory_usage() -> str:
    """Return total, used, and available physical memory (RAM) in GiB."""

    memory = {}
    with open("/proc/meminfo", "r", encoding="utf-8") as meminfo_file:
        for line in meminfo_file:
            key, value, *_ = line.split()
            if key in {"MemTotal:", "MemAvailable:"}:
                memory[key.removesuffix(":")] = int(value) * 1024

    total = memory["MemTotal"]
    available = memory["MemAvailable"]
    used = total - available
    gib = 1024 ** 3

    return (
        f"RAM: total {total // gib} GiB, used {used // gib} GiB, "
        f"available {available // gib} GiB"
    )


@mcp.tool()
def system_uptime() -> str:
    """Return how long the machine has been running."""

    with open("/proc/uptime", "r", encoding="utf-8") as uptime_file:
        total_seconds = float(uptime_file.readline().split()[0])

    hours = int(total_seconds // 3600)
    minutes = int((total_seconds % 3600) // 60)

    return f"System uptime: {hours} hours {minutes} minutes"


@mcp.tool()
def host_info() -> str:
    """Return the hostname and operating system details."""

    hostname = platform.node()
    os_info = platform.platform()

    return f"Host: {hostname} | OS: {os_info}"

if __name__ == "__main__":
    # No print() here: the client and server talk through standard output.
    mcp.run()
