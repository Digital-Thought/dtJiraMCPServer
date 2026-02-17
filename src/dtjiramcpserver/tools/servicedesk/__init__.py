"""Service desk management tools - Phase 4.

Provides tools for listing service desks, managing queues,
customers, and organisations via the JSM REST API.
"""

from dtjiramcpserver.tools.servicedesk.customers import (
    ServiceDeskAddCustomersTool,
    ServiceDeskGetCustomersTool,
    ServiceDeskRemoveCustomersTool,
)
from dtjiramcpserver.tools.servicedesk.desks import (
    ServiceDeskGetTool,
    ServiceDeskListTool,
)
from dtjiramcpserver.tools.servicedesk.organisations import (
    ServiceDeskAddOrganisationTool,
    ServiceDeskGetOrganisationsTool,
    ServiceDeskRemoveOrganisationTool,
)
from dtjiramcpserver.tools.servicedesk.queues import (
    ServiceDeskGetQueueIssuesTool,
    ServiceDeskGetQueuesTool,
)

__all__ = [
    "ServiceDeskListTool",
    "ServiceDeskGetTool",
    "ServiceDeskGetQueuesTool",
    "ServiceDeskGetQueueIssuesTool",
    "ServiceDeskGetCustomersTool",
    "ServiceDeskAddCustomersTool",
    "ServiceDeskRemoveCustomersTool",
    "ServiceDeskGetOrganisationsTool",
    "ServiceDeskAddOrganisationTool",
    "ServiceDeskRemoveOrganisationTool",
]
