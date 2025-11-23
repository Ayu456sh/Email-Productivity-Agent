import streamlit as st
from streamlit_option_menu import option_menu
import os
import json
import time
import requests

# Page Config
st.set_page_config(page_title="Email Agent Pro", page_icon="⚡", layout="wide")

API_URL = "http://localhost:8000"

# --- CSS INJECTION ---
def local_css(file_name):
    with open(file_name) as f:
        st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)

css_path = os.path.join(os.path.dirname(__file__), 'style.css')
if os.path.exists(css_path):
    local_css(css_path)

# --- HELPER FUNCTIONS ---
def get_badge_class(category):
    if not category: return "badge-newsletter"
    cat_lower = category.lower()
    if "urgent" in cat_lower or "high" in cat_lower: return "badge-urgent"
    if "to-do" in cat_lower: return "badge-todo"
    if "meeting" in cat_lower: return "badge-meeting"
    return "badge-newsletter"

def check_api_status():
    try:
        resp = requests.get(f"{API_URL}/")
        return resp.status_code == 200
    except:
        return False

# --- SIDEBAR NAVIGATION ---
with st.sidebar:
    selected = option_menu(
        "Agent Pro",
        ["Dashboard", "Inbox", "The Brain", "Chat", "Drafts"],
        icons=['speedometer2', 'inbox', 'cpu', 'chat-dots', 'file-earmark-text'],
        menu_icon="robot",
        default_index=0,
        styles={
            "container": {"padding": "0!important", "background-color": "#000000"},
            "icon": {"color": "#00F0FF", "font-size": "16px"}, 
            "nav-link": {"font-size": "14px", "text-align": "left", "margin":"0px", "--hover-color": "#1F2937"},
            "nav-link-selected": {"background-color": "#1F2937", "border-left": "3px solid #00F0FF"},
        }
    )
    st.markdown("---")
    
    api_status = check_api_status()
    if api_status:
        st.caption("SYSTEM STATUS: ONLINE")
        st.caption("v2.1.0 | FUTURISTIC BUILD")
    else:
        st.error("⚠️ BACKEND OFFLINE")
        st.caption("Please run: uvicorn email_agent.backend.main:app --reload")

# --- DASHBOARD ---
if selected == "Dashboard":
    st.markdown("## 📊 COMMAND CENTER")
    
    if not api_status:
        st.warning("Backend is offline. Cannot fetch data.")
    else:
        try:
            emails = requests.get(f"{API_URL}/emails").json()
            drafts = requests.get(f"{API_URL}/drafts").json()
            
            unread_count = sum(1 for e in emails if not e['is_read'])
            urgent_count = sum(1 for e in emails if e['category'] and "urgent" in e['category'].lower())
            draft_count = len(drafts)
            
            # Top Metrics Row
            c1, c2, c3, c4 = st.columns(4)
            c1.metric("UNREAD", unread_count)
            c2.metric("URGENT", urgent_count)
            c3.metric("DRAFTS", draft_count)
            c4.metric("SYSTEM HEALTH", "100%")
            
            st.markdown("---")
            
            # Split View: Recent Activity vs Quick Actions
            col_main, col_side = st.columns([2, 1])
            
            with col_main:
                st.markdown("### 📡 INCOMING STREAM")
                for email in emails[:4]:
                    badge_class = get_badge_class(email['category'])
                    cat_display = email['category'] if email['category'] else "PENDING"
                    st.markdown(f"""
                    <div class="email-card">
                        <div style="display: flex; justify-content: space-between;">
                            <span class="badge {badge_class}">{cat_display}</span>
                            <span style="color: var(--text-muted); font-size: 0.8rem;">{email['timestamp'][:10]}</span>
                        </div>
                        <div style="font-weight: 600; margin-top: 0.5rem;">{email['subject']}</div>
                        <div style="color: var(--text-muted); font-size: 0.9rem;">{email['sender']}</div>
                    </div>
                    """, unsafe_allow_html=True)
                    
            with col_side:
                st.markdown("### ⚡ QUICK ACTIONS")
                
                # Primary action: Load Inbox
                if st.button("📂 LOAD INBOX", use_container_width=True, type="primary"):
                    with st.spinner("LOADING INBOX..."):
                        resp = requests.post(f"{API_URL}/sync/mock")
                        if resp.status_code == 200:
                            count = resp.json()['count']
                            st.toast(f"✅ Inbox Connected: {count} Emails Loaded", icon="📧")
                            time.sleep(1)
                            st.rerun()
                        else:
                            st.error(f"Error: {resp.text}")
                
                st.info("Agent is idle. Waiting for commands.")
        except Exception as e:
            st.error(f"Error fetching data: {e}")

