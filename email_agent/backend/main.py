"""Email Productivity Agent API.

This module provides a FastAPI-based RESTful API for managing emails,
generating drafts, and interacting with an AI-powered email assistant.
"""
from fastapi import FastAPI, HTTPException, Body
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import json
import os
import sys

# Add current directory to path to ensure imports work
sys.path.append(os.path.dirname(__file__))

import dal
import llm_service
from email_service import EmailService
import system_prompts

email_service = EmailService()

app = FastAPI(title="Email Agent Pro API", version="2.1.0")

# Add CORS middleware to allow frontend to connect
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)

# Initialize DB on startup
@app.on_event("startup")
def startup_event() -> None:
    """Initialize database and load default data on application startup.
    
    This function:
    - Initializes the database schema
    - Loads mock email data if no emails exist
    - Loads default prompts if they haven't been configured
    """
    dal.initialize_db()
    # Load mock data if empty (logic copied from app.py)
    emails = dal.get_all_emails()
    if not emails:
        mock_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'mock_inbox.json')
        if os.path.exists(mock_path):
            with open(mock_path, 'r') as f:
                mock_data = json.load(f)
                dal.load_mock_inbox(mock_data)
    
    # Load default prompts
    if not dal.get_prompt("categorization"):
        defaults_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'prompts', 'default_prompts.json')
        if os.path.exists(defaults_path):
            with open(defaults_path, 'r') as f:
                defaults = json.load(f)
                for name, data in defaults.items():
                    dal.save_prompt(name, data['content'])

# --- Pydantic Models ---
class DraftRequest(BaseModel):
    email_id: str
    subject: str
    body: str

class ChatRequest(BaseModel):
    message: str
    selected_email_id: Optional[str] = None

class ProcessRequest(BaseModel):
    email_id: str

# --- Endpoints ---

@app.get("/")
def read_root() -> Dict[str, str]:
    """Health check endpoint.
    
    Returns:
        Dictionary containing API status and version information.
    """
    return {"status": "online", "version": "2.1.0"}

@app.get("/emails")
def get_emails() -> List[Dict[str, Any]]:
    """Retrieve all emails from the database.
    
    Returns:
        List of email dictionaries containing all email data.
    """
    return dal.get_all_emails()

@app.get("/emails/{email_id}")
def get_email(email_id: str) -> Dict[str, Any]:
    """Retrieve a specific email by ID.
    
    Args:
        email_id: Unique identifier for the email.
        
    Returns:
        Email dictionary containing all email data.
        
    Raises:
        HTTPException: 404 if email not found.
    """
    email = dal.get_email(email_id)
    if not email:
        raise HTTPException(status_code=404, detail="Email not found")
    return email

@app.post("/emails/{email_id}/process")
def process_email(email_id: str) -> Dict[str, Any]:
    """Process an email: categorize it and extract action items.
    
    Args:
        email_id: Unique identifier for the email to process.
        
    Returns:
        Dictionary containing processing status, category, and extracted action items.
        
    Raises:
        HTTPException: 404 if email not found, 500 if processing fails.
    """
    email = dal.get_email(email_id)
    if not email:
        raise HTTPException(status_code=404, detail="Email not found")
    
    try:
        # Categorize
        user_rules = dal.get_prompt("categorization")
        full_prompt = system_prompts.CATEGORIZATION_SYSTEM_PROMPT.replace("[USER_RULES_PLACEHOLDER]", user_rules)
        category = llm_service.generate_response(full_prompt, email['body'])
        
        # Extract Actions
        user_rules_actions = dal.get_prompt("action_items")
        full_action_prompt = system_prompts.ACTION_ITEMS_SYSTEM_PROMPT.replace(
            "[USER_RULES_PLACEHOLDER]", user_rules_actions
        )
        actions_resp = llm_service.generate_response(full_action_prompt, email['body'])
        try:
            actions = json.loads(llm_service.extract_json(actions_resp))
        except json.JSONDecodeError:
            actions = []
            
        dal.save_processed_output(email_id, category, actions)
        return {"status": "success", "category": category, "action_items": actions}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/emails/{email_id}/draft")
def generate_draft(email_id: str) -> Dict[str, Any]:
    """Generate a draft reply for a specific email.
    
    Args:
        email_id: Unique identifier for the email to reply to.
        
    Returns:
        Dictionary containing status and generated draft body.
        
    Raises:
        HTTPException: 404 if email not found, 500 if generation fails.
    """
    email = dal.get_email(email_id)
    if not email:
        raise HTTPException(status_code=404, detail="Email not found")
    
    try:
        user_rules = dal.get_prompt("auto_reply")
        full_prompt = system_prompts.AUTO_REPLY_SYSTEM_PROMPT.replace("[USER_RULES_PLACEHOLDER]", user_rules)
        draft_body = llm_service.generate_response(full_prompt, email['body'])
        dal.save_draft(email_id, f"Re: {email['subject']}", draft_body)
        return {"status": "success", "draft_body": draft_body}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/drafts")
def get_drafts() -> List[Dict[str, Any]]:
    """Retrieve all saved drafts.
    
    Returns:
        List of draft dictionaries.
    """
    return dal.get_drafts()

