# ============================================
# 📁 app.py - APEX AI AGENT (FINAL)
# TAQWA's Final Project - STREAMLIT CLOUD READY
# ============================================
# FORCE DEPLOY - v2.1
import os
import json
import datetime
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import streamlit as st
from dotenv import load_dotenv
import pandas as pd
from google import genai
import requests

from langchain.agents import create_agent
from langchain.tools import tool
from langchain_google_genai import ChatGoogleGenerativeAI

# ✅ FORCE DEPLOY - v2.0
st.set_page_config(page_title="Apex AI Agent", page_icon="🤖", layout="wide")

load_dotenv()

# ============================================
# 📧 GMAIL SETUP
# ============================================

GMAIL_EMAIL = os.getenv("GMAIL_EMAIL", "banukabil348@gmail.com")
GMAIL_PASSWORD = os.getenv("GMAIL_PASSWORD", "your_app_password")

def send_gmail_notification(to_email, subject, body):
    try:
        msg = MIMEMultipart()
        msg['From'] = GMAIL_EMAIL
        msg['To'] = to_email
        msg['Subject'] = subject
        msg.attach(MIMEText(body, 'plain'))
        
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(GMAIL_EMAIL, GMAIL_PASSWORD)
        server.send_message(msg)
        server.quit()
        return True
    except Exception as e:
        print(f"Email error: {e}")
        return False

# ============================================
# 📁 DATA HANDLING
# ============================================

def load_users():
    try:
        os.makedirs('data', exist_ok=True)
        with open('data/users.json', 'r') as f:
            return json.load(f)
    except Exception:
        return []

def save_user(user_data):
    users = load_users()
    for i, u in enumerate(users):
        if u['email'] == user_data['email']:
            users[i] = user_data
            with open('data/users.json', 'w') as f:
                json.dump(users, f, indent=4)
            return
    users.append(user_data)
    with open('data/users.json', 'w') as f:
        json.dump(users, f, indent=4)

def load_messages():
    try:
        os.makedirs('data', exist_ok=True)
        with open('data/messages.json', 'r') as f:
            return json.load(f)
    except Exception:
        return []

def save_message(msg_data):
    messages = load_messages()
    messages.append(msg_data)
    with open('data/messages.json', 'w') as f:
        json.dump(messages, f, indent=4)

def load_admin_replies():
    try:
        os.makedirs('data', exist_ok=True)
        with open('data/admin_replies.json', 'r') as f:
            return json.load(f)
    except Exception:
        return []

def save_admin_reply(reply_data):
    replies = load_admin_replies()
    replies.append(reply_data)
    with open('data/admin_replies.json', 'w') as f:
        json.dump(replies, f, indent=4)

def load_admin_chat_history():
    try:
        os.makedirs('data', exist_ok=True)
        with open('data/admin_chat_history.json', 'r') as f:
            return json.load(f)
    except Exception:
        return []

def save_admin_chat_history(chat_data):
    history = load_admin_chat_history()
    history.append(chat_data)
    with open('data/admin_chat_history.json', 'w') as f:
        json.dump(history, f, indent=4)

def get_user_by_email(email):
    users = load_users()
    for user in users:
        if user['email'] == email:
            return user
    return None

def get_user_messages(email):
    messages = load_messages()
    user_msgs = []
    for msg in messages:
        if msg.get('user') == email:
            user_msgs.append(msg)
    return user_msgs

def clear_all_history():
    with open('data/messages.json', 'w') as f:
        json.dump([], f, indent=4)
    with open('data/admin_chat_history.json', 'w') as f:
        json.dump([], f, indent=4)
    with open('data/admin_replies.json', 'w') as f:
        json.dump([], f, indent=4)

def clear_user_history(email):
    messages = load_messages()
    user_msgs = [msg for msg in messages if msg.get('user') != email]
    with open('data/messages.json', 'w') as f:
        json.dump(user_msgs, f, indent=4)

# ============================================
# 🤖 GEMINI SETUP
# ============================================

gemini_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")

if not gemini_key:
    st.error("❌ GEMINI_API_KEY missing! Add to .env file")
    st.stop()

client = genai.Client(api_key=gemini_key)

def generate_ai_response(prompt):
    models_to_try = [
        "gemini-3.6-flash",
        "gemini-3.5-flash",
        "gemini-3.5-flash-lite",
        "gemini-2.5-flash",
        "gemini-2.0-flash",
    ]
    
    for model_name in models_to_try:
        try:
            response = client.models.generate_content(
                model=model_name,
                contents=prompt
            )
            if response and response.text:
                return response.text
        except Exception:
            continue
            
    return None