# --- THE BRAIN ---
elif selected == "The Brain":
    st.markdown("## 🧠 COGNITIVE ARCHITECTURE")
    st.markdown("Configure the neural pathways for the agent's logic cores.")
    
    prompt_types = {
        "categorization": "🔍 CATEGORIZATION LOGIC",
        "action_items": "📋 TASK EXTRACTION PROTOCOL",
        "auto_reply": "✍️ RESPONSE GENERATION MATRIX"
    }
    
    if api_status:
        for p_key, p_label in prompt_types.items():
            with st.expander(p_label, expanded=True):
                try:
                    current_content = requests.get(f"{API_URL}/prompts/{p_key}").json()['content']
                    
                    if p_key == "auto_reply":
                        st.caption("Define the personality and tone the Agent uses when writing drafts.")
                    elif p_key == "categorization":
                        st.caption("Edit the logic rules below to teach the Agent how to classify emails.")
                    else:
                        st.caption("Edit the rules below to teach the Agent how to behave. System instructions are hidden.")
                    
                    new_content = st.text_area(f"USER RULES: {p_key.upper()}", value=current_content, height=250, key=f"txt_{p_key}")
                    
                    c_save, c_void = st.columns([1, 3])
                    with c_save:
                        if st.button("💾 UPDATE NEURAL PATHWAYS", key=f"save_{p_key}", type="primary", use_container_width=True):
                            with st.spinner("UPLOADING NEURAL WEIGHTS..."):
                                requests.post(f"{API_URL}/prompts/{p_key}", json={"content": new_content})
                                time.sleep(0.8) # Cinematic delay
                            st.toast(f"{p_key.upper()} MODULE UPDATED", icon="✅")
                except Exception as e:
                    st.error(f"Error loading prompt: {e}")

