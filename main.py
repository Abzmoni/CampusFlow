"""CampusFlow Pro — Command-Line Campus Helpdesk Application."""

import sys

from campusflow.audited_workflow import (
    assign_with_history,
    reopen_with_history,
    update_status_with_history,
)
from campusflow.cli_actions import confirm_duplicate_warning, create_with_history
from campusflow.history import get_ticket_history
from campusflow.knowledge_lab import run_knowledge_lab
from campusflow.reports import generate_enhanced_report
from campusflow.sla import escalate_overdue
from campusflow.sla_queue import get_sla_attention_queue
from campusflow.storage import load_data, save_data
from campusflow.workflow import find_ticket, get_work_queue

STORAGE_PATH = "data/tickets.json"


# --------------------------------------------------
# DISPLAY HEADERS
# --------------------------------------------------

def print_header(title):
    print("\n" + "=" * 60)
    print(f"  {title}")
    print("=" * 60)


# --------------------------------------------------
# PERSISTENCE HELPER
# --------------------------------------------------

def persist_state(tickets, events, filepath=STORAGE_PATH):
    """Save tickets and events atomically under Version-2 schema."""
    save_data(
        {"schema_version": 2, "tickets": tickets, "events": events},
        filepath,
    )


# --------------------------------------------------
# FORMAT TICKET INFORMATION
# --------------------------------------------------

def format_ticket_row(t):
    assigned = t.get("assigned_to") or "Unassigned"
    return (
        f"[{t.get('id')}] {t.get('title'):<30} | "
        f"{t.get('category'):<8} | "
        f"Priority: {t.get('priority'):<8} | "
        f"Status: {t.get('status'):<11} | "
        f"Assigned: {assigned}"
    )


# --------------------------------------------------
# CREATE TICKET (WITH DUPLICATE GUARD & AUDIT)
# --------------------------------------------------

def handle_create(tickets, events):
    print_header("CREATE A NEW TICKET")

    title = input("Enter ticket title: ").strip()

    print("Categories: Network, Hardware, Software, Other")
    category = input("Enter category: ").strip()

    print("Urgency levels: low, medium, high")
    urgency = input("Enter urgency: ").strip()

    affected_raw = input("Enter number of affected users: ").strip()

    try:
        affected_users = int(affected_raw)
    except ValueError:
        print("\n[Error] Affected users must be a valid positive integer.")
        return

    actor = input("Enter operator/actor label (default: operator): ").strip() or "operator"

    try:
        ticket = create_with_history(
            tickets,
            events,
            title,
            category,
            urgency,
            affected_users,
            actor=actor,
            confirm_duplicates=confirm_duplicate_warning,
        )

        if ticket is None:
            print("\n[Notice] Ticket creation was cancelled.")
            return

        persist_state(tickets, events)

        print(f"\n[Success] Ticket {ticket['id']} created successfully!")
        print(f"  Priority calculated: {ticket['priority'].upper()}")
        print(f"  Status: {ticket['status']}")
        if "due_at" in ticket:
            print(f"  Due At: {ticket['due_at']}")

    except ValueError as err:
        print(f"\n[Error] Failed to create ticket: {err}")


# --------------------------------------------------
# LIST AND VIEW TICKETS
# --------------------------------------------------

def handle_list_view(tickets):
    print_header("ALL TICKETS")

    if not tickets:
        print("No tickets found in the system.")
        return

    for ticket in tickets:
        print(format_ticket_row(ticket))

    choice = input("\nEnter Ticket ID to view details (or press Enter to return): ").strip()

    if choice:
        try:
            ticket = find_ticket(tickets, choice)

            print("\n" + "-" * 40)
            print(f"Ticket ID:        {ticket.get('id')}")
            print(f"Title:            {ticket.get('title')}")
            print(f"Category:         {ticket.get('category')}")
            print(f"Urgency:          {ticket.get('urgency')}")
            print(f"Affected Users:   {ticket.get('affected_users')}")
            print(f"Priority:         {ticket.get('priority').upper()}")
            print(f"Status:           {ticket.get('status')}")
            print(f"Assigned To:      {ticket.get('assigned_to') or 'Unassigned'}")
            if "created_at" in ticket:
                print(f"Created At:       {ticket.get('created_at')}")
            if "due_at" in ticket:
                print(f"Due At:           {ticket.get('due_at')}")
            if "escalation_cycle" in ticket:
                print(f"Escalated (SLA):  {'Yes' if ticket.get('escalation_cycle') == 1 else 'No'}")
            print("-" * 40)

        except ValueError as err:
            print(f"\n[Error] {err}")


# --------------------------------------------------
# ASSIGN TICKET (AUDITED)
# --------------------------------------------------

