# Normalize a ticket title
def normalize_title(title):
    return " ".join(title.casefold().split())


# Find possible duplicate tickets
def detect_duplicates(tickets, category, title):

    duplicates = []

    # Normalize the new ticket details
    new_title = normalize_title(title)
    new_category = category.strip().casefold()

    # Check each existing ticket
    for ticket in tickets:

        # Ignore resolved tickets
        if ticket["status"] == "resolved":
            continue

        # Normalize existing ticket details
        existing_title = normalize_title(ticket["title"])
        existing_category = ticket["category"].strip().casefold()

        # Check whether both title and category match
        if existing_title == new_title and existing_category == new_category:
            duplicates.append(ticket["id"])

    return duplicates