# ============================================
# 🔍 TAVILY SEARCH
# ============================================

TAVILY_API_KEY = os.getenv("TAVILY_API_KEY")

def search_internet(query):
    if not TAVILY_API_KEY:
        return "Tavily API key not configured."
    
    try:
        url = "https://api.tavily.com/search"
        payload = {
            "api_key": TAVILY_API_KEY,
            "query": query,
            "search_depth": "basic",
            "max_results": 3
        }
        response = requests.post(url, json=payload)
        data = response.json()
        
        results = data.get('results', [])
        if results:
            output = "📊 **Search Results:**\n\n"
            for i, result in enumerate(results[:3], 1):
                output += f"{i}. {result.get('content', '')[:200]}\n\n"
            return output
        return "No results found."
    except Exception as e:
        return f"Search error: {e}"

# ============================================
# 📊 REPORT FUNCTIONS
# ============================================

def get_todays_report_data():
    try:
        users = load_users()
        messages = load_messages()
        
        today = datetime.datetime.now().strftime("%Y-%m-%d")
        today_users = [u for u in users if u.get('signup_time', '').startswith(today)]
        today_messages = [m for m in messages if m.get('timestamp', '').startswith(today)]
        
        data = []
        for msg in today_messages[-10:]:
            data.append({
                "User": msg.get('name', 'Unknown'),
                "Message": msg.get('message', '')[:50],
                "Time": msg.get('timestamp', '')[:16]
            })
        
        if not data:
            data = [{"User": "No Data", "Message": "No messages today", "Time": "-"}]
        
        return pd.DataFrame(data)
    except Exception:
        return pd.DataFrame([{"User": "Error", "Message": "Data load issue", "Time": "-"}])

def send_daily_report():
    try:
        df = get_todays_report_data()
        table_html = df.to_html(index=False, border=0)
        
        users = load_users()
        messages = load_messages()
        today = datetime.datetime.now().strftime("%Y-%m-%d")
        today_users = [u for u in users if u.get('signup_time', '').startswith(today)]
        today_messages = [m for m in messages if m.get('timestamp', '').startswith(today)]
        
        html_body = f"""
        <html>
        <body style="font-family: Arial, sans-serif;">
            <h2>📊 Daily Report - {today}</h2>
            <p><b>👥 New Users:</b> {len(today_users)}</p>
            <p><b>💬 New Messages:</b> {len(today_messages)}</p>
            <p><b>👤 Total Users:</b> {len(users)}</p>
            <p><b>💬 Total Messages:</b> {len(messages)}</p>
            <hr>
            <h3>📝 Recent Messages</h3>
            {table_html}
            <hr>
            <p style="color:gray;">Sent by Apex AI Agent 🤖</p>
        </body>
        </html>
        """
        
        msg = MIMEMultipart()
        msg['From'] = GMAIL_EMAIL
        msg['To'] = GMAIL_EMAIL
        msg['Subject'] = f"📊 Daily Report - {today}"
        msg.attach(MIMEText(html_body, 'html'))
        
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(GMAIL_EMAIL, GMAIL_PASSWORD)
        server.send_message(msg)
        server.quit()
        return "✅ Report sent to Admin Gmail!"
    except Exception as e:
        return f"❌ Error: {str(e)}"

# ============================================
# 🧠 LANGCHAIN v1 AGENT TOOLS
# ============================================

@tool
def internet_search(query: str) -> str:
    """Search the internet for current information, news, or latest updates."""
    return search_internet(query)

@tool
def get_report_data(query: str) -> str:
    """Get today's business report data including new users, messages, and recent activity."""
    df = get_todays_report_data()
    users = load_users()
    messages = load_messages()
    today = datetime.datetime.now().strftime("%Y-%m-%d")
    today_users = [u for u in users if u.get("signup_time", "").startswith(today)]
    today_messages = [m for m in messages if m.get("timestamp", "").startswith(today)]

    return (
        f"📊 **Today's Report ({today})**\n\n"
        f"👥 New Users: {len(today_users)}\n"
        f"💬 New Messages: {len(today_messages)}\n"
        f"👤 Total Users: {len(users)}\n"
        f"💬 Total Messages: {len(messages)}\n\n"
        f"📝 Recent Messages:\n{df.to_string(index=False)}"
    )

@tool
def send_report_email(query: str) -> str:
    """Send the daily report to admin email."""
    return send_daily_report()

# ============================================
# 🧠 LANGCHAIN AGENT
# ============================================

langchain_model = ChatGoogleGenerativeAI(
    model="gemini-3.5-flash",
    google_api_key=gemini_key,
    temperature=0.3,
)