def handle_assign(tickets, events):
    print_header("ASSIGN TICKET")

    ticket_id = input("Enter Ticket ID to assign (e.g. T001): ").strip()
    staff_name = input("Enter staff member name: ").strip()
    actor = input("Enter operator/actor label (default: operator): ").strip() or "operator"

    try:
        updated = assign_with_history(
            tickets,
            events,
            ticket_id,
            staff_name,
            actor=actor,
        )

        persist_state(tickets, events)

        print(
            f"\n[Success] Ticket {updated['id']} "
            f"assigned to '{updated['assigned_to']}'."
        )

    except ValueError as err:
        print(f"\n[Error] Assignment failed: {err}")


# --------------------------------------------------
# UPDATE TICKET WORKFLOW (AUDITED)
# --------------------------------------------------

def handle_workflow(tickets, events):
    print_header("UPDATE TICKET STATUS / WORKFLOW")

    print("1. Progress / Update Status (open -> in_progress -> resolved)")
    print("2. Reopen a Resolved Ticket (resolved -> open)")

    choice = input("Select an option (1-2): ").strip()

    if choice == "1":
        ticket_id = input("Enter Ticket ID: ").strip()
        print("Target status options: open, in_progress, resolved")
        new_status = input("Enter new status: ").strip()
        actor = input("Enter operator/actor label (default: operator): ").strip() or "operator"

        try:
            updated = update_status_with_history(
                tickets,
                events,
                ticket_id,
                new_status,
                actor=actor,
            )

            persist_state(tickets, events)

            print(
                f"\n[Success] Ticket {updated['id']} "
                f"status updated to '{updated['status']}'."
            )

        except ValueError as err:
            print(f"\n[Error] Transition rejected: {err}")

    elif choice == "2":
        ticket_id = input("Enter Ticket ID to reopen: ").strip()
        actor = input("Enter operator/actor label (default: operator): ").strip() or "operator"

        try:
            updated = reopen_with_history(
                tickets,
                events,
                ticket_id,
                actor=actor,
            )

            persist_state(tickets, events)

            print(
                f"\n[Success] Ticket {updated['id']} "
                "reopened and set back to 'open' with a fresh SLA cycle!"
            )
            if "due_at" in updated:
                print(f"  New SLA Due At: {updated['due_at']}")

        except ValueError as err:
            print(f"\n[Error] Reopen failed: {err}")

    else:
        print("\n[Error] Invalid choice.")


# --------------------------------------------------
# VIEW PRIORITIZED WORK QUEUE (ORIGINAL)
# --------------------------------------------------

def handle_work_queue(tickets):
    print_header("PRIORITIZED WORK QUEUE (OPEN TICKETS)")

    queue = get_work_queue(tickets)

    if not queue:
        print("Work queue is empty. No unresolved tickets.")
        return

    print("Open & In-Progress Tickets (Ordered: Critical -> High -> Medium -> Low, ID tie-breaker):\n")

    for pos, ticket in enumerate(queue, start=1):
        assigned = ticket.get("assigned_to") or "Unassigned"
        print(
            f"#{pos:<2} [{ticket.get('id')}] "
            f"Priority: {ticket.get('priority').upper():<8} | "
            f"Status: {ticket.get('status'):<11} | "
            f"Users: {ticket.get('affected_users'):<3} | "
            f"{ticket.get('title')} ({assigned})"
        )


# --------------------------------------------------
# VIEW SLA ATTENTION QUEUE (PRO)
# --------------------------------------------------

def handle_sla_queue(tickets):
    print_header("SLA ATTENTION QUEUE (TIME-CRITICAL)")

    try:
        attention = get_sla_attention_queue(tickets)
    except ValueError as err:
        print(f"\n[Error] Could not load SLA queue: {err}")
        return

    if not attention:
        print("SLA queue is empty. No unresolved tickets.")
        return

    print("Unresolved Tickets (Overdue first, then earliest deadline, then ID):\n")

    for pos, ticket in enumerate(attention, start=1):
        assigned = ticket.get("assigned_to") or "Unassigned"
        due = ticket.get("due_at") or "No deadline"
        overdue_badge = "[OVERDUE]" if ticket.get("overdue") or (
            ticket.get("escalation_cycle", 0) == 1
        ) else "        "

        print(
            f"#{pos:<2} {overdue_badge} [{ticket.get('id')}] "
            f"Due: {due:<25} | "
            f"Priority: {ticket.get('priority').upper():<8} | "
            f"Status: {ticket.get('status'):<11} | "
            f"{ticket.get('title')} ({assigned})"
        )


# --------------------------------------------------
# CHECK AND ESCALATE OVERDUE TICKETS (PRO)
# --------------------------------------------------

def handle_escalate(tickets, events):
    print_header("CHECK AND ESCALATE OVERDUE TICKETS")

    actor = input("Enter operator label (default: system): ").strip() or "system"

    try:
        result = escalate_overdue(tickets, events, actor=actor)

        if result["newly_escalated"] > 0:
            persist_state(tickets, events)

        print("\nSLA Escalation Results:")
        print(f"  - Newly escalated tickets:    {result['newly_escalated']}")
        print(f"  - Already escalated tickets:  {result['already_escalated']}")

        if result["newly_escalated"] == 0 and result["already_escalated"] == 0:
            print("  - No tickets currently breach their SLA deadlines.")

    except ValueError as err:
        print(f"\n[Error] Escalation failed: {err}")


