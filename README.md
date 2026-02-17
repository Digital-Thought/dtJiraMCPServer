# dtJiraMCPServer

MCP Server for Jira Cloud and JSM Cloud administration via natural language.

## Overview

dtJiraMCPServer provides a [Model Context Protocol](https://modelcontextprotocol.io/) (MCP) server that bridges LLM clients (such as Claude Desktop or Claude Code) with Atlassian Jira Cloud and Jira Service Management (JSM) Cloud REST APIs. The server exposes 47 tools across 9 categories, enabling an LLM to perform administrative and operational tasks across both platforms.

## Features

- **47 tools** across 9 feature areas
- **Self-documenting** - LLMs can discover tools and read usage guides at runtime
- **Robust error handling** - structured errors with retry, rate limiting, and backoff
- **Input validation** - validates parameters before making API calls
- **Pagination** - consistent pagination across all list operations
- **Stateless** - no local state or caching; designed for containerised deployment

### Tool Categories

| Category | Tools | Description |
|----------|-------|-------------|
| Meta | 2 | Tool discovery and usage guides |
| Issues | 7 | JQL search, issue CRUD, transitions |
| Service Desk | 10 | Desks, queues, customers, organisations |
| Request Types | 6 | Request type CRUD, fields, groups |
| Fields | 10 | Custom fields, contexts, screens, screen schemes |
| Workflows | 8 | Workflows, statuses, transitions |
| Knowledge Base | 1 | Article search |
| SLA | 2 | SLA metrics and detail |
| Assets | 1 | Workspace queries |

See [docs/tool-reference.md](docs/tool-reference.md) for the complete tool listing.

## Quick Start

### Docker (Recommended)

```bash
docker build -t dtjiramcpserver:latest .

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

### Local Development

```bash
git clone <repo-url>
cd dtJiraMCPServer
python -m venv .venv
.venv\Scripts\activate  # Windows
# source .venv/bin/activate  # Linux/macOS
pip install -e ".[dev]"

export JIRA_INSTANCE_URL=https://your-domain.atlassian.net
export JIRA_USER_EMAIL=user@example.com
export JIRA_API_TOKEN=your-api-token
python -m dtjiramcpserver
```

See [docs/installation.md](docs/installation.md) for detailed setup instructions.

## Environment Variables

| Variable | Purpose | Required | Default |
|----------|---------|----------|---------|
| `JIRA_INSTANCE_URL` | Atlassian Cloud instance URL | Yes | - |
| `JIRA_USER_EMAIL` | Atlassian account email | Yes | - |
| `JIRA_API_TOKEN` | Atlassian API token | Yes | - |
| `LOG_LEVEL` | Application log level | No | `INFO` |

## MCP Client Configuration

### Claude Desktop

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

## Testing

```bash
# Unit tests
pytest tests/unit/ -v --cov=dtjiramcpserver

# Integration tests (require Jira credentials)
export JIRA_INSTANCE_URL=https://your-domain.atlassian.net
export JIRA_USER_EMAIL=user@example.com
export JIRA_API_TOKEN=your-api-token
pytest tests/integration/ -v
```

See [tests/README.md](tests/README.md) for test suite documentation.

## Documentation

- [Installation Guide](docs/installation.md) - Setup and configuration
- [User Guide](docs/user-guide.md) - How the LLM interacts with tools
- [Tool Reference](docs/tool-reference.md) - Complete tool listing and parameters

## Architecture

- **Transport**: stdio (MCP SDK native)
- **Client layer**: httpx-based async HTTP with rate limiting and retry
- **Tool framework**: Auto-discovery registry with structured error handling
- **Application**: dtPyAppFramework one-shot pattern

## Requirements

- Python 3.10+
- Atlassian Cloud instance with API token access
- Docker (for containerised deployment)

## Licence

MIT
