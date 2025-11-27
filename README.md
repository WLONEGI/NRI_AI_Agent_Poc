# Local Knowledge Memory MCP Server

A local MCP server that provides memory storage using Markdown files and keyword-based search.

## Setup

1. Create virtual environment and install dependencies:
```bash
python3 -m venv .venv
.venv/bin/pip install -e .
```

## Usage

### Interactive Testing (MCP Inspector)
```bash
mcp dev src/memory_mcp/main.py
```

### Connect from MCP Clients (Antigravity, Claude Desktop, etc.)

Add the following configuration to your MCP settings file (e.g., `~/Library/Application Support/Code/User/globalStorage/mcp-servers.json` or similar depending on your client):

```json
{
  "mcpServers": {
    "local-memory-store": {
      "command": "/Users/negishi/develop/NRI_AI_Agent_Poc/.venv/bin/python",
      "args": [
        "/Users/negishi/develop/NRI_AI_Agent_Poc/src/memory_mcp/main.py"
      ]
    }
  }
}
```
