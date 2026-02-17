# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- Project management tools (5): `project_list`, `project_get`, `project_create`, `project_update`, `project_delete`
- Lookup tools (3): `issue_type_list`, `priority_list`, `user_search`
- Group management tools (6): `group_list`, `group_get_members`, `group_create`, `group_add_user`, `group_remove_user`, `group_delete`
- Read-only mode via `JIRA_READ_ONLY` environment variable — restricts server to 38 non-mutating tools
- `mutates` attribute on BaseTool for tool classification (read-only vs mutating)
- `validate_project_key()` validator for Jira project key format
- Unit tests for all new tools and read-only mode (445 tests, 93% coverage)

## [0.1.0] - 2026-02-17

### Added

- Project scaffolding and core infrastructure with dtPyAppFramework
- Atlassian HTTP client layer with rate limiting, exponential backoff, and error classification
- Platform API client for Jira Cloud REST API v3
- JSM API client for Jira Service Management REST API with experimental header support
- Pagination handler normalising Platform (startAt/maxResults) and JSM (start/limit/isLastPage) conventions
- Input validation utilities for strings, integers, enums, issue keys, and pagination
- Custom exception hierarchy mapping to Atlassian API error categories
- MCP server orchestration with stdio transport
- Tool framework with base tool class, auto-discovery registry, and safe_execute pattern
- Dockerfile for containerised deployment (python:3.12-slim, non-root user)
- Self-documentation meta-tools: `list_available_tools`, `get_tool_guide`
- Issue management tools (7): `jql_search`, `issue_get`, `issue_create`, `issue_update`, `issue_transition`, `issue_get_transitions`, `issue_delete`
- Service desk tools (10): `servicedesk_list`, `servicedesk_get`, `servicedesk_get_queues`, `servicedesk_get_queue_issues`, `servicedesk_get_customers`, `servicedesk_add_customers`, `servicedesk_remove_customers`, `servicedesk_get_organisations`, `servicedesk_add_organisation`, `servicedesk_remove_organisation`
- Request type tools (6): `requesttype_list`, `requesttype_get`, `requesttype_create`, `requesttype_delete`, `requesttype_get_fields`, `requesttype_get_groups`
- Field management tools (10): `field_list`, `field_create`, `field_update`, `field_get_contexts`, `field_add_context`, `screen_list`, `screen_get`, `screen_add_field`, `screen_scheme_list`, `screen_scheme_get`
- Workflow management tools (8): `workflow_list`, `workflow_get`, `workflow_create`, `status_list`, `status_get`, `status_create`, `transition_list`, `transition_get`
- Knowledge base tool: `knowledgebase_search`
- SLA tools (2): `sla_get_metrics`, `sla_get_detail`
- Asset tool: `assets_get_workspaces`
- Unit test suite (340 tests, 93% coverage)
- Integration tests for Platform and JSM APIs
- Documentation: installation guide, user guide, tool reference
