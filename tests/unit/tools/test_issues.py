"""Tests for issue management tools (Phase 3)."""

from __future__ import annotations

from typing import Any
from unittest.mock import AsyncMock

import pytest

from dtjiramcpserver.exceptions import InputValidationError, NotFoundError
from tests.conftest import EXPECTED_TOOL_COUNT
from dtjiramcpserver.tools.issues.create import IssueCreateTool
from dtjiramcpserver.tools.issues.delete import IssueDeleteTool
from dtjiramcpserver.tools.issues.get import IssueGetTool
from dtjiramcpserver.tools.issues.search import JqlSearchTool
from dtjiramcpserver.tools.issues.transition import (
    IssueGetTransitionsTool,
    IssueTransitionTool,
)
from dtjiramcpserver.tools.issues.update import IssueUpdateTool


@pytest.fixture
def platform_client() -> AsyncMock:
    """Mocked PlatformClient for issue tools."""
    client = AsyncMock()
    client.base_url = "https://test.atlassian.net/rest/api/3"
    return client


def _make_tool(tool_cls: type, client: AsyncMock) -> Any:
    """Instantiate a tool with a mocked platform client."""
    return tool_cls(platform_client=client)


# --------------------------------------------------------------------------- #
# JqlSearchTool
# --------------------------------------------------------------------------- #


class TestJqlSearchTool:
    """Tests for jql_search tool."""

    class TestValidation:
        """Input validation tests."""

        @pytest.mark.asyncio
        async def test_missing_jql_returns_error(self, platform_client: AsyncMock) -> None:
            """Missing jql parameter returns VALIDATION_ERROR."""
            tool = _make_tool(JqlSearchTool, platform_client)
            result = await tool.safe_execute({})
            assert result.success is False
            assert result.error["type"] == "VALIDATION_ERROR"

        @pytest.mark.asyncio
        async def test_empty_jql_returns_error(self, platform_client: AsyncMock) -> None:
            """Empty jql string returns VALIDATION_ERROR."""
            tool = _make_tool(JqlSearchTool, platform_client)
            result = await tool.safe_execute({"jql": ""})
            assert result.success is False
            assert result.error["type"] == "VALIDATION_ERROR"

    class TestExecution:
        """Successful execution tests."""

        @pytest.mark.asyncio
        async def test_simple_search(self, platform_client: AsyncMock) -> None:
            """Simple JQL search returns cursor-paginated results."""
            platform_client.post.return_value = {
                "issues": [{"key": "PROJ-1"}, {"key": "PROJ-2"}],
                "isLast": True,
            }
            tool = _make_tool(JqlSearchTool, platform_client)
            result = await tool.safe_execute({"jql": "project = PROJ"})

            assert result.success is True
            assert len(result.data) == 2
            assert result.pagination["returned"] == 2
            assert result.pagination["has_more"] is False

        @pytest.mark.asyncio
        async def test_has_more_with_next_token(self, platform_client: AsyncMock) -> None:
            """When isLast=False, returns next_page_token in pagination."""
            platform_client.post.return_value = {
                "issues": [{"key": "PROJ-1"}],
                "isLast": False,
                "nextPageToken": "cursor123",
            }
            tool = _make_tool(JqlSearchTool, platform_client)
            result = await tool.safe_execute({"jql": "project = PROJ", "limit": 1})

            assert result.pagination["has_more"] is True
            assert result.pagination["next_page_token"] == "cursor123"

        @pytest.mark.asyncio
        async def test_passes_fields_and_expand(self, platform_client: AsyncMock) -> None:
            """Fields and expand parameters are passed in the POST body."""
            platform_client.post.return_value = {"issues": [], "isLast": True}
            tool = _make_tool(JqlSearchTool, platform_client)
            await tool.safe_execute({
                "jql": "project = PROJ",
                "fields": ["summary", "status"],
                "expand": ["changelog"],
                "limit": 10,
            })

            call_args = platform_client.post.call_args
            json_body = call_args.kwargs.get("json") or call_args[1].get("json")
            assert json_body["fields"] == ["summary", "status"]
            assert json_body["expand"] == ["changelog"]

        @pytest.mark.asyncio
        async def test_next_page_token_forwarded(self, platform_client: AsyncMock) -> None:
            """next_page_token is forwarded in the POST body."""
            platform_client.post.return_value = {"issues": [], "isLast": True}
            tool = _make_tool(JqlSearchTool, platform_client)
            await tool.safe_execute({
                "jql": "project = PROJ",
                "next_page_token": "cursor123",
            })

            call_args = platform_client.post.call_args
            json_body = call_args.kwargs.get("json") or call_args[1].get("json")
            assert json_body["nextPageToken"] == "cursor123"

        @pytest.mark.asyncio
        async def test_limit_forwarded(self, platform_client: AsyncMock) -> None:
            """Limit is forwarded as maxResults."""
            platform_client.post.return_value = {"issues": [], "isLast": True}
            tool = _make_tool(JqlSearchTool, platform_client)
            await tool.safe_execute({"jql": "project = PROJ", "limit": 25})

            call_args = platform_client.post.call_args
            json_body = call_args.kwargs.get("json") or call_args[1].get("json")
            assert json_body["maxResults"] == 25

    class TestGuide:
        """Self-documentation tests."""

        def test_guide_has_correct_metadata(self) -> None:
            """Guide returns correct name and category."""
            tool = JqlSearchTool()
            guide = tool.get_guide()
            assert guide.name == "jql_search"
            assert guide.category == "issues"
            assert len(guide.parameters) == 5  # jql, limit, next_page_token, fields, expand
            assert guide.parameters[0].name == "jql"
            assert guide.parameters[0].required is True


