"""Data Access Layer (DAL) for Email Productivity Agent.

This module handles all database operations including email management,
prompt storage, and draft management using SQLite.
"""
import sqlite3
import json
import os
from typing import List, Dict, Any, Optional

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'email_agent.db')


def get_db_connection() -> sqlite3.Connection:
    """Create and return a database connection with Row factory.
    
    Returns:
        SQLite connection object configured with Row factory.
    """
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def initialize_db():
    """Create tables for emails, prompts, and drafts."""
    conn = get_db_connection()
    c = conn.cursor()
    
    # Emails Table
    c.execute('''CREATE TABLE IF NOT EXISTS emails (
        id TEXT PRIMARY KEY,
        sender TEXT,
        subject TEXT,
        body TEXT,
        timestamp TEXT,
        category TEXT,
        action_items TEXT,
        is_read BOOLEAN
    )''')
    
    # Prompts Table
    c.execute('''CREATE TABLE IF NOT EXISTS prompts (
        name TEXT PRIMARY KEY,
        content TEXT
    )''')
    
    # Drafts Table
    c.execute('''CREATE TABLE IF NOT EXISTS drafts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        email_id TEXT,
        subject TEXT,
        body TEXT,
        created_at TEXT
    )''')
    
    conn.commit()
    conn.close()

def load_mock_inbox(json_data: List[Dict[str, Any]]) -> None:
    """Insert email data from mock inbox into the database.
    
    Args:
        json_data: List of email dictionaries to insert.
    """
    conn = get_db_connection()
    c = conn.cursor()
    
    for email in json_data:
        # Check if email already exists to avoid duplicates on restart
        c.execute("SELECT id FROM emails WHERE id = ?", (email['id'],))
        if c.fetchone() is None:
            c.execute('''INSERT INTO emails (id, sender, subject, body, timestamp, category, action_items, is_read)
                         VALUES (?, ?, ?, ?, ?, ?, ?, ?)''',
                      (email['id'], email['sender'], email['subject'], email['body'], email['timestamp'],
                       email.get('category'), json.dumps(email.get('action_items', [])), email['is_read']))
    
    conn.commit()
    conn.close()

def get_prompt(name: str) -> Optional[str]:
    """Retrieve a prompt template by name.
    
    Args:
        name: Name of the prompt template.
        
    Returns:
        Prompt content string if found, None otherwise.
    """
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("SELECT content FROM prompts WHERE name = ?", (name,))
    row = c.fetchone()
    conn.close()
    return row['content'] if row else None

def save_prompt(name: str, content: str) -> None:
    """Save or update a prompt template.
    
    Args:
        name: Name of the prompt template.
        content: The prompt template content.
    """
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("INSERT OR REPLACE INTO prompts (name, content) VALUES (?, ?)", (name, content))
    conn.commit()
    conn.close()

def save_processed_output(email_id: str, category: str, action_item_json: Any) -> None:
    """Update email with processing results.
    
    Args:
        email_id: Unique identifier for the email.
        category: Determined category for the email.
        action_item_json: Extracted action items (will be JSON serialized).
    """
    conn = get_db_connection()
    c = conn.cursor()
    c.execute('''UPDATE emails 
                 SET category = ?, action_items = ? 
                 WHERE id = ?''', 
              (category, json.dumps(action_item_json), email_id))
    conn.commit()
    conn.close()

def get_all_emails() -> List[Dict[str, Any]]:
    """Retrieve all emails from the database.
    
    Returns:
        List of email dictionaries with parsed action_items.
    """
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("SELECT * FROM emails ORDER BY timestamp DESC")
    emails = [dict(row) for row in c.fetchall()]
    conn.close()
    # Parse JSON fields
    for email in emails:
        if email['action_items']:
            try:
                email['action_items'] = json.loads(email['action_items'])
            except json.JSONDecodeError:
                email['action_items'] = []
    return emails

def get_email(email_id: str) -> Optional[Dict[str, Any]]:
    """Retrieve a single email by ID.
    
    Args:
        email_id: Unique identifier for the email.
        
    Returns:
        Email dictionary with parsed action_items if found, None otherwise.
    """
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("SELECT * FROM emails WHERE id = ?", (email_id,))
    row = c.fetchone()
    conn.close()
    if row:
        email = dict(row)
        if email['action_items']:
            try:
                email['action_items'] = json.loads(email['action_items'])
            except json.JSONDecodeError:
                email['action_items'] = []
        return email
    return None

def save_draft(email_id: str, subject: str, body: str) -> None:
    """Save a new draft reply.
    
    Args:
        email_id: ID of the email being replied to.
        subject: Draft email subject.
        body: Draft email body content.
    """
    conn = get_db_connection()
    c = conn.cursor()
    import datetime
    created_at = datetime.datetime.now().isoformat()
    c.execute("INSERT INTO drafts (email_id, subject, body, created_at) VALUES (?, ?, ?, ?)",
              (email_id, subject, body, created_at))
    conn.commit()
    conn.close()

def get_drafts() -> List[Dict[str, Any]]:
    """Retrieve all saved drafts.
    
    Returns:
        List of draft dictionaries ordered by creation time (newest first).
    """
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("SELECT * FROM drafts ORDER BY created_at DESC")
    drafts = [dict(row) for row in c.fetchall()]
    conn.close()
    return drafts

def delete_draft(draft_id: int) -> None:
    """Delete a draft by ID.
    
    Args:
        draft_id: Unique identifier for the draft to delete.
    """
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("DELETE FROM drafts WHERE id = ?", (draft_id,))
    conn.commit()
    conn.close()

def update_draft(draft_id: int, subject: str, body: str) -> None:
    """Update an existing draft.
    
    Args:
        draft_id: Unique identifier for the draft to update.
        subject: Updated email subject.
        body: Updated email body content.
    """
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("UPDATE drafts SET subject = ?, body = ? WHERE id = ?", (subject, body, draft_id))
    conn.commit()
    conn.close()

def save_email(email: Dict[str, Any]) -> None:
    """Insert a single email if it doesn't already exist.
    
    Args:
        email: Email dictionary containing all required fields.
    """
    conn = get_db_connection()
    c = conn.cursor()
    # Check if exists
    c.execute("SELECT id FROM emails WHERE id = ?", (email['id'],))
    if c.fetchone() is None:
        c.execute('''INSERT INTO emails (id, sender, subject, body, timestamp, category, action_items, is_read)
                     VALUES (?, ?, ?, ?, ?, ?, ?, ?)''',
                  (email['id'], email['sender'], email['subject'], email['body'], email['timestamp'],
                   email.get('category'), json.dumps(email.get('action_items', [])), email['is_read']))
    conn.commit()
    conn.close()