langchain_agent = create_agent(
    model=langchain_model,
    tools=[internet_search, get_report_data, send_report_email],
    system_prompt="""You are Apex AI - a professional, friendly Business Agent.

IMPORTANT RULES:
1. ONLY introduce yourself when user asks "who are you"
2. For off-topic questions, say "I only answer business-related questions"
3. For payment, suggest admin
4. Keep it short (max 50 words)
"""
)

def run_langchain_agent(user_input):
    try:
        result = langchain_agent.invoke({
            "messages": [{"role": "user", "content": user_input}]
        })
        
        messages = result.get("messages", [])
        if not messages:
            return "I couldn't generate a response."
        
        content = messages[-1].content
        
        if isinstance(content, str):
            return content
        if isinstance(content, list):
            parts = []
            for block in content:
                if isinstance(block, dict):
                    text = block.get("text")
                    if text:
                        parts.append(str(text))
                elif isinstance(block, str):
                    parts.append(block)
            if parts:
                return "\n".join(parts)
        
        return str(content)
    except Exception as e:
        return f"⚠️ Error: {str(e)}"

# ============================================
# 🤖 AI AGENT CLASS
# ============================================

class AIAgent:
    def __init__(self):
        self.memory = []
        self.user_info = {}
        self.intro_given = False

    def think(self, user_input):
        self.memory.append({"role": "user", "content": user_input})
        lower_input = user_input.lower()

        # Off-topic questions
        off_topic = ["weather", "birthday", "song", "movie", "recipe", "joke", "funny", "love", "relationship"]
        if any(word in lower_input for word in off_topic):
            return {
                "reply": "🌟 I'm Apex AI - Your Business Partner!\n\nI only answer business-related questions like:\n• 💻 Web Development\n• 🤖 AI Agents\n• 🎬 Video Editing\n• 📱 Automation\n\nHow can I help with your business? 😊",
                "should_connect": False
            }

        # Payment
        if "payment" in lower_input or "pay" in lower_input:
            return {
                "reply": "💎 **Payment & Pricing:**\n\nFor payment details, I'll connect you with our admin team.\n\n📞 **Talk to Admin:** http://localhost:8501/?admin=true\n\nOr click **Talk to Admin** button above! 🚀",
                "should_connect": True
            }

        # Identity
        if "who are you" in lower_input or "who is" in lower_input or "introduce" in lower_input:
            return {
                "reply": "🌟 **Hey! I'm Apex AI - your business buddy!** 🚀\n\nI'm a professional Business AI Agent designed to help you with:\n• 💻 Web Development\n• 🤖 Custom AI Agents\n• 🎬 Video Editing\n• 📱 Automation\n\nTell me what you want to build! 😊",
                "should_connect": False
            }

        agent_keywords = ["report", "data", "summary", "send", "email", "search", "find", "latest", "news"]
        
        if any(word in lower_input for word in agent_keywords):
            try:
                reply = run_langchain_agent(user_input)
                reply = reply.replace('Gemini', 'Apex AI').replace('Google', 'Apex AI')
                self.memory.append({"role": "assistant", "content": reply})
                should_connect = any(word in reply.lower() for word in ["admin", "talk", "connect"])
                return {"reply": reply, "should_connect": should_connect}
            except Exception:
                pass

        prompt = f"""
You are Apex AI - a friendly, professional Business Agent.

USER: {user_input}
NAME: {self.user_info.get('name', 'Friend')}

RULES:
1. DO NOT introduce yourself unless user asked "who are you"
2. Give a DIRECT, TO-THE-POINT answer
3. Use 1-2 emojis maximum
4. Keep it short (max 40 words)
5. Ask ONE follow-up question
6. For payments, suggest admin

Response (max 40 words):
"""
        
        reply = generate_ai_response(prompt)
        
        if reply:
            reply = reply.replace('Gemini', 'Apex AI').replace('Google', 'Apex AI')
            self.memory.append({"role": "assistant", "content": reply})
            should_connect = any(word in reply.lower() for word in ["admin", "talk", "connect"])
            return {"reply": reply, "should_connect": should_connect}
        else:
            return {
                "reply": "I can help with business solutions! What would you like to build today? 😊",
                "should_connect": True
            }

    def get_quick_topics(self):
        return [
            "Web Development",
            "AI Agents", 
            "Video Editing",
            "Automation"
        ]

# ============================================
# 🎨 UI - FORCE DARK THEME (STREAMLIT CLOUD)
# ============================================