# --------------------------------------------------------------------------- #
# IssueGetTool
# --------------------------------------------------------------------------- #


class TestIssueGetTool:
    """Tests for issue_get tool."""

    class TestValidation:

        @pytest.mark.asyncio
        async def test_missing_issue_key(self, platform_client: AsyncMock) -> None:
            """Missing issue_key returns VALIDATION_ERROR."""
            tool = _make_tool(IssueGetTool, platform_client)
            result = await tool.safe_execute({})
            assert result.success is False
            assert result.error["type"] == "VALIDATION_ERROR"

        @pytest.mark.asyncio
        async def test_invalid_issue_key_format(self, platform_client: AsyncMock) -> None:
            """Invalid issue key format returns VALIDATION_ERROR."""
            tool = _make_tool(IssueGetTool, platform_client)
            result = await tool.safe_execute({"issue_key": "invalid"})
            assert result.success is False
            assert result.error["type"] == "VALIDATION_ERROR"

    class TestExecution:

        @pytest.mark.asyncio
        async def test_get_issue(self, platform_client: AsyncMock) -> None:
            """Successful issue retrieval returns issue data."""
            platform_client.get.return_value = {
                "key": "PROJ-123",
                "id": "10001",
                "fields": {"summary": "Test issue"},
            }
            tool = _make_tool(IssueGetTool, platform_client)
            result = await tool.safe_execute({"issue_key": "PROJ-123"})

            assert result.success is True
            assert result.data["key"] == "PROJ-123"

        @pytest.mark.asyncio
        async def test_get_with_fields(self, platform_client: AsyncMock) -> None:
            """Fields parameter limits returned data."""
            platform_client.get.return_value = {"key": "PROJ-123", "fields": {"summary": "Test"}}
            tool = _make_tool(IssueGetTool, platform_client)
            await tool.safe_execute({"issue_key": "PROJ-123", "fields": ["summary"]})

            call_args = platform_client.get.call_args
            params = call_args.kwargs.get("params") or call_args[1].get("params")
            assert params["fields"] == "summary"

        @pytest.mark.asyncio
        async def test_lowercase_key_normalised(self, platform_client: AsyncMock) -> None:
            """Lowercase issue key is normalised to uppercase."""
            platform_client.get.return_value = {"key": "PROJ-123"}
            tool = _make_tool(IssueGetTool, platform_client)
            await tool.safe_execute({"issue_key": "proj-123"})

            call_args = platform_client.get.call_args
            assert "/issue/PROJ-123" == call_args[0][0]

    class TestErrorHandling:

        @pytest.mark.asyncio
        async def test_not_found(self, platform_client: AsyncMock) -> None:
            """Non-existent issue returns NOT_FOUND."""
            platform_client.get.side_effect = NotFoundError(message="Issue not found")
            tool = _make_tool(IssueGetTool, platform_client)
            result = await tool.safe_execute({"issue_key": "PROJ-999"})

            assert result.success is False
            assert result.error["type"] == "NOT_FOUND"

    class TestGuide:

        def test_guide_metadata(self) -> None:
            tool = IssueGetTool()
            guide = tool.get_guide()
            assert guide.name == "issue_get"
            assert guide.parameters[0].name == "issue_key"