@app.post("/drafts")
def create_draft(draft: DraftRequest) -> Dict[str, str]:
    """Create a new draft.
    
    Args:
        draft: Draft request containing email_id, subject, and body.
        
    Returns:
        Dictionary containing operation status.
    """
    dal.save_draft(draft.email_id, draft.subject, draft.body)
    return {"status": "success"}

@app.delete("/drafts/{draft_id}")
def delete_draft(draft_id: int) -> Dict[str, str]:
    """Delete a draft by ID.
    
    Args:
        draft_id: Unique identifier for the draft to delete.
        
    Returns:
        Dictionary containing operation status.
    """
    dal.delete_draft(draft_id)
    return {"status": "success"}

@app.put("/drafts/{draft_id}")
def update_draft(draft_id: int, draft: DraftRequest) -> Dict[str, str]:
    """Update an existing draft.
    
    Args:
        draft_id: Unique identifier for the draft to update.
        draft: Updated draft data containing subject and body.
        
    Returns:
        Dictionary containing operation status.
    """
    dal.update_draft(draft_id, draft.subject, draft.body)
    return {"status": "success"} 

@app.post("/chat")
def chat(request: ChatRequest) -> Dict[str, str]:
    """Handle chat interactions with the email assistant.
    
    Args:
        request: Chat request containing message and optionally selected_email_id.
        
    Returns:
        Dictionary containing response type and content.
    """
    prompt = request.message
    
    if "draft" in prompt.lower() and "reply" in prompt.lower():
        # Special draft handling
        email_body_context = ""
        if request.selected_email_id:
            email = dal.get_email(request.selected_email_id)
            if email:
                email_body_context = email['body']
                
        user_rules = dal.get_prompt("auto_reply")
        full_prompt = system_prompts.AUTO_REPLY_SYSTEM_PROMPT.replace("[USER_RULES_PLACEHOLDER]", user_rules)
        draft_content = llm_service.generate_response(full_prompt, email_body_context, additional_context=prompt)
        return {"type": "draft", "content": draft_content}
    else:
        # General chat with Inbox Context
        # Fetch recent emails for context
        emails = dal.get_all_emails()
        # Summarize emails for context (limit to last 20 to fit context window)
        email_context = "\n".join([
            f"- [{e['category'] or 'Uncategorized'}] From: {e['sender']}, Subject: {e['subject']}" 
            for e in emails[:20]
        ])
        
        generic_prompt = f"""You are an advanced email productivity agent. 
        You have access to the user's inbox metadata below.
        
        INBOX CONTEXT:
        {email_context}
        
        USER QUERY: {{email_body}}
        
        Answer the user's query based on the inbox context if relevant. Be concise."""
        
        response_text = llm_service.generate_response(generic_prompt, prompt)
        return {"type": "text", "content": response_text}

@app.get("/prompts/{name}")
def get_prompt(name: str) -> Dict[str, str]:
    """Retrieve a specific prompt template by name.
    
    Args:
        name: Name of the prompt template (e.g., 'categorization', 'auto_reply').
        
    Returns:
        Dictionary containing the prompt content.
    """
    return {"content": dal.get_prompt(name)}

@app.post("/prompts/{name}")
def update_prompt(name: str, body: Dict[str, str] = Body(...)) -> Dict[str, str]:
    """Update a prompt template.
    
    Args:
        name: Name of the prompt template to update.
        body: Dictionary containing the new prompt content.
        
    Returns:
        Dictionary containing operation status.
    """
    dal.save_prompt(name, body['content'])
    return {"status": "success"}

@app.post("/sync/mock")
def sync_mock() -> Dict[str, Any]:
    """Load mock email data into the database.
    
    Returns:
        Dictionary containing operation status and count of loaded emails.
        
    Raises:
        HTTPException: 500 if sync fails.
    """
    try:
        mock_emails = email_service.get_mock_emails()
        dal.load_mock_inbox(mock_emails)
        return {"status": "success", "count": len(mock_emails)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/sync/real")
def sync_real() -> Dict[str, Any]:
    """Fetch real emails from IMAP server and save to database.
    
    Requires EMAIL_IMAP_SERVER, EMAIL_USER, and EMAIL_PASSWORD environment variables.
    
    Returns:
        Dictionary containing operation status and count of synced emails.
        
    Raises:
        HTTPException: 400 if credentials missing, 500 if sync fails.
    """
    server = os.getenv("EMAIL_IMAP_SERVER")
    user = os.getenv("EMAIL_USER")
    password = os.getenv("EMAIL_PASSWORD")
    
    if not all([server, user, password]):
        raise HTTPException(status_code=400, detail="Missing email credentials in .env")
        
    try:
        real_emails = email_service.fetch_real_emails(server, user, password)
        # Save to DB (using load_mock_inbox logic for now as it handles upsert/replace)
        # Ideally we should have a dedicated upsert method, but for now this works if we want to append/merge
        # Actually, let's just loop and save individually to be safe and not wipe existing if we want to keep history
        for email in real_emails:
            # Check if exists to avoid overwriting processed status if we re-fetch
            existing = dal.get_email(email['id'])
            if not existing:
                dal.save_email(email)
                
        return {"status": "success", "count": len(real_emails)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
