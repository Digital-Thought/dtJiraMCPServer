# dtJiraMCPServer - Test Suite

## Structure

```
tests/
├── conftest.py                         # Shared pytest fixtures
├── unit/                               # Unit tests (no external dependencies)
│   ├── test_config.py                  # Configuration model validation
│   ├── test_errors.py                  # Error classification and mapping
│   ├── test_rate_limiter.py            # Rate limit retry behaviour
│   ├── test_pagination.py             # Pagination response parsing
│   ├── test_client.py                  # HTTP client (mocked httpx)
│   ├── test_validators.py             # Input validation functions
│   ├── test_tool_base.py              # BaseTool and ToolResult models
│   ├── test_tool_registry.py          # Tool registry auto-discovery
│   ├── test_meta_tools.py             # Meta-tool implementations
│   ├── test_server.py                  # MCP server orchestration
│   └── tools/                          # Tool-specific unit tests
│       ├── test_issues.py             # Issue management tools (7 tools)
│       ├── test_servicedesk.py        # Service desk tools (10 tools)
│       ├── test_requesttypes.py       # Request type tools (6 tools)
│       ├── test_fields.py            # Field management tools (10 tools)
│       ├── test_workflows.py          # Workflow management tools (8 tools)
│       └── test_phase8.py            # KB, SLA, and asset tools (4 tools)
└── integration/                        # Integration tests (require Jira credentials)
    └── test_live_tools.py             # Live API tests across all tool categories
```

## Running Tests

```bash
# All unit tests
pytest tests/unit/ -v

# With coverage
pytest tests/ -v --cov=dtjiramcpserver

# Specific test file
pytest tests/unit/test_validators.py -v

# Specific tool category
pytest tests/unit/tools/test_issues.py -v

# Integration tests (require environment variables)
export JIRA_INSTANCE_URL=https://your-domain.atlassian.net
export JIRA_USER_EMAIL=user@example.com
export JIRA_API_TOKEN=your-api-token
pytest tests/integration/ -v
```

## Test Patterns

### Unit Tests

Each tool test file follows a consistent structure:

```python
class TestToolName:
    class TestValidation:
        # Tests for missing/invalid parameters
        async def test_missing_required_param(self): ...

    class TestExecution:
        # Tests for successful API interaction (mocked)
        async def test_happy_path(self): ...

    class TestGuide:
        # Tests for self-documentation
        def test_guide_metadata(self): ...
```

### Integration Tests

Integration tests require real Jira credentials set via environment variables. They perform read-only operations against the configured instance to verify API compatibility.

Skipped automatically when credentials are not set.

## Coverage Target

Minimum 80% coverage on core modules (currently 93%). Security-critical functions
(credential handling, input validation) target 100% coverage.

## Test Count

| Category | Tests |
|----------|-------|
| Core infrastructure | 142 |
| Issue tools | 38 |
| Service desk tools | 38 |
| Request type tools | 25 |
| Field management tools | 42 |
| Workflow tools | 36 |
| KB/SLA/Asset tools | 17 |
| Integration | 2 |
| **Total** | **340** |