# --- INBOX VIEWER (CRM STYLE) ---
elif selected == "Inbox":
    st.markdown("## 📥 DATA STREAM")
    
    # Simulate Ingestion Animation (Only on first load of this page view)
    if 'inbox_loaded' not in st.session_state:
        loader_placeholder = st.empty()
        with loader_placeholder.container():
            st.markdown('<div class="pulsing-loader">📡 ESTABLISHING SECURE UPLINK...</div>', unsafe_allow_html=True)
            time.sleep(0.8)
            st.markdown('<div class="pulsing-loader">🔄 INGESTING EMAIL PACKETS...</div>', unsafe_allow_html=True)
            time.sleep(0.8)
            st.markdown('<div class="pulsing-loader">🤖 RUNNING CLASSIFICATION NEURAL NET...</div>', unsafe_allow_html=True)
            time.sleep(0.8)
        loader_placeholder.empty()
        st.session_state['inbox_loaded'] = True
    
    if api_status:
        emails = requests.get(f"{API_URL}/emails").json()
        
        # Master-Detail Layout
        col_list, col_detail = st.columns([1, 2])
        
        # Select Email Logic (using session state to track selection)
        if 'selected_email_id' not in st.session_state:
            st.session_state.selected_email_id = emails[0]['id'] if emails else None
            
        with col_list:
            st.markdown("### MESSAGES")
            for email in emails:
                # Highlight selected
                is_selected = st.session_state.selected_email_id == email['id']
                border_style = "2px solid #00F0FF" if is_selected else "1px solid #1F2937"
                bg_style = "#111" if is_selected else "var(--card-bg)"
                
                # Use a container for the card to allow clicking the button inside
                with st.container():
                    if st.button(f"{email['sender']}\n{email['subject'][:30]}...", key=f"btn_{email['id']}", use_container_width=True):
                        st.session_state.selected_email_id = email['id']
                        st.rerun()
        
        # Detail View
        with col_detail:
            if st.session_state.selected_email_id:
                email = next((e for e in emails if e['id'] == st.session_state.selected_email_id), None)
                if email:
                    # Header
                    st.markdown(f"""
                    <div style="padding: 1.5rem; border: 1px solid var(--border-color); border-radius: 8px; background: #0A0A0A; box-shadow: 0 4px 20px rgba(0,0,0,0.5);">
                        <div style="display: flex; justify-content: space-between; align-items: center;">
                            <h2 style="margin: 0;">{email['subject']}</h2>
                            <span class="badge {get_badge_class(email['category'])}">{email['category'] or 'UNPROCESSED'}</span>
                        </div>
                        <div style="color: var(--text-muted); margin-top: 0.5rem; font-size: 0.9rem;">
                            <strong>FROM:</strong> {email['sender']} &nbsp;|&nbsp; <strong>RECEIVED:</strong> {email['timestamp']}
                        </div>
                        <hr style="border-color: var(--border-color); margin: 1.5rem 0;">
                        <div style="line-height: 1.7; font-size: 1.05rem;">
                            {email['body']}
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    # Action Panel
                    st.markdown("### ⚙️ OPERATIONS")
                    ac1, ac2 = st.columns(2)
                    
                    with ac1:
                        if st.button("⚡ ANALYZE (Categorize & Extract)", key="analyze_btn", use_container_width=True):
                            with st.spinner("PROCESSING..."):
                                resp = requests.post(f"{API_URL}/emails/{email['id']}/process")
                                if resp.status_code == 200:
                                    st.rerun()
                                else:
                                    st.error(f"Error: {resp.text}")
                                
                    with ac2:
                        if st.button("✍️ GENERATE DRAFT", key="draft_btn", use_container_width=True):
                            with st.spinner("GENERATING..."):
                                resp = requests.post(f"{API_URL}/emails/{email['id']}/draft")
                                if resp.status_code == 200:
                                    st.toast("DRAFT COMPILED", icon="📝")
                                else:
                                    st.error(f"Error: {resp.text}")

                    # Extraction Results (Animated Expansion)
                    if email['action_items']:
                        st.markdown("### 📋 EXTRACTED INTELLIGENCE")
                        ai_data = email['action_items']
                        
                        with st.expander("VIEW PARSED JSON DATA", expanded=True):
                            if isinstance(ai_data, dict):
                                if ai_data.get('action_summary'):
                                    st.info(f"**SUMMARY:** {ai_data['action_summary']}")
                                if ai_data.get('tasks'):
                                    st.table(ai_data['tasks'])
                            elif isinstance(ai_data, list) and ai_data:
                                # Display as code block for the "technical" feel
                                st.code(json.dumps(ai_data, indent=2), language='json')
                            else:
                                st.write(ai_data)

# --- CHAT ---
elif selected == "Chat":
    st.markdown("## 💬 NEURAL INTERFACE")
    
    # Helper for typing effect
    def stream_text(text, delay=0.02):
        """Simulates typing effect"""
        placeholder = st.empty()
        full_text = ""
        for char in text:
            full_text += char
            placeholder.markdown(full_text + "▌")
            time.sleep(delay)
        placeholder.markdown(full_text)
        return full_text

    if "messages" not in st.session_state:
        st.session_state.messages = []

    # Display History
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            if message.get("is_html"):
                st.markdown(message["content"], unsafe_allow_html=True)
            else:
                st.markdown(message["content"])

    # Input
    if prompt := st.chat_input("Input command..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant"):
            if not api_status:
                 response = "⚠️ SYSTEM OFFLINE: BACKEND DISCONNECTED."
                 stream_text(response)
                 st.session_state.messages.append({"role": "assistant", "content": response})
            else:
                with st.spinner("COMPUTING..."):
                    try:
                        # Check for draft intent without selection
                        is_draft_request = "draft" in prompt.lower() and "reply" in prompt.lower()
                        selected_id = st.session_state.get('selected_email_id')
                        
                        if is_draft_request and not selected_id:
                            response = "⚠️ PLEASE SELECT AN EMAIL FIRST: I need to know which email to reply to."
                            stream_text(response)
                            st.session_state.messages.append({"role": "assistant", "content": response})
                        else:
                            payload = {"message": prompt}
                            if selected_id:
                                payload["selected_email_id"] = selected_id
                                
                            resp = requests.post(f"{API_URL}/chat", json=payload).json()
                            
                            if resp['type'] == 'draft':
                                intro = "Acknowledged. Initiating drafting protocols..."
                                stream_text(intro)
                                st.session_state.messages.append({"role": "assistant", "content": intro})
                                
                                draft_content = resp['content']
                                
                                # Display Draft in Styled Container
                                draft_html = f"""
                                <div class="draft-container">
                                    <div style="color: var(--warning-color); font-size: 0.8rem; margin-bottom: 0.5rem; text-transform: uppercase; letter-spacing: 1px;">
                                        ⚠️ DRAFT PREVIEW - DO NOT SEND
                                    </div>
                                    {draft_content.replace(chr(10), '<br>')}
                                </div>
                                """
                                st.markdown(draft_html, unsafe_allow_html=True)
                                st.session_state.messages.append({"role": "assistant", "content": draft_html, "is_html": True})
                                
                                # Safety Button
                                c_safe, c_edit = st.columns([1, 1])
                                with c_safe:
                                    if st.button("💾 SAVE AS DRAFT (DO NOT SEND)", key=f"safe_save_{int(time.time())}", type="primary"):
                                        requests.post(f"{API_URL}/drafts", json={
                                            "email_id": "chat_gen",
                                            "subject": f"Draft from Chat: {prompt[:20]}...",
                                            "body": draft_content
                                        })
                                        st.toast("SECURELY SAVED TO DRAFTS", icon="🔒")
                            else:
                                # Check for structured draft output in text response (from new prompt)
                                if "### Suggested Draft Reply" in resp['content']:
                                    parts = resp['content'].split("### Suggested Follow-Up Action (JSON)")
                                    draft_part = parts[0]
                                    follow_up_part = parts[1] if len(parts) > 1 else None
                                    
                                    st.markdown(draft_part)
                                    st.session_state.messages.append({"role": "assistant", "content": draft_part})
                                    
                                    if follow_up_part:
                                        try:
                                            # Clean up JSON string
                                            json_str = follow_up_part.strip().strip('`').strip()
                                            follow_up_data = json.loads(json_str)
                                            st.info(f"**SUGGESTED FOLLOW-UP:**\n\nTask: {follow_up_data.get('task')}\nDeadline: {follow_up_data.get('deadline')}")
                                            st.session_state.messages.append({"role": "assistant", "content": f"**SUGGESTED FOLLOW-UP:**\n\nTask: {follow_up_data.get('task')}\nDeadline: {follow_up_data.get('deadline')}"})
                                        except:
                                            st.text(follow_up_part)
                                else:
                                    response_text = resp['content']
                                    stream_text(response_text)
                                    st.session_state.messages.append({"role": "assistant", "content": response_text})

                    except Exception as e:
                        st.error(f"Error: {e}")

# --- DRAFTS ---
elif selected == "Drafts":
    st.markdown("## 📝 OUTBOX BUFFER")
    
    if api_status:
        drafts = requests.get(f"{API_URL}/drafts").json()
        
        if not drafts:
            st.info("BUFFER EMPTY.")
        else:
            for draft in drafts:
                with st.expander(f"DRAFT: {draft['subject']}", expanded=True):
                    # Editable Fields
                    new_subject = st.text_input("SUBJECT", value=draft['subject'], key=f"subj_{draft['id']}")
                    new_body = st.text_area("CONTENT", value=draft['body'], height=200, key=f"d_{draft['id']}")
                    
                    c1, c2, c3 = st.columns([1, 1, 3])
                    with c1:
                        if st.button("💾 SAVE CHANGES", key=f"save_d_{draft['id']}", type="primary"):
                            requests.put(f"{API_URL}/drafts/{draft['id']}", json={
                                "email_id": draft['email_id'],
                                "subject": new_subject,
                                "body": new_body
                            })
                            st.toast("DRAFT UPDATED", icon="✅")
                            time.sleep(0.5)
                            st.rerun()
                            
                    with c2:
                        st.button("🚀 TRANSMIT", key=f"send_{draft['id']}", disabled=True, help="Sending disabled for safety.")
                    with c3:
                        if st.button("🗑️ PURGE", key=f"del_{draft['id']}"):
                            requests.delete(f"{API_URL}/drafts/{draft['id']}")
                            st.rerun()
