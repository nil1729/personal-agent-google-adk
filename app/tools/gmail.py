import base64
from datetime import datetime, timedelta
from typing import Dict, Any, Optional

from googleapiclient.errors import HttpError

from app.clients.gmail import get_gmail_service


def _parse_email_address(address_str: str) -> Dict[str, str]:
    """Parse email address string into dict."""
    if not address_str:
        return {"email": "", "name": ""}

    if "<" in address_str and ">" in address_str:
        name = address_str.split("<")[0].strip().strip('"')
        email_addr = address_str.split("<")[1].split(">")[0].strip()
        return {"email": email_addr, "name": name}
    else:
        return {"email": address_str.strip(), "name": ""}


def _extract_email_data(message_data: Dict) -> Dict[str, Any]:
    """Extract email data into a simple dict."""
    headers_dict = {}
    for header in message_data["payload"].get("headers", []):
        headers_dict[header["name"].lower()] = header["value"]

    # Extract body content
    text_content = ""
    html_content = ""

    def extract_body(payload):
        nonlocal text_content, html_content

        if payload.get("mimeType") == "text/plain" and payload.get("body", {}).get(
            "data"
        ):
            try:
                text_content = base64.urlsafe_b64decode(payload["body"]["data"]).decode(
                    "utf-8"
                )
            except Exception:
                pass
        elif payload.get("mimeType") == "text/html" and payload.get("body", {}).get(
            "data"
        ):
            try:
                html_content = base64.urlsafe_b64decode(payload["body"]["data"]).decode(
                    "utf-8"
                )
            except Exception:
                pass
        elif payload.get("parts"):
            for part in payload["parts"]:
                extract_body(part)

    extract_body(message_data["payload"])

    # Extract attachments
    attachments = []

    def extract_attachments(payload):
        if payload.get("filename") and payload.get("body", {}).get("attachmentId"):
            attachments.append(
                {
                    "filename": payload["filename"],
                    "mime_type": payload.get("mimeType", ""),
                    "size": payload.get("body", {}).get("size", 0),
                    "attachment_id": payload["body"]["attachmentId"],
                }
            )
        elif payload.get("parts"):
            for part in payload["parts"]:
                extract_attachments(part)

    extract_attachments(message_data["payload"])

    return {
        "id": message_data["id"],
        "thread_id": message_data["threadId"],
        "subject": headers_dict.get("subject", ""),
        "from": _parse_email_address(headers_dict.get("from", "")),
        "to": headers_dict.get("to", ""),
        "date": datetime.fromtimestamp(
            int(message_data["internalDate"]) / 1000
        ).isoformat(),
        "snippet": message_data.get("snippet", ""),
        "body_text": text_content,
        "body_html": html_content,
        "labels": message_data.get("labelIds", []),
        "attachments": attachments,
        "size": message_data.get("sizeEstimate", 0),
    }


# =============================================================================
# DATE/TIME UTILITY FUNCTION
# =============================================================================


def get_current_datetime() -> dict:
    """
    Get current date and time information.

    Returns:
        Dict with status and current date/time information
    """
    print("--- Tool: get_current_datetime called ---")

    try:
        now = datetime.now()
        today = now.date()
        yesterday = today - timedelta(days=1)
        tomorrow = today + timedelta(days=1)

        return {
            "status": "success",
            "current_datetime": {
                "timestamp": now.isoformat(),
                "date": today.isoformat(),
                "time": now.time().isoformat(),
                "year": now.year,
                "month": now.month,
                "day": now.day,
                "hour": now.hour,
                "minute": now.minute,
                "second": now.second,
                "weekday": now.strftime("%A"),
                "month_name": now.strftime("%B"),
                "formatted_date": now.strftime("%Y-%m-%d"),
                "formatted_datetime": now.strftime("%Y-%m-%d %H:%M:%S"),
                "human_readable": now.strftime("%A, %B %d, %Y at %I:%M %p"),
                "yesterday_date": yesterday.isoformat(),
                "tomorrow_date": tomorrow.isoformat(),
                "gmail_search_format": {
                    "today": today.strftime("%Y/%m/%d"),
                    "yesterday": yesterday.strftime("%Y/%m/%d"),
                    "tomorrow": tomorrow.strftime("%Y/%m/%d"),
                },
            },
            "message": f"Current time: {now.strftime('%Y-%m-%d %H:%M:%S')}",
        }

    except Exception as e:
        return {
            "status": "error",
            "error_message": f"Failed to get current datetime: {str(e)}",
        }