st.markdown("""
<style>
    /* ✅ FORCE DARK THEME - STREAMLIT CLOUD */
    .stApp {
        background: radial-gradient(circle at top, #1e1b4b 0%, #0b0f19 80%) !important;
        color: #f8fafc !important;
    }
    
    .gradient-header {
        font-size: 2.5rem !important;
        font-weight: 800 !important;
        background: linear-gradient(90deg, #38bdf8, #818cf8, #c084fc) !important;
        -webkit-background-clip: text !important;
        -webkit-text-fill-color: transparent !important;
        text-align: center !important;
        padding: 10px 0 !important;
    }
    
    .user-card {
        background: rgba(30, 41, 59, 0.8) !important;
        border: 1px solid #38bdf8 !important;
        border-radius: 16px !important;
        padding: 20px !important;
        backdrop-filter: blur(10px) !important;
        box-shadow: 0 0 30px rgba(56, 189, 248, 0.1) !important;
    }
    
    .chat-container {
        background: rgba(15, 23, 42, 0.6) !important;
        border: 2px solid #6366f1 !important;
        border-radius: 20px !important;
        padding: 20px !important;
        box-shadow: 0 0 40px rgba(99, 102, 241, 0.2) !important;
        backdrop-filter: blur(5px) !important;
        max-height: 500px !important;
        overflow-y: auto !important;
        margin-bottom: 15px !important;
        min-height: 100px !important;
    }
    
    .user-msg {
        background: linear-gradient(135deg, #1e3a5f, #2563eb) !important;
        border-left: 4px solid #60a5fa !important;
        padding: 12px 18px !important;
        border-radius: 12px !important;
        margin: 8px 0 !important;
        box-shadow: 0 4px 20px rgba(37, 99, 235, 0.3) !important;
        color: #f0f9ff !important;
        animation: slideIn 0.3s ease !important;
    }
    
    .bot-msg {
        background: linear-gradient(135deg, #1a1a4e, #7c3aed) !important;
        border-left: 4px solid #a78bfa !important;
        padding: 14px 22px !important;
        border-radius: 12px !important;
        margin: 8px 0 !important;
        line-height: 1.8 !important;
        box-shadow: 0 4px 20px rgba(124, 58, 237, 0.3) !important;
        color: #f5f3ff !important;
        animation: slideIn 0.3s ease !important;
    }
    
    .admin-user-msg {
        background: linear-gradient(135deg, #4a1a2e, #db2777) !important;
        border-left: 4px solid #f472b6 !important;
        padding: 12px 18px !important;
        border-radius: 12px !important;
        margin: 8px 0 !important;
        box-shadow: 0 4px 20px rgba(219, 39, 119, 0.3) !important;
        color: #fdf2f8 !important;
        animation: slideIn 0.3s ease !important;
    }
    
    .admin-reply-msg {
        background: linear-gradient(135deg, #1a3a2e, #10b981) !important;
        border-left: 4px solid #34d399 !important;
        padding: 12px 18px !important;
        border-radius: 12px !important;
        margin: 8px 0 !important;
        box-shadow: 0 4px 20px rgba(16, 185, 129, 0.3) !important;
        color: #ecfdf5 !important;
        animation: slideIn 0.3s ease !important;
    }
    
    .admin-chat-box {
        background: linear-gradient(135deg, #fdf2f8, #fce7f3) !important;
        border: 3px solid #f472b6 !important;
        border-radius: 20px !important;
        padding: 25px !important;
        box-shadow: 0 0 50px rgba(244, 114, 182, 0.3) !important;
    }
    
    .admin-reply-box {
        background: rgba(30, 41, 59, 0.5) !important;
        border: 1px solid #c084fc !important;
        border-radius: 12px !important;
        padding: 15px !important;
        margin: 10px 0 !important;
    }
    
    /* ✅ ALL BUTTONS - FIXED */
    .stButton button {
        background: linear-gradient(135deg, #1e293b, #334155) !important;
        color: #f8fafc !important;
        border: 1px solid #38bdf8 !important;
        border-radius: 30px !important;
        padding: 10px 20px !important;
        font-weight: 600 !important;
        width: 100% !important;
        box-shadow: 0 2px 10px rgba(0,0,0,0.3) !important;
        transition: all 0.3s ease !important;
    }
    
    .stButton button:hover {
        background: linear-gradient(135deg, #2563eb, #7c3aed) !important;
        box-shadow: 0 0 30px rgba(99, 102, 241, 0.3) !important;
        transform: translateY(-2px) !important;
        border-color: #a78bfa !important;
    }
    
    /* TALK TO ADMIN */
    .stButton button[data-testid="baseButton-secondary"] {
        background: linear-gradient(135deg, #f472b6, #ec4899) !important;
        border: none !important;
        box-shadow: 0 4px 20px rgba(244, 114, 182, 0.4) !important;
        color: white !important;
    }
    
    .stButton button[data-testid="baseButton-secondary"]:hover {
        background: linear-gradient(135deg, #ec4899, #db2777) !important;
        box-shadow: 0 4px 30px rgba(244, 114, 182, 0.6) !important;
    }
    
    /* NOTIFY ADMIN */
    .stButton button[data-testid="baseButton-primary"] {
        background: linear-gradient(135deg, #f59e0b, #d97706) !important;
        border: none !important;
        box-shadow: 0 4px 20px rgba(245, 158, 11, 0.3) !important;
        color: white !important;
    }
    
    .stButton button[data-testid="baseButton-primary"]:hover {
        background: linear-gradient(135deg, #d97706, #b45309) !important;
        box-shadow: 0 4px 30px rgba(245, 158, 11, 0.5) !important;
        transform: translateY(-2px) !important;
    }
    
    /* SEND BUTTON */
    .stButton button[data-testid="baseButton-formSubmit"] {
        background: linear-gradient(135deg, #2563eb, #7c3aed) !important;
        border: none !important;
        box-shadow: 0 4px 20px rgba(99, 102, 241, 0.4) !important;
        color: white !important;
    }
    
    .stButton button[data-testid="baseButton-formSubmit"]:hover {
        background: linear-gradient(135deg, #1d4ed8, #6d28d9) !important;
        box-shadow: 0 4px 30px rgba(99, 102, 241, 0.6) !important;
    }
    
    @keyframes slideIn {
        from { opacity: 0; transform: translateY(15px) scale(0.98); }
        to { opacity: 1; transform: translateY(0) scale(1); }
    }
    
    .stTextInput input {
        background: rgba(30, 41, 59, 0.8) !important;
        border: 2px solid #6366f1 !important;
        border-radius: 30px !important;
        padding: 12px 20px !important;
        color: white !important;
        font-size: 16px !important;
    }
    
    .stTextInput input:focus {
        border-color: #a78bfa !important;
        box-shadow: 0 0 25px rgba(99, 102, 241, 0.3) !important;
    }
    
    .stTextArea textarea {
        background: rgba(30, 41, 59, 0.8) !important;
        border: 2px solid #6366f1 !important;
        border-radius: 12px !important;
        color: white !important;
        font-size: 14px !important;
    }
    
    .stTextArea textarea:focus {
        border-color: #a78bfa !important;
        box-shadow: 0 0 25px rgba(99, 102, 241, 0.3) !important;
    }
    
    #MainMenu {visibility: hidden !important;}
    footer {visibility: hidden !important;}
    header {visibility: hidden !important;}
</style>
""", unsafe_allow_html=True)