# --------------------------------------------------------------------------- #
# IssueCreateTool
# --------------------------------------------------------------------------- #


class TestIssueCreateTool:
    """Tests for issue_create tool."""

    class TestValidation:

        @pytest.mark.asyncio
        async def test_missing_required_fields(self, platform_client: AsyncMock) -> None:
            """Missing required fields return VALIDATION_ERROR."""
            tool = _make_tool(IssueCreateTool, platform_client)
            result = await tool.safe_execute({"project_key": "PROJ"})
            assert result.success is False
            assert result.error["type"] == "VALIDATION_ERROR"

        @pytest.mark.asyncio
        async def test_empty_summary(self, platform_client: AsyncMock) -> None:
            """Empty summary returns VALIDATION_ERROR."""
            tool = _make_tool(IssueCreateTool, platform_client)
            result = await tool.safe_execute({
                "project_key": "PROJ",
                "issue_type": "Task",
                "summary": "",
            })
            assert result.success is False
            assert result.error["type"] == "VALIDATION_ERROR"

    class TestExecution:

        @pytest.mark.asyncio
        async def test_create_simple_issue(self, platform_client: AsyncMock) -> None:
            """Create issue with minimum required fields."""
            platform_client.post.return_value = {
                "id": "10001",
                "key": "PROJ-1",
                "self": "https://test.atlassian.net/rest/api/3/issue/10001",
            }
            tool = _make_tool(IssueCreateTool, platform_client)
            result = await tool.safe_execute({
                "project_key": "PROJ",
                "issue_type": "Task",
                "summary": "Test issue",
            })

            assert result.success is True
            assert result.data["key"] == "PROJ-1"

            # Verify API payload
            call_args = platform_client.post.call_args
            json_body = call_args.kwargs.get("json") or call_args[1].get("json")
            assert json_body["fields"]["project"]["key"] == "PROJ"
            assert json_body["fields"]["issuetype"]["name"] == "Task"
            assert json_body["fields"]["summary"] == "Test issue"

        @pytest.mark.asyncio
        async def test_create_with_all_optional_fields(self, platform_client: AsyncMock) -> None:
            """Create issue with all optional fields."""
            platform_client.post.return_value = {"id": "10002", "key": "PROJ-2"}
            tool = _make_tool(IssueCreateTool, platform_client)
            result = await tool.safe_execute({
                "project_key": "PROJ",
                "issue_type": "Bug",
                "summary": "Bug report",
                "description": "Something is broken",
                "priority": "High",
                "assignee": "abc123",
                "labels": ["urgent", "frontend"],
                "custom_fields": {"customfield_10001": "custom value"},
            })

            assert result.success is True
            call_args = platform_client.post.call_args
            json_body = call_args.kwargs.get("json") or call_args[1].get("json")
            fields = json_body["fields"]
            assert fields["priority"]["name"] == "High"
            assert fields["assignee"]["accountId"] == "abc123"
            assert fields["labels"] == ["urgent", "frontend"]
            assert fields["customfield_10001"] == "custom value"
            # Description converted to ADF
            assert fields["description"]["type"] == "doc"

    class TestGuide:

        def test_guide_metadata(self) -> None:
            tool = IssueCreateTool()
            guide = tool.get_guide()
            assert guide.name == "issue_create"
            required_params = [p for p in guide.parameters if p.required]
            assert len(required_params) == 3


# --------------------------------------------------------------------------- #
# IssueUpdateTool
# --------------------------------------------------------------------------- #


