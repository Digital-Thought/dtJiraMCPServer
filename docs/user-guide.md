# User Guide

## How It Works

dtJiraMCPServer acts as a bridge between an LLM client and Atlassian Jira Cloud / JSM Cloud. The LLM discovers available tools, reads their guides, and invokes them with structured parameters. The server handles authentication, validation, pagination, and error handling transparently.

```
LLM Client  <--stdio-->  dtJiraMCPServer  <--HTTPS-->  Atlassian Cloud APIs
```

## Self-Documentation System

The server provides two meta-tools that enable the LLM to discover and learn tools at runtime:

### list_available_tools

Returns all tools grouped by category (61 in normal mode, 38 in read-only mode). The LLM typically calls this first to understand what's available.

### get_tool_guide

Returns detailed usage documentation for a specific tool, including:

- Parameters with types, constraints, and defaults
- Response format examples
- Related tools
- Usage notes and prerequisites

## Tool Categories

### Issues (7 tools)

Core issue management operations.

| Tool | Description |
|------|-------------|
| `jql_search` | Execute JQL queries with pagination |
| `issue_get` | Get full issue details by key |
| `issue_create` | Create a new issue |
| `issue_update` | Update issue fields |
| `issue_transition` | Move issue to a new status |
| `issue_get_transitions` | List available transitions for an issue |
| `issue_delete` | Delete an issue |

### Service Desk (10 tools)

JSM service desk management.

| Tool | Description |
|------|-------------|
| `servicedesk_list` | List all service desks |
| `servicedesk_get` | Get service desk details |
| `servicedesk_get_queues` | List queues for a service desk |
| `servicedesk_get_queue_issues` | List issues in a queue |
| `servicedesk_get_customers` | List customers for a service desk |
| `servicedesk_add_customers` | Add customers to a service desk |
| `servicedesk_remove_customers` | Remove customers from a service desk |
| `servicedesk_get_organisations` | List organisations for a service desk |
| `servicedesk_add_organisation` | Add an organisation to a service desk |
| `servicedesk_remove_organisation` | Remove an organisation from a service desk |

### Request Types (6 tools)

JSM request type configuration.

| Tool | Description |
|------|-------------|
| `requesttype_list` | List request types for a service desk |
| `requesttype_get` | Get request type details |
| `requesttype_create` | Create a new request type |
| `requesttype_delete` | Delete a request type |
| `requesttype_get_fields` | Get fields for a request type |
| `requesttype_get_groups` | List request type groups |

### Fields (10 tools)

Custom field and screen management.

| Tool | Description |
|------|-------------|
| `field_list` | List all fields (system and custom) |
| `field_create` | Create a new custom field |
| `field_update` | Update a custom field |
| `field_get_contexts` | Get contexts for a custom field |
| `field_add_context` | Add a context to a custom field |
| `screen_list` | List all screens |
| `screen_get` | Get screen tabs and fields |
| `screen_add_field` | Add a field to a screen tab |
| `screen_scheme_list` | List all screen schemes |
| `screen_scheme_get` | Get screen scheme details |

### Workflows (8 tools)

Workflow, status, and transition management.

| Tool | Description |
|------|-------------|
| `workflow_list` | List all workflows |
| `workflow_get` | Get workflow with statuses and transitions |
| `workflow_create` | Create a new workflow |
| `status_list` | List all statuses with category filtering |
| `status_get` | Get status details |
| `status_create` | Create a new status |
| `transition_list` | List transitions for a workflow |
| `transition_get` | Get transition details with rules |

### Knowledge Base (1 tool)

| Tool | Description |
|------|-------------|
| `knowledgebase_search` | Search KB articles across service desks |

### SLA (2 tools)

| Tool | Description |
|------|-------------|
| `sla_get_metrics` | Get all SLA metrics for a request |
| `sla_get_detail` | Get detailed SLA cycle information |

### Assets (1 tool)

| Tool | Description |
|------|-------------|
| `assets_get_workspaces` | List available asset workspace IDs |

### Projects (5 tools)

Project management operations.

| Tool | Description |
|------|-------------|
| `project_list` | List all projects with filtering |
| `project_get` | Get full project details by key |
| `project_create` | Create a new project |
| `project_update` | Update project fields |
| `project_delete` | Delete a project (with optional undo) |

### Lookup (3 tools)

Reference data lookups for issue types, priorities, and users.

| Tool | Description |
|------|-------------|
| `issue_type_list` | List all available issue types |
| `priority_list` | List all available priorities |
| `user_search` | Search for users by name or email |

### Groups (6 tools)

Group management and membership.

| Tool | Description |
|------|-------------|
| `group_list` | List all groups |
| `group_get_members` | List members of a group |
| `group_create` | Create a new group |
| `group_add_user` | Add a user to a group |
| `group_remove_user` | Remove a user from a group |
| `group_delete` | Delete a group |

## Read-Only Mode

Set `JIRA_READ_ONLY=true` to restrict the server to read-only tools only. This prevents any tool that creates, modifies, or deletes resources from being registered.

In read-only mode, 38 tools are available (all list/get/search tools). The 23 mutating tools (create, update, delete, add, remove operations) are excluded.

## Pagination

All list operations support pagination with consistent parameters:

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `start` | integer | 0 | Starting index |
| `limit` | integer | 50 | Maximum results per page (max: 100) |

Responses include pagination metadata:

```json
{
  "pagination": {
    "start": 0,
    "limit": 50,
    "total": 150,
    "has_more": true
  }
}
```

## Error Handling

All errors return a structured format:

```json
{
  "success": false,
  "error": {
    "type": "NOT_FOUND",
    "message": "Issue PROJ-999 not found"
  }
}
```

Error types:

| Type | Meaning |
|------|---------|
| `VALIDATION_ERROR` | Invalid input parameters |
| `AUTHENTICATION_ERROR` | Invalid credentials (401) |
| `PERMISSION_ERROR` | Insufficient permissions (403) |
| `NOT_FOUND` | Resource does not exist (404) |
| `CONFLICT` | Resource conflict (409) |
| `RATE_LIMITED` | Too many requests (429) - retried automatically |
| `SERVER_ERROR` | Atlassian server error (5xx) - retried automatically |
| `NETWORK_ERROR` | Connection or timeout failure |

Rate limit (429) and server errors (5xx) are retried automatically with exponential backoff. The LLM only sees these errors if all retries are exhausted.

## Permissions

Tool availability depends on your Atlassian account permissions:

| Permission Level | Available Tools |
|-----------------|-----------------|
| Any user | Issue search, issue get, service desk list |
| Project member | Issue create, update, transition, delete |
| Service desk agent | Queue management, customer management |
| Jira Administrator | Field management, workflow management, screen management, project management, group management |