# ============================================
# 👤 MAIN APP
# ============================================

query_params = st.query_params
is_admin_mode = query_params.get("admin", "false").lower() == "true"

user_email = query_params.get("email", "Not Provided")
user_name = query_params.get("username", "Guest")
user_age = query_params.get("age", "N/A")
user_country = query_params.get("country", "N/A")

if user_email != "Not Provided":
    existing_user = get_user_by_email(user_email)
    if existing_user:
        user_name = existing_user.get('name', user_name)
        user_age = existing_user.get('age', user_age)
        user_country = existing_user.get('country', user_country)

# ============================================
# 👨‍💼 ADMIN VIEW
# ============================================

if is_admin_mode:
    st.markdown('<div class="gradient-header">🔐 Admin Panel</div>', unsafe_allow_html=True)
    
    if 'admin_logged_in' not in st.session_state:
        st.session_state.admin_logged_in = False
    
    if not st.session_state.admin_logged_in:
        password = st.text_input("Enter Admin Password:", type="password")
        
        if st.button("Login"):
            if password == "admin123":
                st.session_state.admin_logged_in = True
                st.success("✅ Access Granted!")
                st.balloons()
                st.rerun()
            else:
                st.error("❌ Wrong password!")
    else:
        st.success("👋 Welcome Admin!")
        
        if st.button("🚪 Logout"):
            st.session_state.admin_logged_in = False
            st.rerun()
        
        users = load_users()
        messages = load_messages()
        admin_replies = load_admin_replies()
        admin_chat_history = load_admin_chat_history()
        
        col1, col2, col3 = st.columns(3)
        with col1: st.metric("👥 Users", len(users))
        with col2: st.metric("⏳ Pending", len([u for u in users if u.get('status') == 'pending']))
        with col3: st.metric("💬 Messages", len(messages))
        
        st.markdown("---")
        
        st.subheader("💬 Admin Chat History")
        
        if admin_chat_history:
            for chat in admin_chat_history[-20:]:
                if chat.get('sender') == 'user':
                    st.markdown(f'<div class="admin-user-msg"><b>👤 {chat.get("user_name", "User")}:</b> {chat["message"]}</div>', unsafe_allow_html=True)
                else:
                    st.markdown(f'<div class="admin-reply-msg"><b>👑 Admin:</b> {chat["message"]}</div>', unsafe_allow_html=True)
        else:
            st.info("No admin chat history yet.")
        
        st.markdown("---")
        
        st.subheader("📊 Agent Report Generator")
        col1, col2 = st.columns(2)
        with col1:
            if st.button("📊 View Today's Data", use_container_width=True):
                df = get_todays_report_data()
                st.dataframe(df, use_container_width=True)
        with col2:
            if st.button("📧 Send Report to Email", use_container_width=True):
                with st.spinner("Sending report..."):
                    result = send_daily_report()
                    st.success(result)
                    st.balloons()
        
        st.markdown("---")
        
        tab1, tab2, tab3 = st.tabs(["👥 Users", "💬 Messages & Reply", "📧 Sent Replies"])
        
        with tab1:
            for user in users:
                with st.expander(f"📌 {user['name']} - {user['email']}"):
                    st.write(f"**Age:** {user.get('age', 'N/A')}")
                    st.write(f"**Country:** {user.get('country', 'N/A')}")
                    st.write(f"**Status:** {user.get('status', 'pending').upper()}")
                    if st.button(f"✅ Mark Contacted", key=f"c_{user['email']}"):
                        user['status'] = 'contacted'
                        save_user(user)
                        st.success("✅ Status updated!")
                        st.rerun()
        
        with tab2:
            st.subheader("💬 Messages - Reply to Users")
            
            col1, col2 = st.columns([3, 1])
            with col2:
                if st.button("🗑️ Clear All History", use_container_width=True):
                    clear_all_history()
                    st.success("✅ All history cleared!")
                    st.balloons()
                    st.rerun()
            
            st.markdown("---")
            
            if messages:
                for idx, msg in enumerate(messages[::-1]):
                    with st.expander(f"📩 From: {msg.get('name', 'User')} - {msg.get('timestamp', '')[:16]}"):
                        st.markdown(f"""
                        <div class="admin-reply-box">
                            <b>👤 From:</b> {msg.get('name', 'User')} ({msg.get('user', 'email')})<br>
                            <b>💬 Query:</b> {msg.get('message', '')}<br>
                            <b>🤖 Agent Response:</b> {msg.get('response', '')[:150]}...
                        </div>
                        """, unsafe_allow_html=True)
                        
                        st.markdown("**✍️ Reply to this user:**")
                        
                        with st.form(key=f"reply_form_{idx}", clear_on_submit=True):
                            reply_text = st.text_area(
                                "",
                                placeholder="Type your reply and press Enter...",
                                key=f"reply_{idx}",
                                height=80,
                                label_visibility="collapsed"
                            )
                            
                            col1, col2 = st.columns([3, 1])
                            with col2:
                                send_reply_btn = st.form_submit_button("📤 Send", use_container_width=True)
                            
                            if send_reply_btn and reply_text:
                                save_admin_chat_history({
                                    "sender": "admin",
                                    "user_name": msg.get('name', 'User'),
                                    "user_email": msg.get('user', ''),
                                    "message": reply_text,
                                    "timestamp": str(datetime.datetime.now())
                                })
                                
                                save_message({
                                    "user": msg.get('user', ''),
                                    "name": msg.get('name', 'User'),
                                    "message": "📩 Admin Reply: " + reply_text,
                                    "response": "✅ Admin has replied to you!",
                                    "timestamp": str(datetime.datetime.now())
                                })
                                
                                save_admin_reply({
                                    "user": msg.get('user', ''),
                                    "user_name": msg.get('name', ''),
                                    "admin_reply": reply_text,
                                    "timestamp": str(datetime.datetime.now())
                                })
                                
                                send_gmail_notification(
                                    msg.get('user', ''),
                                    f"📩 Reply from Admin - Apex AI",
                                    f"Hi {msg.get('name', 'User')},\n\nAdmin Reply:\n{reply_text}\n\nBest regards,\nApex AI Team"
                                )
                                
                                st.success("✅ Reply sent via email!")
                                st.balloons()
                                st.rerun()
            else:
                st.info("No messages yet")
        
        with tab3:
            st.subheader("📧 Admin Reply History")
            if admin_replies:
                for reply in admin_replies[::-1][:10]:
                    st.markdown(f"""
                    <div class="admin-reply-box">
                        <b>To:</b> {reply.get('user_name', 'User')}<br>
                        <b>Reply:</b> {reply.get('admin_reply', '')[:100]}...<br>
                        <small style="color:#94a3b8;">{reply.get('timestamp', '')}</small>
                    </div>
                    """, unsafe_allow_html=True)
            else:
                st.info("No replies sent yet")
    
    st.stop()