class TestIssueUpdateTool:
    """Tests for issue_update tool."""

    class TestValidation:

        @pytest.mark.asyncio
        async def test_missing_issue_key(self, platform_client: AsyncMock) -> None:
            tool = _make_tool(IssueUpdateTool, platform_client)
            result = await tool.safe_execute({"fields": {"summary": "x"}})
            assert result.success is False
            assert result.error["type"] == "VALIDATION_ERROR"

        @pytest.mark.asyncio
        async def test_missing_fields(self, platform_client: AsyncMock) -> None:
            tool = _make_tool(IssueUpdateTool, platform_client)
            result = await tool.safe_execute({"issue_key": "PROJ-1"})
            assert result.success is False
            assert result.error["type"] == "VALIDATION_ERROR"

        @pytest.mark.asyncio
        async def test_empty_fields_object(self, platform_client: AsyncMock) -> None:
            """Empty fields dict returns VALIDATION_ERROR."""
            tool = _make_tool(IssueUpdateTool, platform_client)
            result = await tool.safe_execute({"issue_key": "PROJ-1", "fields": {}})
            assert result.success is False
            assert result.error["type"] == "VALIDATION_ERROR"

    class TestExecution:

        @pytest.mark.asyncio
        async def test_update_fields(self, platform_client: AsyncMock) -> None:
            """Successful update returns confirmation."""
            platform_client.put.return_value = None
            tool = _make_tool(IssueUpdateTool, platform_client)
            result = await tool.safe_execute({
                "issue_key": "PROJ-1",
                "fields": {"summary": "Updated title"},
            })

            assert result.success is True
            assert result.data["updated"] is True
            assert result.data["issue_key"] == "PROJ-1"

    class TestGuide:

        def test_guide_metadata(self) -> None:
            tool = IssueUpdateTool()
            guide = tool.get_guide()
            assert guide.name == "issue_update"
            assert len(guide.parameters) == 2


# --------------------------------------------------------------------------- #
# IssueGetTransitionsTool
# --------------------------------------------------------------------------- #


class TestIssueGetTransitionsTool:
    """Tests for issue_get_transitions tool."""

    class TestValidation:

        @pytest.mark.asyncio
        async def test_missing_issue_key(self, platform_client: AsyncMock) -> None:
            tool = _make_tool(IssueGetTransitionsTool, platform_client)
            result = await tool.safe_execute({})
            assert result.success is False
            assert result.error["type"] == "VALIDATION_ERROR"

    class TestExecution:

        @pytest.mark.asyncio
        async def test_get_transitions(self, platform_client: AsyncMock) -> None:
            """Returns available transitions."""
            platform_client.get.return_value = {
                "transitions": [
                    {"id": "21", "name": "In Progress", "to": {"name": "In Progress"}},
                    {"id": "31", "name": "Done", "to": {"name": "Done"}},
                ]
            }
            tool = _make_tool(IssueGetTransitionsTool, platform_client)
            result = await tool.safe_execute({"issue_key": "PROJ-1"})

            assert result.success is True
            assert len(result.data) == 2
            assert result.data[0]["id"] == "21"

    class TestGuide:

        def test_guide_metadata(self) -> None:
            tool = IssueGetTransitionsTool()
            guide = tool.get_guide()
            assert guide.name == "issue_get_transitions"
            assert "issue_transition" in (guide.related_tools or [])


# --------------------------------------------------------------------------- #
# IssueTransitionTool
# --------------------------------------------------------------------------- #


class TestIssueTransitionTool:
    """Tests for issue_transition tool."""

    class TestValidation:

        @pytest.mark.asyncio
        async def test_missing_transition_id(self, platform_client: AsyncMock) -> None:
            tool = _make_tool(IssueTransitionTool, platform_client)
            result = await tool.safe_execute({"issue_key": "PROJ-1"})
            assert result.success is False
            assert result.error["type"] == "VALIDATION_ERROR"

    class TestExecution:

        @pytest.mark.asyncio
        async def test_simple_transition(self, platform_client: AsyncMock) -> None:
            """Simple transition without comment or fields."""
            platform_client.post.return_value = {}
            tool = _make_tool(IssueTransitionTool, platform_client)
            result = await tool.safe_execute({
                "issue_key": "PROJ-1",
                "transition_id": "21",
            })

            assert result.success is True
            assert result.data["transitioned"] is True

            call_args = platform_client.post.call_args
            json_body = call_args.kwargs.get("json") or call_args[1].get("json")
            assert json_body["transition"]["id"] == "21"
            assert "update" not in json_body
            assert "fields" not in json_body

        @pytest.mark.asyncio
        async def test_transition_with_comment(self, platform_client: AsyncMock) -> None:
            """Transition with a comment includes the update block."""
            platform_client.post.return_value = {}
            tool = _make_tool(IssueTransitionTool, platform_client)
            result = await tool.safe_execute({
                "issue_key": "PROJ-1",
                "transition_id": "31",
                "comment": "Closing this issue",
            })

            assert result.success is True
            call_args = platform_client.post.call_args
            json_body = call_args.kwargs.get("json") or call_args[1].get("json")
            assert "update" in json_body
            assert json_body["update"]["comment"][0]["add"]["body"]["type"] == "doc"

        @pytest.mark.asyncio
        async def test_transition_with_fields(self, platform_client: AsyncMock) -> None:
            """Transition with required fields includes them in the payload."""
            platform_client.post.return_value = {}
            tool = _make_tool(IssueTransitionTool, platform_client)
            result = await tool.safe_execute({
                "issue_key": "PROJ-1",
                "transition_id": "31",
                "fields": {"resolution": {"name": "Done"}},
            })

            assert result.success is True
            call_args = platform_client.post.call_args
            json_body = call_args.kwargs.get("json") or call_args[1].get("json")
            assert json_body["fields"]["resolution"]["name"] == "Done"

    class TestGuide:

        def test_guide_metadata(self) -> None:
            tool = IssueTransitionTool()
            guide = tool.get_guide()
            assert guide.name == "issue_transition"
            assert len(guide.parameters) == 4


