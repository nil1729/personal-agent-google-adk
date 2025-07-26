"""
Enhanced Gmail Client Functions for Agentic Workflows
===================================================

Gmail client with comprehensive label management and enhanced email operations.
Each function returns a simple dict with status and data.
"""

import os

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

# Global service instance
_gmail_service = None


def get_gmail_service():
    """Get or create Gmail service instance."""
    global _gmail_service

    if _gmail_service is None:
        _gmail_service = _create_gmail_service()

    return _gmail_service


def _create_gmail_service():
    """Create Gmail service with authentication."""
    credentials_file = os.getenv("GMAIL_APP_CREDENTIALS_FILE")
    if not credentials_file:
        raise ValueError("GMAIL_APP_CREDENTIALS_FILE environment variable must be set")

    token_file = os.getenv("GMAIL_APP_TOKEN_FILE", "gmail_token.json")
    # Read-only scopes
    scopes = ["https://www.googleapis.com/auth/gmail.readonly"]

    creds = None

    if os.path.exists(token_file):
        creds = Credentials.from_authorized_user_file(token_file, scopes)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(credentials_file, scopes)
            creds = flow.run_local_server(port=0)

        with open(token_file, "w") as token:
            token.write(creds.to_json())

    return build("gmail", "v1", credentials=creds)


__all__ = [
    "get_gmail_service",
]