# ============================================
# 👤 USER VIEW
# ============================================

user_history = []
if user_email != "Not Provided":
    user_history = get_user_messages(user_email)

if "chat_history" not in st.session_state:
    if user_history:
        st.session_state.chat_history = user_history
    else:
        st.session_state.chat_history = []

if "agent" not in st.session_state:
    st.session_state.agent = AIAgent()
    st.session_state.agent.user_info = {
        "name": user_name,
        "email": user_email,
        "age": user_age,
        "country": user_country
    }
if "show_admin_chat" not in st.session_state:
    st.session_state.show_admin_chat = False

st.markdown("""
<div style="text-align: center; padding: 20px 0;">
    <div class="gradient-header">Apex AI Business Agent</div>
    <p style="color: #94a3b8; margin-top: 5px;">✨ Your AI Business Partner</p>
</div>
""", unsafe_allow_html=True)

col1, col2, col3 = st.columns([2, 1, 1])

with col1:
    if user_email == "Not Provided" or user_name == "Guest":
        display_name = "Guest User"
        display_email = "Not Signed In"
        display_country = "N/A"
        avatar_letter = "G"
    else:
        display_name = user_name
        display_email = user_email
        display_country = user_country
        avatar_letter = user_name[0].upper() if user_name else "G"
    
    st.markdown(f"""
    <div class="user-card">
        <div style="display: flex; align-items: center; gap: 15px;">
            <div style="background: linear-gradient(135deg, #38bdf8, #c084fc); 
                        width: 55px; height: 55px; border-radius: 50%; 
                        display: flex; align-items: center; justify-content: center; 
                        font-size: 24px; font-weight: bold; color: white;">
                {avatar_letter}
            </div>
            <div>
                <b style="font-size: 1.3rem;">👤 {display_name}</b><br>
                <span style="color: #94a3b8;">✉️ {display_email} | 🌍 {display_country}</span>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

with col2:
    if st.button("💖 Talk to Admin", use_container_width=True):
        st.session_state.show_admin_chat = not st.session_state.show_admin_chat

with col3:
    if st.button("📧 Notify Admin", use_container_width=True):
        send_gmail_notification(
            GMAIL_EMAIL,
            f"🔔 User Request: {user_name}",
            f"User {user_name} ({user_email}) wants to connect!"
        )
        st.success("✅ Admin notified!")
        st.balloons()

if st.session_state.show_admin_chat:
    st.markdown("""
    <div class="admin-chat-box">
        <div style="display: flex; align-items: center; gap: 15px; margin-bottom: 15px;">
            <div style="background: linear-gradient(135deg, #f472b6, #ec4899); 
                        width: 50px; height: 50px; border-radius: 50%; 
                        display: flex; align-items: center; justify-content: center; 
                        font-size: 28px; color: white;">
                💖
            </div>
            <div>
                <h3 style="color: #be185d; margin: 0;">✨ Talk to Admin</h3>
                <p style="color: #9d174d; margin: 0; font-size: 14px;">We're here to help! 💕</p>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    admin_message = st.text_area("💬 Type your message...", placeholder="Hi! I'd like to discuss my project...", key="admin_msg")
    
    if st.button("📤 Send to Admin", key="send_admin"):
        if admin_message:
            save_admin_chat_history({
                "sender": "user",
                "user_name": user_name,
                "user_email": user_email,
                "message": admin_message,
                "timestamp": str(datetime.datetime.now())
            })
            
            send_gmail_notification(
                GMAIL_EMAIL,
                f"💌 Admin Message: {user_name}",
                f"💖 New Message from {user_name}!\n\n📧 Email: {user_email}\n💬 Message: {admin_message}"
            )
            st.success("✅ Message sent to Admin! They'll reply soon! 💕")
            st.balloons()
            st.session_state.show_admin_chat = False
            st.rerun()

st.markdown("---")

col1, col2 = st.columns([3, 1])
with col1:
    st.markdown("### 💬 Chat with Apex AI")
with col2:
    if st.button("🗑️ Clear Chat", use_container_width=True):
        st.session_state.chat_history = []
        if user_email != "Not Provided":
            clear_user_history(user_email)
        st.success("✅ Chat cleared!")
        st.rerun()

with st.container():
    st.markdown('<div class="chat-container">', unsafe_allow_html=True)
    
    if st.session_state.chat_history:
        for chat in st.session_state.chat_history:
            if isinstance(chat, dict):
                if 'user_query' in chat and 'bot_response' in chat:
                    st.markdown(f'<div class="user-msg"><b>👤 You:</b> {chat["user_query"]}</div>', unsafe_allow_html=True)
                    st.markdown(f'<div class="bot-msg"><b>🤖 Apex AI:</b><br>{chat["bot_response"]}</div>', unsafe_allow_html=True)
                elif 'message' in chat and 'response' in chat:
                    st.markdown(f'<div class="user-msg"><b>👤 You:</b> {chat["message"]}</div>', unsafe_allow_html=True)
                    st.markdown(f'<div class="bot-msg"><b>🤖 Apex AI:</b><br>{chat["response"]}</div>', unsafe_allow_html=True)
    else:
        st.info("🌟 Start a conversation with Apex AI!")
    
    st.markdown('</div>', unsafe_allow_html=True)

st.markdown("### ⚡ Quick Topics")
qcols = st.columns(4)
quick_topics = st.session_state.agent.get_quick_topics()
icons = ["💻 ", "🤖 ", "🎬 ", "📱 "]

selected_topic = None
for idx, col in enumerate(qcols):
    with col:
        if st.button(f"{icons[idx]}{quick_topics[idx]}", key=f"topic_{idx}", use_container_width=True):
            selected_topic = quick_topics[idx]

st.markdown("### 💬 Type your message")

with st.form(key="chat_form", clear_on_submit=True):
    col1, col2 = st.columns([4, 1])
    with col1:
        user_input = st.text_input(
            "",
            placeholder="💬 Type your message and press Enter...",
            key="chat_input",
            label_visibility="collapsed"
        )
    with col2:
        send_btn = st.form_submit_button("🚀 Send", use_container_width=True)
    
    final_input = selected_topic if selected_topic else (user_input if send_btn else None)
    
    if final_input:
        with st.spinner("🤖 Thinking..."):
            try:
                response = st.session_state.agent.think(final_input)
                
                st.session_state.chat_history.append({
                    "user_query": final_input,
                    "bot_response": response['reply']
                })
                
                save_message({
                    "user": user_email,
                    "name": user_name,
                    "message": final_input,
                    "response": response['reply'],
                    "timestamp": str(datetime.datetime.now())
                })
                
                if user_email != "Not Provided":
                    existing = get_user_by_email(user_email)
                    is_new_user = (existing is None)
                    
                    if is_new_user:
                        send_gmail_notification(
                            user_email,
                            "🎉 Welcome to Apex AI Solutions!",
                            f"""
                            🌟 Hi {user_name}!
                            
                            Welcome to Apex AI Solutions! 🚀
                            
                            ✨ We can help you with:
                            • 💻 Web Development
                            • 🤖 AI Agents
                            • 🎬 Video Editing  
                            • 📱 Automation
                            
                            Let's make something amazing! 💪
                            
                            Best,
                            Apex AI Team
                            """
                        )
                        
                        send_gmail_notification(
                            GMAIL_EMAIL,
                            f"🔔 New User Sign-In: {user_name}",
                            f"""
                            New user signed in!
                            
                            Name: {user_name}
                            Email: {user_email}
                            Age: {user_age}
                            Country: {user_country}
                            Time: {datetime.datetime.now()}
                            """
                        )
                        
                        st.toast("🎉 Welcome email sent!", icon="🎉")
                
                save_user({
                    "name": user_name,
                    "email": user_email,
                    "age": user_age,
                    "country": user_country,
                    "signup_time": str(datetime.datetime.now()),
                    "status": "pending"
                })
                
                if response.get('should_connect', False):
                    send_gmail_notification(
                        GMAIL_EMAIL,
                        f"💬 User wants admin: {user_name}",
                        f"User: {user_name}\nEmail: {user_email}\nQuery: {final_input}"
                    )
                    st.info("💖 Admin notified! They'll reach out soon!")
                    st.balloons()
                
                st.rerun()
                
            except Exception as e:
                st.error(f"❌ Error: {e}")
                st.info("💡 Make sure all secrets are set in Streamlit Cloud")

st.markdown("---")
st.markdown("""
<div style="text-align: center; color: #64748b; padding: 10px;">
    🚀 Made with ❤️ by <b>TAQWA</b> | Apex AI Solutions
</div>
""", unsafe_allow_html=True)