# --------------------------------------------------------------------------- #
# IssueDeleteTool
# --------------------------------------------------------------------------- #


class TestIssueDeleteTool:
    """Tests for issue_delete tool."""

    class TestValidation:

        @pytest.mark.asyncio
        async def test_missing_issue_key(self, platform_client: AsyncMock) -> None:
            tool = _make_tool(IssueDeleteTool, platform_client)
            result = await tool.safe_execute({})
            assert result.success is False
            assert result.error["type"] == "VALIDATION_ERROR"

    class TestExecution:

        @pytest.mark.asyncio
        async def test_delete_issue(self, platform_client: AsyncMock) -> None:
            """Successful deletion returns confirmation."""
            platform_client.delete.return_value = None
            tool = _make_tool(IssueDeleteTool, platform_client)
            result = await tool.safe_execute({"issue_key": "PROJ-1"})

            assert result.success is True
            assert result.data["deleted"] is True
            assert result.data["issue_key"] == "PROJ-1"

        @pytest.mark.asyncio
        async def test_delete_with_subtasks(self, platform_client: AsyncMock) -> None:
            """Delete with subtasks passes the query parameter."""
            platform_client.delete.return_value = None
            tool = _make_tool(IssueDeleteTool, platform_client)
            result = await tool.safe_execute({
                "issue_key": "PROJ-1",
                "delete_subtasks": True,
            })

            assert result.success is True
            call_args = platform_client.delete.call_args
            params = call_args.kwargs.get("params") or call_args[1].get("params")
            assert params["deleteSubtasks"] == "true"

        @pytest.mark.asyncio
        async def test_not_found(self, platform_client: AsyncMock) -> None:
            """Deleting non-existent issue returns NOT_FOUND."""
            platform_client.delete.side_effect = NotFoundError(message="Issue not found")
            tool = _make_tool(IssueDeleteTool, platform_client)
            result = await tool.safe_execute({"issue_key": "PROJ-999"})

            assert result.success is False
            assert result.error["type"] == "NOT_FOUND"

    class TestGuide:

        def test_guide_metadata(self) -> None:
            tool = IssueDeleteTool()
            guide = tool.get_guide()
            assert guide.name == "issue_delete"
            assert guide.parameters[1].name == "delete_subtasks"
            assert guide.parameters[1].default is False


# --------------------------------------------------------------------------- #
# Registry integration
# --------------------------------------------------------------------------- #


class TestIssueToolRegistration:
    """Tests for issue tool auto-discovery via registry."""

    def test_all_issue_tools_discovered(self) -> None:
        """All 7 issue tools are discovered by the registry."""
        from dtjiramcpserver.tools.registry import ToolRegistry

        registry = ToolRegistry()
        registry.discover_and_register()

        expected_names = {
            "jql_search",
            "issue_get",
            "issue_create",
            "issue_update",
            "issue_transition",
            "issue_get_transitions",
            "issue_delete",
        }

        categories = registry.get_tools_by_category()
        assert "issues" in categories
        issue_names = {t.name for t in categories["issues"]}
        assert expected_names == issue_names

    def test_tool_count_includes_issues(self) -> None:
        """Registry count includes meta tools + issue tools."""
        from dtjiramcpserver.tools.registry import ToolRegistry

        registry = ToolRegistry()
        registry.discover_and_register()
        assert registry.tool_count == EXPECTED_TOOL_COUNT
