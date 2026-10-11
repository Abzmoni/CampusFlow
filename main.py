"""CampusFlow — Command-Line Campus Helpdesk Application."""

import sys
from campusflow.reports import generate_report
from campusflow.storage import load_tickets, save_tickets
from campusflow.tickets import create_ticket
from campusflow.workflow import (
    assign_ticket,
    find_ticket,
    get_work_queue,
    reopen_ticket,
    update_status,
)

STORAGE_PATH = "data/tickets.json"


def print_header(title):
    print("\n" + "=" * 60)
    print(f"  {title}")
    print("=" * 60)


def format_ticket_row(t):
    assigned = t.get("assigned_to") or "Unassigned"
    return (
        f"[{t.get('id')}] {t.get('title'):<30} | "
        f"{t.get('category'):<8} | "
        f"Priority: {t.get('priority'):<8} | "
        f"Status: {t.get('status'):<11} | "
        f"Assigned: {assigned}"
    )


def handle_create(tickets):
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

    try:
        ticket = create_ticket(tickets, title, category, urgency, affected_users)
        save_tickets(tickets, STORAGE_PATH)
        print(f"\n[Success] Ticket {ticket['id']} created successfully!")
        print(f"  Priority calculated: {ticket['priority'].upper()}")
        print(f"  Status: {ticket['status']}")
    except ValueError as err:
        print(f"\n[Error] Failed to create ticket: {err}")


def handle_list_view(tickets):
    print_header("ALL TICKETS")
    if not tickets:
        print("No tickets found in the system.")
        return

    for t in tickets:
        print(format_ticket_row(t))

    choice = input("\nEnter Ticket ID to view details (or press Enter to return): ").strip()
    if choice:
        try:
            t = find_ticket(tickets, choice)
            print("\n" + "-" * 40)
            print(f"Ticket ID:      {t.get('id')}")
            print(f"Title:          {t.get('title')}")
            print(f"Category:       {t.get('category')}")
            print(f"Urgency:        {t.get('urgency')}")
            print(f"Affected Users: {t.get('affected_users')}")
            print(f"Priority:       {t.get('priority').upper()}")
            print(f"Status:         {t.get('status')}")
            print(f"Assigned To:    {t.get('assigned_to') or 'Unassigned'}")
            print("-" * 40)
        except ValueError as err:
            print(f"\n[Error] {err}")


def handle_assign(tickets):
    print_header("ASSIGN TICKET")
    ticket_id = input("Enter Ticket ID to assign (e.g. T001): ").strip()
    staff_name = input("Enter staff member name: ").strip()

    try:
        updated = assign_ticket(tickets, ticket_id, staff_name)
        save_tickets(tickets, STORAGE_PATH)
        print(f"\n[Success] Ticket {updated['id']} assigned to '{updated['assigned_to']}'.")
    except ValueError as err:
        print(f"\n[Error] Assignment failed: {err}")


def handle_workflow(tickets):
    print_header("UPDATE TICKET STATUS / WORKFLOW")
    print("1. Progress / Update Status (open -> in_progress -> resolved)")
    print("2. Reopen a Resolved Ticket (resolved -> open)")
    choice = input("Select an option (1-2): ").strip()

    if choice == "1":
        ticket_id = input("Enter Ticket ID: ").strip()
        print("Target status options: open, in_progress, resolved")
        new_status = input("Enter new status: ").strip()
        try:
            updated = update_status(tickets, ticket_id, new_status)
            save_tickets(tickets, STORAGE_PATH)
            print(f"\n[Success] Ticket {updated['id']} status updated to '{updated['status']}'.")
        except ValueError as err:
            print(f"\n[Error] Transition rejected: {err}")
    elif choice == "2":
        ticket_id = input("Enter Ticket ID to reopen: ").strip()
        try:
            updated = reopen_ticket(tickets, ticket_id)
            save_tickets(tickets, STORAGE_PATH)
            print(f"\n[Success] Ticket {updated['id']} reopened and set back to 'open'.")
        except ValueError as err:
            print(f"\n[Error] Reopen failed: {err}")
    else:
        print("\n[Error] Invalid choice.")


def handle_work_queue(tickets):
    print_header("PRIORITIZED WORK QUEUE")
    queue = get_work_queue(tickets)
    if not queue:
        print("Work queue is empty. No unresolved tickets.")
        return

    print("Open & In-Progress Tickets (Ordered: Critical -> High -> Medium -> Low, ID tie-breaker):\n")
    for pos, t in enumerate(queue, start=1):
        assigned = t.get("assigned_to") or "Unassigned"
        print(
            f"#{pos:<2} [{t.get('id')}] Priority: {t.get('priority').upper():<8} | "
            f"Status: {t.get('status'):<11} | "
            f"Users: {t.get('affected_users'):<3} | "
            f"{t.get('title')} ({assigned})"
        )


def handle_reports(tickets):
    print_header("HELPDESK SUMMARY REPORT")
    report = generate_report(tickets)

    print(f"Total Tickets: {report['total']}\n")
    print("Breakdown by Status:")
    for status, count in report["by_status"].items():
        print(f"  - {status.replace('_', ' ').title():<15}: {count}")

    print("\nBreakdown by Priority:")
    for priority, count in report["by_priority"].items():
        print(f"  - {priority.title():<15}: {count}")


def main():
    try:
        tickets = load_tickets(STORAGE_PATH)
    except ValueError as err:
        print(f"\n[FATAL ERROR] {err}")
        print("Please resolve the file conflict or inspect data/tickets.json before restarting.")
        sys.exit(1)

    while True:
        print("\n" + "=" * 60)
        print("              CAMPUSFLOW HELP DESK MANAGER")
        print("=" * 60)
        print("1. Create Ticket")
        print("2. List / View Tickets")
        print("3. Assign Ticket to Staff")
        print("4. Update Ticket Workflow Status")
        print("5. View Prioritized Work Queue")
        print("6. View Summary Reports")
        print("7. Exit")
        print("=" * 60)

        choice = input("Enter your choice (1-7): ").strip()

        if choice == "1":
            handle_create(tickets)
        elif choice == "2":
            handle_list_view(tickets)
        elif choice == "3":
            handle_assign(tickets)
        elif choice == "4":
            handle_workflow(tickets)
        elif choice == "5":
            handle_work_queue(tickets)
        elif choice == "6":
            handle_reports(tickets)
        elif choice == "7":
            save_tickets(tickets, STORAGE_PATH)
            print("\nExiting CampusFlow. Tickets safely saved to storage. Goodbye!")
            break
        else:
            print("\n[Error] Invalid choice. Please enter a number between 1 and 7.")


if __name__ == "__main__":
    main()
