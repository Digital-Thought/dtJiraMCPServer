# Installation Guide

## Prerequisites

- Python 3.10 or later
- An Atlassian Cloud instance (Jira Cloud and/or Jira Service Management)
- An Atlassian API token ([create one here](https://id.atlassian.com/manage-profile/security/api-tokens))

## Docker Installation (Recommended)

### Build the Image

```bash
git clone <repo-url>
cd dtJiraMCPServer
docker build -t dtjiramcpserver:latest .
```

### Run

```bash
docker run -i --rm \
  --read-only \
  -v dtjiramcp_data:/_working \
  --security-opt=no-new-privileges \
  --cap-drop=ALL \
  -e JIRA_INSTANCE_URL=https://your-domain.atlassian.net \
  -e JIRA_USER_EMAIL=user@example.com \
  -e JIRA_API_TOKEN=your-api-token \
  dtjiramcpserver:latest
```

The server communicates via stdin/stdout using the MCP stdio transport. It is designed to be launched by an MCP client (such as Claude Desktop or Claude Code).

### Security Flags

| Flag | Purpose |
|------|---------|
| `--read-only` | Prevents writes to the container filesystem |
| `-v dtjiramcp_data:/_working` | Persistent volume for framework keystore and logs |
| `--security-opt=no-new-privileges` | Prevents privilege escalation |
| `--cap-drop=ALL` | Drops all Linux capabilities |

## Local Installation

### Setup

```bash
git clone <repo-url>
cd dtJiraMCPServer
python -m venv .venv

# Activate virtual environment
.venv\Scripts\activate        # Windows
# source .venv/bin/activate   # Linux/macOS

# Install with development dependencies
pip install -e ".[dev]"
```

### Configuration

Set the required environment variables:

```bash
# Required
export JIRA_INSTANCE_URL=https://your-domain.atlassian.net
export JIRA_USER_EMAIL=user@example.com
export JIRA_API_TOKEN=your-api-token

# Optional
export LOG_LEVEL=INFO  # DEBUG, INFO, WARNING, ERROR
```

On Windows, use `set` instead of `export`:

```cmd
set JIRA_INSTANCE_URL=https://your-domain.atlassian.net
set JIRA_USER_EMAIL=user@example.com
set JIRA_API_TOKEN=your-api-token
```

### Run

```bash
python -m dtjiramcpserver
```

## MCP Client Configuration

### Claude Desktop

Add to your Claude Desktop configuration file:

**macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`
**Windows**: `%APPDATA%\Claude\claude_desktop_config.json`

```json
{
  "mcpServers": {
    "jira": {
      "command": "docker",
      "args": [
        "run", "-i", "--rm",
        "--read-only",
        "-v", "dtjiramcp_data:/_working",
        "--security-opt=no-new-privileges",
        "--cap-drop=ALL",
        "-e", "JIRA_INSTANCE_URL=https://your-domain.atlassian.net",
        "-e", "JIRA_USER_EMAIL=user@example.com",
        "-e", "JIRA_API_TOKEN=your-api-token",
        "dtjiramcpserver:latest"
      ]
    }
  }
}
```

### Claude Code

Add to your project's `.mcp.json` or global MCP settings:

```json
{
  "mcpServers": {
    "jira": {
      "command": "python",
      "args": ["-m", "dtjiramcpserver"],
      "env": {
        "JIRA_INSTANCE_URL": "https://your-domain.atlassian.net",
        "JIRA_USER_EMAIL": "user@example.com",
        "JIRA_API_TOKEN": "your-api-token"
      }
    }
  }
}
```

## Verifying the Installation

Once the server is running via an MCP client, ask the LLM:

> "List all available Jira tools"

The LLM should invoke `list_available_tools` and return a categorised listing of all 47 tools.

## Atlassian API Token

1. Go to [Atlassian API Tokens](https://id.atlassian.com/manage-profile/security/api-tokens)
2. Click **Create API token**
3. Give it a label (e.g. "MCP Server")
4. Copy the token - it will not be shown again

The token authenticates as your Atlassian account. The server's permissions are limited to what your account can access.

## Troubleshooting

### "Configuration error: JIRA_INSTANCE_URL is required"

Ensure all three required environment variables are set. The URL must include the protocol (`https://`).

### "Authentication failed"

Verify your email and API token are correct. The email must match the Atlassian account that owns the API token.

### "Permission denied" errors on specific tools

Your Atlassian account needs appropriate permissions. Administrative tools (field management, workflow management) require Jira Administrator access.