def get_emails_by_date_range(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    max_results: int = 20,
) -> dict:
    """
    Get emails from a specific date range.

    Args:
        start_date: Start date in YYYY-MM-DD format (default: today)
        end_date: End date in YYYY-MM-DD format (default: tomorrow for inclusive today search)
        max_results: Maximum number of results (default: 20, max: 50)

    Returns:
        Dict with status and list of emails
    """
    print(
        f"--- Tool: get_emails_by_date_range called with start_date: {start_date}, end_date: {end_date} ---"
    )

    try:
        # Get current date info if dates not provided
        if not start_date or not end_date:
            date_info = get_current_datetime()
            if date_info["status"] != "success":
                return date_info

        # Set default dates
        if not start_date:
            start_date = date_info["current_datetime"]["date"]
        if not end_date:
            # For inclusive search of a single day, end date should be the next day
            if start_date == date_info["current_datetime"]["date"]:
                end_date = date_info["current_datetime"]["tomorrow_date"]
            else:
                # Parse start_date and add one day
                start_dt = datetime.strptime(start_date, "%Y-%m-%d")
                end_dt = start_dt + timedelta(days=1)
                end_date = end_dt.strftime("%Y-%m-%d")

        # Convert to Gmail search format (YYYY/MM/DD)
        gmail_start = start_date.replace("-", "/")
        gmail_end = end_date.replace("-", "/")

        # Construct query
        query = f"after:{gmail_start} before:{gmail_end}"

        return search_emails(query, max_results)

    except Exception as e:
        return {
            "status": "error",
            "error_message": f"Failed to get emails by date range: {str(e)}",
        }


def get_today_emails(max_results: int = 20) -> dict:
    """
    Get today's emails using the current date.

    Args:
        max_results: Maximum number of results (default: 20, max: 50)

    Returns:
        Dict with status and list of today's emails
    """
    print("--- Tool: get_today_emails called ---")

    try:
        date_info = get_current_datetime()
        if date_info["status"] != "success":
            return date_info

        today_format = date_info["current_datetime"]["gmail_search_format"]["today"]
        tomorrow_format = date_info["current_datetime"]["gmail_search_format"][
            "tomorrow"
        ]

        query = f"after:{today_format} before:{tomorrow_format}"
        result = search_emails(query, max_results)

        if result["status"] == "success":
            result["message"] = (
                f"Found {result['count']} emails from today ({date_info['current_datetime']['formatted_date']})"
            )

        return result

    except Exception as e:
        return {
            "status": "error",
            "error_message": f"Failed to get today's emails: {str(e)}",
        }


# =============================================================================
# LABEL MANAGEMENT FUNCTIONS (READ-ONLY)
# =============================================================================


def list_labels() -> dict:
    """
    List all labels in the user's mailbox.

    Returns:
        Dict with status and list of labels with their details
    """
    print("--- Tool: list_labels called ---")

    try:
        service = get_gmail_service()
        results = service.users().labels().list(userId="me").execute()
        labels = results.get("labels", [])

        # Format labels with useful information
        formatted_labels = []
        for label in labels:
            formatted_labels.append(
                {
                    "id": label["id"],
                    "name": label["name"],
                    "type": label["type"],
                    "messages_total": label.get("messagesTotal", 0),
                    "messages_unread": label.get("messagesUnread", 0),
                    "threads_total": label.get("threadsTotal", 0),
                    "threads_unread": label.get("threadsUnread", 0),
                    "label_list_visibility": label.get("labelListVisibility", ""),
                    "message_list_visibility": label.get("messageListVisibility", ""),
                }
            )

        return {
            "status": "success",
            "labels": formatted_labels,
            "count": len(formatted_labels),
            "message": f"Found {len(formatted_labels)} labels",
        }

    except HttpError as e:
        return {"status": "error", "error_message": f"Failed to list labels: {str(e)}"}
    except Exception as e:
        return {"status": "error", "error_message": f"Unexpected error: {str(e)}"}


def get_label_details(label_id: str) -> dict:
    """
    Get detailed information about a specific label.

    Args:
        label_id: The label ID to get details for

    Returns:
        Dict with status and label details
    """
    print(f"--- Tool: get_label_details called for {label_id} ---")

    try:
        service = get_gmail_service()
        label = service.users().labels().get(userId="me", id=label_id).execute()

        return {
            "status": "success",
            "label": {
                "id": label["id"],
                "name": label["name"],
                "type": label["type"],
                "messages_total": label.get("messagesTotal", 0),
                "messages_unread": label.get("messagesUnread", 0),
                "threads_total": label.get("threadsTotal", 0),
                "threads_unread": label.get("threadsUnread", 0),
                "label_list_visibility": label.get("labelListVisibility", ""),
                "message_list_visibility": label.get("messageListVisibility", ""),
                "color": label.get("color", {}),
            },
        }

    except HttpError as e:
        return {"status": "error", "error_message": f"Failed to get label: {str(e)}"}
    except Exception as e:
        return {"status": "error", "error_message": f"Unexpected error: {str(e)}"}


