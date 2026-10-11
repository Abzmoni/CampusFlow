"""Engineer B's reporting and metrics engine for CampusFlow."""


def generate_report(tickets):
    """Generate summary statistics for the ticket collection.

    Returns total tickets and breakdowns by status and priority.
    Correctly handles an empty collection with zero counts.
    """
    if not isinstance(tickets, list):
        raise ValueError("Tickets must be a list.")

    report = {
        "total": len(tickets),
        "by_status": {
            "open": 0,
            "in_progress": 0,
            "resolved": 0,
        },
        "by_priority": {
            "critical": 0,
            "high": 0,
            "medium": 0,
            "low": 0,
        },
    }

    for ticket in tickets:
        if not isinstance(ticket, dict):
            continue
        status = str(ticket.get("status", "")).lower()
        if status in report["by_status"]:
            report["by_status"][status] += 1

        priority = str(ticket.get("priority", "")).lower()
        if priority in report["by_priority"]:
            report["by_priority"][priority] += 1

    return report
