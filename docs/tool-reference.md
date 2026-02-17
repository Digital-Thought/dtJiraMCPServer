# Tool Reference

Complete reference for all 47 tools provided by dtJiraMCPServer. For detailed parameter documentation, use the `get_tool_guide` tool at runtime.

## Meta Tools

### list_available_tools

List all available tools grouped by category.

- **Parameters**: None
- **Returns**: Categorised tool listing with names and descriptions

### get_tool_guide

Get detailed usage documentation for a specific tool.

- **Parameters**: `tool_name` (string, required)
- **Returns**: Full guide with parameters, examples, and notes

---

## Issue Management

### jql_search

Execute a JQL query and return matching issues.

- **Parameters**: `jql` (string, required), `start`, `limit`, `fields` (array), `expand` (array)
- **API**: `POST /rest/api/3/search/jql` (cursor-based pagination)

### issue_get

Get full details of a single issue.

- **Parameters**: `issue_key` (string, required), `fields` (array), `expand` (array)
- **API**: `GET /rest/api/3/issue/{issueIdOrKey}`

### issue_create

Create a new issue in Jira.

- **Parameters**: `project_key`, `issue_type`, `summary` (all required), `description`, `priority`, `assignee`, `labels`, `custom_fields`
- **API**: `POST /rest/api/3/issue`

### issue_update

Update fields on an existing issue.

- **Parameters**: `issue_key` (string, required), `fields` (object, required)
- **API**: `PUT /rest/api/3/issue/{issueIdOrKey}`

### issue_transition

Transition an issue to a new status.

- **Parameters**: `issue_key`, `transition_id` (both required), `comment`, `fields`
- **API**: `POST /rest/api/3/issue/{issueIdOrKey}/transitions`

### issue_get_transitions

List available transitions for an issue.

- **Parameters**: `issue_key` (string, required)
- **API**: `GET /rest/api/3/issue/{issueIdOrKey}/transitions`

### issue_delete

Delete an issue.

- **Parameters**: `issue_key` (string, required), `delete_subtasks` (boolean)
- **API**: `DELETE /rest/api/3/issue/{issueIdOrKey}`

---

## Service Desk Management

### servicedesk_list

List all accessible service desks.

- **Parameters**: `start`, `limit`
- **API**: `GET /rest/servicedeskapi/servicedesk`

### servicedesk_get

Get details of a specific service desk.

- **Parameters**: `service_desk_id` (integer, required)
- **API**: `GET /rest/servicedeskapi/servicedesk/{serviceDeskId}`

### servicedesk_get_queues

List queues for a service desk.

- **Parameters**: `service_desk_id` (integer, required), `include_count` (boolean), `start`, `limit`
- **API**: `GET /rest/servicedeskapi/servicedesk/{serviceDeskId}/queue`

### servicedesk_get_queue_issues

List issues in a queue.

- **Parameters**: `service_desk_id`, `queue_id` (both integer, required), `start`, `limit`
- **API**: `GET /rest/servicedeskapi/servicedesk/{serviceDeskId}/queue/{queueId}/issue`

### servicedesk_get_customers

List customers for a service desk.

- **Parameters**: `service_desk_id` (integer, required), `query` (string), `start`, `limit`
- **API**: `GET /rest/servicedeskapi/servicedesk/{serviceDeskId}/customer`

### servicedesk_add_customers

Add customers to a service desk.

- **Parameters**: `service_desk_id` (integer, required), `account_ids` (array, required)
- **API**: `POST /rest/servicedeskapi/servicedesk/{serviceDeskId}/customer`

### servicedesk_remove_customers

Remove customers from a service desk.

- **Parameters**: `service_desk_id` (integer, required), `account_ids` (array, required)
- **API**: `DELETE /rest/servicedeskapi/servicedesk/{serviceDeskId}/customer`

### servicedesk_get_organisations

List organisations linked to a service desk.

- **Parameters**: `service_desk_id` (integer, required), `start`, `limit`
- **API**: `GET /rest/servicedeskapi/servicedesk/{serviceDeskId}/organization`

### servicedesk_add_organisation

Add an organisation to a service desk.

- **Parameters**: `service_desk_id` (integer, required), `organisation_id` (integer, required)
- **API**: `POST /rest/servicedeskapi/servicedesk/{serviceDeskId}/organization`

### servicedesk_remove_organisation

Remove an organisation from a service desk.

- **Parameters**: `service_desk_id` (integer, required), `organisation_id` (integer, required)
- **API**: `DELETE /rest/servicedeskapi/servicedesk/{serviceDeskId}/organization`

---

## Request Type Management

### requesttype_list

List request types for a service desk.

- **Parameters**: `service_desk_id` (integer, required), `search_query`, `group_id`, `start`, `limit`
- **API**: `GET /rest/servicedeskapi/servicedesk/{serviceDeskId}/requesttype`

### requesttype_get

Get details of a specific request type.

- **Parameters**: `service_desk_id`, `request_type_id` (both integer, required)
- **API**: `GET /rest/servicedeskapi/servicedesk/{serviceDeskId}/requesttype/{requestTypeId}`

### requesttype_create

Create a new request type.

- **Parameters**: `service_desk_id` (integer, required), `name`, `issue_type_id` (both string, required), `description`, `help_text`
- **API**: `POST /rest/servicedeskapi/servicedesk/{serviceDeskId}/requesttype`