def find_label_by_name(label_name: str) -> dict:
    """
    Find a label by its name (case-insensitive).

    Args:
        label_name: Name of the label to find

    Returns:
        Dict with status and label details if found
    """
    print(f"--- Tool: find_label_by_name called for '{label_name}' ---")

    try:
        labels_result = list_labels()
        if labels_result["status"] != "success":
            return labels_result

        label_name_lower = label_name.lower()
        for label in labels_result["labels"]:
            if label["name"].lower() == label_name_lower:
                return {
                    "status": "success",
                    "label": label,
                    "message": f"Found label '{label['name']}'",
                }

        return {
            "status": "not_found",
            "message": f"No label found with name '{label_name}'",
        }

    except Exception as e:
        return {"status": "error", "error_message": f"Unexpected error: {str(e)}"}


def get_system_labels() -> dict:
    """
    Get all system labels (INBOX, SENT, DRAFT, etc.).

    Returns:
        Dict with status and list of system labels
    """
    print("--- Tool: get_system_labels called ---")

    try:
        labels_result = list_labels()
        if labels_result["status"] != "success":
            return labels_result

        system_labels = [
            label for label in labels_result["labels"] if label["type"] == "system"
        ]

        return {
            "status": "success",
            "labels": system_labels,
            "count": len(system_labels),
            "message": f"Found {len(system_labels)} system labels",
        }

    except Exception as e:
        return {"status": "error", "error_message": f"Unexpected error: {str(e)}"}


def get_user_labels() -> dict:
    """
    Get all user-created labels.

    Returns:
        Dict with status and list of user labels
    """
    print("--- Tool: get_user_labels called ---")

    try:
        labels_result = list_labels()
        if labels_result["status"] != "success":
            return labels_result

        user_labels = [
            label for label in labels_result["labels"] if label["type"] == "user"
        ]

        return {
            "status": "success",
            "labels": user_labels,
            "count": len(user_labels),
            "message": f"Found {len(user_labels)} user-created labels",
        }

    except Exception as e:
        return {"status": "error", "error_message": f"Unexpected error: {str(e)}"}


def get_labels_with_unread_count() -> dict:
    """
    Get all labels that have unread messages.

    Returns:
        Dict with status and list of labels with unread counts
    """
    print("--- Tool: get_labels_with_unread_count called ---")

    try:
        labels_result = list_labels()
        if labels_result["status"] != "success":
            return labels_result

        labels_with_unread = [
            label for label in labels_result["labels"] if label["messages_unread"] > 0
        ]

        # Sort by unread count (descending)
        labels_with_unread.sort(key=lambda x: x["messages_unread"], reverse=True)

        return {
            "status": "success",
            "labels": labels_with_unread,
            "count": len(labels_with_unread),
            "message": f"Found {len(labels_with_unread)} labels with unread messages",
        }

    except Exception as e:
        return {"status": "error", "error_message": f"Unexpected error: {str(e)}"}


def get_label_statistics() -> dict:
    """
    Get statistics about all labels (message counts, unread counts, etc.).

    Returns:
        Dict with status and label statistics
    """
    print("--- Tool: get_label_statistics called ---")

    try:
        labels_result = list_labels()
        if labels_result["status"] != "success":
            return labels_result

        total_messages = sum(
            label["messages_total"] for label in labels_result["labels"]
        )
        total_unread = sum(
            label["messages_unread"] for label in labels_result["labels"]
        )

        system_labels_count = len(
            [l for l in labels_result["labels"] if l["type"] == "system"]
        )
        user_labels_count = len(
            [l for l in labels_result["labels"] if l["type"] == "user"]
        )

        # Top labels by message count
        top_labels = sorted(
            labels_result["labels"], key=lambda x: x["messages_total"], reverse=True
        )[:10]

        # Labels with most unread
        unread_labels = sorted(
            [l for l in labels_result["labels"] if l["messages_unread"] > 0],
            key=lambda x: x["messages_unread"],
            reverse=True,
        )[:10]

        return {
            "status": "success",
            "statistics": {
                "total_labels": len(labels_result["labels"]),
                "system_labels": system_labels_count,
                "user_labels": user_labels_count,
                "total_messages": total_messages,
                "total_unread": total_unread,
                "top_labels_by_count": top_labels,
                "labels_with_unread": unread_labels,
            },
        }

    except Exception as e:
        return {"status": "error", "error_message": f"Unexpected error: {str(e)}"}