# --------------------------------------------------
# VIEW TICKET AUDIT HISTORY (PRO)
# --------------------------------------------------

def handle_history(events):
    print_header("VIEW TICKET AUDIT HISTORY")

    ticket_id = input("Enter Ticket ID to view audit history (e.g. T001): ").strip()
    if not ticket_id:
        print("\n[Error] Ticket ID cannot be empty.")
        return

    try:
        history = get_ticket_history(events, ticket_id)
        if not history:
            print(f"\nNo audit history recorded for Ticket '{ticket_id.upper()}'.")
            return

        print(f"\nAudit History for {ticket_id.upper()} ({len(history)} events):\n")
        print(f"{'Event ID':<10} {'Timestamp':<28} {'Event':<10} {'Actor':<12} {'Transition':<24} {'Details'}")
        print("-" * 100)

        for event in history:
            b_stat = event.get("before_status") or "-"
            a_stat = event.get("after_status") or "-"
            trans = f"{b_stat} -> {a_stat}"
            print(
                f"{event.get('event_id'):<10} "
                f"{event.get('timestamp'):<28} "
                f"{event.get('event_type'):<10} "
                f"{event.get('actor'):<12} "
                f"{trans:<24} "
                f"{event.get('details')}"
            )

    except ValueError as err:
        print(f"\n[Error] Could not retrieve history: {err}")


# --------------------------------------------------
# VIEW ENHANCED SUMMARY REPORTS (PRO)
# --------------------------------------------------

def handle_reports(tickets):
    print_header("CAMPUSFLOW SUMMARY REPORT (ENHANCED)")

    report = generate_enhanced_report(tickets)

    print(f"Total Tickets: {report['total']}\n")

    print("Breakdown by Status:")
    for status, count in report["by_status"].items():
        print(f"  - {status.replace('_', ' ').title():<15}: {count}")

    print("\nBreakdown by Priority:")
    for priority, count in report["by_priority"].items():
        print(f"  - {priority.title():<15}: {count}")

    print("\nSLA Performance Metrics:")
    print(f"  - Overdue Unresolved Tickets:         {report.get('overdue', 0)}")
    print(f"  - Escalated in Current SLA Cycle:     {report.get('escalated_this_cycle', 0)}")


# --------------------------------------------------
# ENGINEERING KNOWLEDGE LAB
# --------------------------------------------------

def handle_knowledge_lab():
    print_header("ENGINEERING KNOWLEDGE LAB")
    print("Welcome to the CampusFlow Pro Engineering Knowledge Lab.")
    print("You will answer 10 multiple-choice engineering questions.")
    print("You must also provide explanations for at least three answers.")
    print("Your quiz results will be saved separately from helpdesk tickets.")
    print("\nStarting quiz...\n")
    run_knowledge_lab()


# --------------------------------------------------
# MAIN APPLICATION
# --------------------------------------------------

def main():
    # Load Version 2 data structure
    try:
        data = load_data(STORAGE_PATH)
        tickets = data["tickets"]
        events = data["events"]
    except ValueError as err:
        print(f"\n[FATAL ERROR] {err}")
        print("Please resolve the file conflict or inspect data/tickets.json before restarting.")
        sys.exit(1)

    while True:
        print("\n" + "=" * 60)
        print("              CAMPUSFLOW PRO HELP DESK MANAGER")
        print("=" * 60)
        print(" 1. Create Ticket (with Duplicate Warning)")
        print(" 2. List / View Tickets")
        print(" 3. Assign Ticket to Staff")
        print(" 4. Update Ticket Workflow Status (Progress / Reopen)")
        print(" 5. View Prioritized Work Queue (Original)")
        print(" 6. View SLA Attention Queue (Pro)")
        print(" 7. Check and Escalate Overdue Tickets (Pro)")
        print(" 8. View Ticket Audit History (Pro)")
        print(" 9. View Summary Reports (Enhanced SLA Analytics)")
        print("10. Engineering Knowledge Lab")
        print("11. Exit")
        print("=" * 60)

        choice = input("Enter your choice (1-11): ").strip()

        if choice == "1":
            handle_create(tickets, events)
        elif choice == "2":
            handle_list_view(tickets)
        elif choice == "3":
            handle_assign(tickets, events)
        elif choice == "4":
            handle_workflow(tickets, events)
        elif choice == "5":
            handle_work_queue(tickets)
        elif choice == "6":
            handle_sla_queue(tickets)
        elif choice == "7":
            handle_escalate(tickets, events)
        elif choice == "8":
            handle_history(events)
        elif choice == "9":
            handle_reports(tickets)
        elif choice == "10":
            handle_knowledge_lab()
        elif choice == "11":
            persist_state(tickets, events)
            print("\nExiting CampusFlow Pro. Tickets and audit history safely saved. Goodbye!")
            break
        else:
            print("\n[Error] Invalid choice. Please enter a number between 1 and 11.")


if __name__ == "__main__":
    main()