### requesttype_delete

Delete a request type.

- **Parameters**: `service_desk_id`, `request_type_id` (both integer, required)
- **API**: `DELETE /rest/servicedeskapi/servicedesk/{serviceDeskId}/requesttype/{requestTypeId}`

### requesttype_get_fields

Get fields configured for a request type.

- **Parameters**: `service_desk_id`, `request_type_id` (both integer, required)
- **API**: `GET /rest/servicedeskapi/servicedesk/{serviceDeskId}/requesttype/{requestTypeId}/field`

### requesttype_get_groups

List request type groups for a service desk.

- **Parameters**: `service_desk_id` (integer, required), `start`, `limit`
- **API**: `GET /rest/servicedeskapi/servicedesk/{serviceDeskId}/requesttypegroup`

---

## Field Management

### field_list

List all Jira fields (system and custom).

- **Parameters**: `type_filter` (string: "system", "custom", "all")
- **API**: `GET /rest/api/3/field` (returns flat array, no pagination)

### field_create

Create a new custom field.

- **Parameters**: `name`, `field_type` (both string, required), `description`, `searcher_key`
- **API**: `POST /rest/api/3/field`

### field_update

Update an existing custom field.

- **Parameters**: `field_id` (string, required), `name`, `description`, `searcher_key`
- **API**: `PUT /rest/api/3/field/{fieldId}`

### field_get_contexts

Get contexts for a custom field.

- **Parameters**: `field_id` (string, required), `start`, `limit`
- **API**: `GET /rest/api/3/field/{fieldId}/context`

### field_add_context

Add a context to a custom field.

- **Parameters**: `field_id`, `name` (both string, required), `description`, `project_ids` (array), `issue_type_ids` (array)
- **API**: `POST /rest/api/3/field/{fieldId}/context`

### screen_list

List all Jira screens.

- **Parameters**: `start`, `limit`
- **API**: `GET /rest/api/3/screens`

### screen_get

Get a screen's tabs and fields.

- **Parameters**: `screen_id` (integer, required)
- **API**: `GET /rest/api/3/screens/{screenId}/tabs`

### screen_add_field

Add a field to a screen tab.

- **Parameters**: `screen_id`, `tab_id` (both integer, required), `field_id` (string, required)
- **API**: `POST /rest/api/3/screens/{screenId}/tabs/{tabId}/fields`

### screen_scheme_list

List all screen schemes.

- **Parameters**: `start`, `limit`
- **API**: `GET /rest/api/3/screenscheme`

### screen_scheme_get

Get details of a screen scheme.

- **Parameters**: `screen_scheme_id` (integer, required)
- **API**: `GET /rest/api/3/screenscheme?id={id}`

---

## Workflow Management

### workflow_list

List all Jira workflows.

- **Parameters**: `start`, `limit`
- **API**: `GET /rest/api/3/workflow/search`

### workflow_get

Get workflow details including statuses and transitions.

- **Parameters**: `workflow_name` (string, required)
- **API**: `GET /rest/api/3/workflow/search?workflowName={name}&expand=transitions,statuses`

### workflow_create

Create a new workflow.

- **Parameters**: `name` (string, required), `statuses` (array, required), `transitions` (array, required), `description`, `scope_type`, `scope_project_id`
- **API**: `POST /rest/api/3/workflows/create`

### status_list

List all statuses with optional category filtering.

- **Parameters**: `status_category` (string: "TODO", "IN_PROGRESS", "DONE"), `search_string`, `start`, `limit`
- **API**: `GET /rest/api/3/statuses/search`

### status_get

Get details of a status by ID or name.

- **Parameters**: `status_id_or_name` (string, required)
- **API**: `GET /rest/api/3/status/{idOrName}`

### status_create

Create a new status.

- **Parameters**: `name`, `status_category` (both string, required), `description`, `scope_type`, `scope_project_id`
- **API**: `POST /rest/api/3/statuses`

### transition_list

List transitions for a workflow.

- **Parameters**: `workflow_name` (string, required)
- **API**: `GET /rest/api/3/workflow/search?workflowName={name}&expand=transitions`

### transition_get

Get detailed transition information including rules.

- **Parameters**: `workflow_name`, `transition_id` (both string, required)
- **API**: `GET /rest/api/3/workflow/search?workflowName={name}&expand=transitions,transitions.rules`

---

## Knowledge Base

### knowledgebase_search

Search knowledge base articles.

- **Parameters**: `query` (string, required), `highlight` (boolean), `service_desk_id` (integer), `start`, `limit`
- **API**: `GET /rest/servicedeskapi/knowledgebase/article` or `GET /rest/servicedeskapi/servicedesk/{id}/knowledgebase/article`

---

## SLA Management

### sla_get_metrics

Get all SLA metrics for a customer request.

- **Parameters**: `issue_key` (string, required), `start`, `limit`
- **API**: `GET /rest/servicedeskapi/request/{issueIdOrKey}/sla`

### sla_get_detail

Get detailed SLA information for a specific metric.

- **Parameters**: `issue_key` (string, required), `metric_id` (integer, required)
- **API**: `GET /rest/servicedeskapi/request/{issueIdOrKey}/sla/{slaMetricId}`

---

## Asset Management

### assets_get_workspaces

List available Assets workspace IDs.

- **Parameters**: None
- **API**: `GET /rest/servicedeskapi/assets/workspace`