# =============================================================================
# ENHANCED EMAIL FUNCTIONS WITH LABEL SUPPORT
# =============================================================================


def get_emails_by_label(label_name: str, max_results: int = 20) -> dict:
    """
    Get emails from a specific label by name.

    Args:
        label_name: Name of the label (e.g., "INBOX", "SENT", "Important", etc.)
        max_results: Maximum number of results (default: 20, max: 50)

    Returns:
        Dict with status and list of emails
    """
    print(f"--- Tool: get_emails_by_label called for '{label_name}' ---")

    try:
        # First, find the label to get its ID
        label_result = find_label_by_name(label_name)
        if label_result["status"] == "not_found":
            # Try as label ID directly
            return list_messages(max_results, label_name)
        elif label_result["status"] != "success":
            return label_result

        label_id = label_result["label"]["id"]
        return list_messages(max_results, label_id)

    except Exception as e:
        return {"status": "error", "error_message": f"Unexpected error: {str(e)}"}


def search_emails_with_labels(query: str, max_results: int = 10) -> dict:
    """
    Enhanced search that includes label information in results.

    Args:
        query: Gmail search query
        max_results: Maximum number of results (default: 10, max: 50)

    Returns:
        Dict with status, emails, and label mapping
    """
    print(f"--- Tool: search_emails_with_labels called with query: {query} ---")

    try:
        # Get all labels for mapping
        labels_result = list_labels()
        label_map = {}
        if labels_result["status"] == "success":
            label_map = {
                label["id"]: label["name"] for label in labels_result["labels"]
            }

        # Perform the search
        search_result = search_emails(query, max_results)
        if search_result["status"] != "success":
            return search_result

        # Enhance emails with label names
        for email in search_result["emails"]:
            email["label_names"] = [
                label_map.get(label_id, label_id) for label_id in email["labels"]
            ]

        return {
            "status": "success",
            "emails": search_result["emails"],
            "count": search_result["count"],
            "label_mapping": label_map,
            "message": search_result["message"],
        }

    except Exception as e:
        return {"status": "error", "error_message": f"Unexpected error: {str(e)}"}


# =============================================================================
# ORIGINAL EMAIL FUNCTIONS
# =============================================================================


def get_email_by_id(message_id: str) -> dict:
    """
    Get a specific email by its ID.

    Args:
        message_id: Gmail message ID

    Returns:
        Dict with status and email data
    """
    print(f"--- Tool: get_email_by_id called for {message_id} ---")

    try:
        service = get_gmail_service()
        message = (
            service.users()
            .messages()
            .get(userId="me", id=message_id, format="full")
            .execute()
        )

        email_data = _extract_email_data(message)

        return {"status": "success", "email": email_data}

    except HttpError as e:
        return {"status": "error", "error_message": f"Failed to get email: {str(e)}"}
    except Exception as e:
        return {"status": "error", "error_message": f"Unexpected error: {str(e)}"}


def search_emails(query: str, max_results: int = 10) -> dict:
    """
    Search emails using Gmail search syntax.

    Args:
        query: Gmail search query (e.g., "from:example@gmail.com", "subject:meeting")
        max_results: Maximum number of results (default: 10, max: 50)

    Returns:
        Dict with status and list of emails

    Examples:
        search_emails("from:boss@company.com")
        search_emails("subject:meeting")
        search_emails("has:attachment")
    """
    print(f"--- Tool: search_emails called with query: {query} ---")

    try:
        service = get_gmail_service()

        # Limit max_results to prevent overwhelming responses
        max_results = min(max_results, 50)

        # Get message IDs
        results = (
            service.users()
            .messages()
            .list(userId="me", q=query, maxResults=max_results)
            .execute()
        )

        messages_data = results.get("messages", [])

        if not messages_data:
            return {
                "status": "success",
                "emails": [],
                "count": 0,
                "message": "No emails found",
            }

        # Fetch email data
        emails = []
        for msg_data in messages_data:
            message = (
                service.users()
                .messages()
                .get(userId="me", id=msg_data["id"], format="full")
                .execute()
            )
            emails.append(_extract_email_data(message))

        return {
            "status": "success",
            "emails": emails,
            "count": len(emails),
            "message": f"Found {len(emails)} emails",
        }

    except HttpError as e:
        return {"status": "error", "error_message": f"Search failed: {str(e)}"}
    except Exception as e:
        return {"status": "error", "error_message": f"Unexpected error: {str(e)}"}


