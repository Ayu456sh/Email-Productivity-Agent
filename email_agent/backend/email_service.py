"""Email Service for retrieving emails from mock data or IMAP servers.

This module provides functionality to load mock emails from JSON files
or fetch real emails via IMAP.
"""
import os
import json
import datetime
from typing import List, Dict
from imap_tools import MailBox


class EmailService:
    """Service for managing email retrieval from multiple sources."""
    
    def __init__(self):
        self.mock_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'mock_inbox.json')
        
    def get_mock_emails(self) -> List[Dict]:
        """Load emails from the mock JSON file.
        
        Returns:
            List of email dictionaries from mock data.
        """
        if os.path.exists(self.mock_path):
            with open(self.mock_path, 'r') as f:
                return json.load(f)
        return []

    def fetch_real_emails(self, server: str, user: str, password: str, 
                          limit: int = 10) -> List[Dict]:
        """Fetch emails from IMAP server.
        
        Args:
            server: IMAP server address.
            user: Email account username.
            password: Email account password (should be app password for Gmail).
            limit: Maximum number of emails to fetch (default: 10).
            
        Returns:
            List of email dictionaries with standardized format.
            
        Raises:
            Exception: If IMAP connection or fetch fails.
        """
        emails = []
        try:
            with MailBox(server).login(user, password) as mailbox:
                # Fetch recent emails
                for msg in mailbox.fetch(limit=limit, reverse=True):
                    emails.append({
                        "id": msg.uid,
                        "sender": msg.from_,
                        "subject": msg.subject,
                        "body": msg.text or msg.html,
                        "timestamp": msg.date.isoformat(),
                        "category": None,
                        "action_items": [],
                        "is_read": False  # Treat fetched as unread for processing
                    })
        except Exception as e:
            raise Exception(f"IMAP Error: {e}")
            
        return emails