def list_messages(max_results: int = 10, label: str = "INBOX") -> dict:
    """
    List messages from a specific label/folder.

    Args:
        max_results: Maximum number of results (default: 10, max: 50)
        label: Gmail label to filter by (default: "INBOX")
               Common labels: "INBOX", "SENT", "DRAFT", "SPAM", "TRASH", "UNREAD", "IMPORTANT"

    Returns:
        Dict with status and list of emails
    """
    print(f"--- Tool: list_messages called for {label} label ---")

    try:
        service = get_gmail_service()

        # Limit max_results to prevent overwhelming responses
        max_results = min(max_results, 50)

        # Get message IDs with label filter
        results = (
            service.users()
            .messages()
            .list(
                userId="me", maxResults=max_results, labelIds=[label] if label else None
            )
            .execute()
        )

        messages_data = results.get("messages", [])

        if not messages_data:
            return {
                "status": "success",
                "emails": [],
                "count": 0,
                "message": f"No messages found in {label}",
            }

        # Fetch email data
        emails = []
        for msg_data in messages_data:
            message = (
                service.users()
                .messages()
                .get(userId="me", id=msg_data["id"], format="full")
                .execute()
            )
            emails.append(_extract_email_data(message))

        return {
            "status": "success",
            "emails": emails,
            "count": len(emails),
            "message": f"Found {len(emails)} messages in {label}",
        }

    except HttpError as e:
        return {"status": "error", "error_message": f"List failed: {str(e)}"}
    except Exception as e:
        return {"status": "error", "error_message": f"Unexpected error: {str(e)}"}


def get_recent_emails(days: int = 1, max_results: int = 20) -> dict:
    """
    Get recent emails from the last N days.

    Args:
        days: Number of days to look back (default: 1)
        max_results: Maximum number of results (default: 20, max: 50)

    Returns:
        Dict with status and list of emails
    """
    print(f"--- Tool: get_recent_emails called for last {days} days ---")

    try:
        start_date = datetime.now() - timedelta(days=days)
        query = f"after:{start_date.strftime('%Y/%m/%d')}"

        return search_emails(query, max_results)

    except Exception as e:
        return {
            "status": "error",
            "error_message": f"Failed to get recent emails: {str(e)}",
        }


def get_emails_from_sender(sender_email: str, max_results: int = 10) -> dict:
    """
    Get emails from a specific sender.

    Args:
        sender_email: Email address of sender
        max_results: Maximum number of results (default: 10, max: 50)

    Returns:
        Dict with status and list of emails
    """
    print(f"--- Tool: get_emails_from_sender called for {sender_email} ---")

    query = f"from:{sender_email}"
    return search_emails(query, max_results)


def get_unread_emails(max_results: int = 20) -> dict:
    """
    Get unread emails.

    Args:
        max_results: Maximum number of results (default: 20, max: 50)

    Returns:
        Dict with status and list of unread emails
    """
    print("--- Tool: get_unread_emails called ---")

    query = "is:unread"
    return search_emails(query, max_results)


def get_important_emails(max_results: int = 15) -> dict:
    """
    Get emails marked as important.

    Args:
        max_results: Maximum number of results (default: 15, max: 50)

    Returns:
        Dict with status and list of important emails
    """
    print("--- Tool: get_important_emails called ---")

    query = "is:important"
    return search_emails(query, max_results)


def get_emails_with_attachments(days: int = 7, max_results: int = 15) -> dict:
    """
    Get emails with attachments from the last N days.

    Args:
        days: Number of days to look back (default: 7)
        max_results: Maximum number of results (default: 15, max: 50)

    Returns:
        Dict with status and list of emails with attachments
    """
    print(f"--- Tool: get_emails_with_attachments called for last {days} days ---")

    start_date = datetime.now() - timedelta(days=days)
    query = f"has:attachment after:{start_date.strftime('%Y/%m/%d')}"

    return search_emails(query, max_results)


def get_emails_by_subject(subject_keyword: str, max_results: int = 10) -> dict:
    """
    Get emails containing specific keywords in the subject.

    Args:
        subject_keyword: Keyword to search in subject line
        max_results: Maximum number of results (default: 10, max: 50)

    Returns:
        Dict with status and list of emails
    """
    print(f"--- Tool: get_emails_by_subject called for '{subject_keyword}' ---")

    query = f"subject:{subject_keyword}"
    return search_emails(query, max_results)
