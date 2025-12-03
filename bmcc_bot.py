import streamlit as st
import requests
import json

# --- CONFIGURATION ---
GEMINI_MODEL = 'gemini-2.5-flash-preview-09-2025'
API_URL = f"https://generativelanguage.googleapis.com/v1beta/models/{GEMINI_MODEL}:generateContent?key="

st.set_page_config(page_title="BMCC International Guide", page_icon="🗽", layout="centered")

# --- KNOWLEDGE BASE (Simulating Scraped Data) ---
# This is the "Brain" of the bot. You can update this text with info from the BMCC website.
BMCC_KNOWLEDGE_BASE = """
GENERAL BMCC RULES:
- BMCC is a CUNY college. All applications go through CUNY.
- Application Fee: $65.
- English Proficiency: TOEFL (45), IELTS (5.0), Duolingo (75), or PTE (39).
- Exempt from English test if: From English-speaking country or completed English Comp I at a US college with C or better.

TRANSCRIPT EVALUATION (For education outside US):
- Must use a NACES member agency (like WES, ECE, Josef Silny).
- Required for Domestic students educated abroad AND International students.

SEVIS TRANSFER (For F-1 students inside US):
- You must get an acceptance letter first.
- Then, complete the "Transfer Release Form".
- Your current school must release your SEVIS record to BMCC.

CHANGE OF STATUS (B1/B2/J1 to F-1):
- BMCC does NOT assist with the legal change of status application (Form I-539).
- BMCC ONLY provides the Form I-20.
- Students must consult an immigration lawyer.
- You cannot study while on B1/B2 status.

DEADLINES:
- Fall: Feb 1 (Priority).
- Spring: Sep 15 (Priority).
"""

# --- SESSION STATE INITIALIZATION ---
if 'step' not in st.session_state:
    st.session_state.step = 1
if 'profile' not in st.session_state:
    st.session_state.profile = {
        'type': None,      # Freshman, Transfer, Domestic-Abroad
        'location': None,  # Inside US, Outside US
        'visa': None       # F1, B1/B2, None, etc.
    }
if 'messages' not in st.session_state:
    st.session_state.messages = []

# --- HELPER: Gemini API Call ---
def get_ai_response(user_query, profile):
    try:
        api_key = st.secrets["GEMINI_API_KEY"]
    except KeyError:
        return "Error: API Key missing."

    # Construct the System Prompt based on the user's specific profile
    profile_summary = f"User Profile: {profile['type']}, Currently {profile['location']}"
    if profile['visa']:
        profile_summary += f", Visa Status: {profile['visa']}"

    system_instruction = (
        "You are an expert International Admissions Advisor for BMCC (CUNY). "
        f"CONTEXT: {BMCC_KNOWLEDGE_BASE}\n\n"
        f"CURRENT USER PROFILE: {profile_summary}\n\n"
        "RULES:"
        "1. Answer ONLY based on the context and the user's profile."
        "2. Provide answers in clear, simple Step 1, Step 2, Step 3 format."
        "3. If the user is B1/B2/J1 trying to change status, EXPLICITLY state that BMCC only provides the I-20 and they MUST consult an immigration lawyer for the status change."
        "4. If the user is F-1 Transfer in US, mention SEVIS Transfer."
        "5. Keep it concise and professional."
    )

    payload = {
        "contents": [{"role": "user", "parts": [{"text": user_query}]}],
        "systemInstruction": {"parts": [{"text": system_instruction}]}
    }

    try:
        response = requests.post(
            API_URL + api_key,
            headers={'Content-Type': 'application/json'},
            data=json.dumps(payload),
            timeout=30
        )
        if response.status_code == 200:
            return response.json()['candidates'][0]['content']['parts'][0]['text']
        else:
            return "Sorry, I'm having trouble connecting to the server."
    except Exception as e:
        return f"Error: {e}"

# --- UI: RESET BUTTON ---
with st.sidebar:
    st.header("Applicant Profile")
    if st.session_state.step > 3:
        st.success("✅ Profile Complete")
        st.write(f"**Type:** {st.session_state.profile['type']}")
        st.write(f"**Location:** {st.session_state.profile['location']}")
        if st.session_state.profile['visa']:
            st.write(f"**Visa:** {st.session_state.profile['visa']}")
        
        if st.button("Reset Profile"):
            st.session_state.step = 1
            st.session_state.profile = {'type': None, 'location': None, 'visa': None}
            st.session_state.messages = []
            st.rerun()

# --- UI: PROFILE WIZARD (Steps 1-3) ---
st.title("🗽 BMCC International Assistant")

if st.session_state.step == 1:
    st.subheader("Step 1: What type of applicant are you?")
    col1, col2, col3 = st.columns(3)
    
    if col1.button("International Freshman", use_container_width=True):
        st.session_state.profile['type'] = "International Freshman"
        st.session_state.step = 2
        st.rerun()
        
    if col2.button("International Transfer", use_container_width=True):
        st.session_state.profile['type'] = "International Transfer"
        st.session_state.step = 2
        st.rerun()
        
    if col3.button("Domestic (Educated Abroad)", use_container_width=True):
        st.session_state.profile['type'] = "Domestic Student (Educated Outside US)"
        # Domestic students don't need visa checks usually, but let's ask location to be safe
        st.session_state.step = 2 
        st.rerun()

elif st.session_state.step == 2:
    st.subheader("Step 2: Where are you currently located?")
    col1, col2 = st.columns(2)
    
    if col1.button("I am inside the US", use_container_width=True):
        st.session_state.profile['location'] = "Inside the US"
        st.session_state.step = 3
        st.rerun()
        
    if col2.button("I am outside the US", use_container_width=True):
        st.session_state.profile['location'] = "Outside the US"
        st.session_state.profile['visa'] = "None (Needs F-1 Visa)"
        st.session_state.step = 4 # Skip visa check
        st.rerun()

elif st.session_state.step == 3:
    st.subheader("Step 3: What is your current Visa Status?")
    
    options = ["F-1 Student", "B-1/B-2 Visitor", "J-1 Exchange", "Other / Not Sure"]
    
    for option in options:
        if st.button(option, use_container_width=True):
            st.session_state.profile['visa'] = option
            st.session_state.step = 4
            st.rerun()

# --- UI: CHAT INTERFACE (Step 4) ---
elif st.session_state.step == 4:
    # Initial Greeting (Only runs once)
    if not st.session_state.messages:
        greeting = f"Hello! I see you are an **{st.session_state.profile['type']}** located **{st.session_state.profile['location']}**."
        if st.session_state.profile['visa'] == "F-1 Student":
            greeting += " Since you are already on F-1, I can help you with the **SEVIS Transfer** process."
        elif st.session_state.profile['visa'] in ["B-1/B-2 Visitor", "J-1 Exchange"]:
            greeting += " Since you are on a visitor visa, please note that changing status requires careful legal planning."
        
        greeting += " How can I help you today?"
        st.session_state.messages.append({"role": "assistant", "content": greeting})

    # Display Chat
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    # Chat Input
    if prompt := st.chat_input("Ask about application steps, documents, or deadlines..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant"):
            with st.spinner("Consulting the knowledge base..."):
                response = get_ai_response(prompt, st.session_state.profile)
                st.markdown(response)
                st.session_state.messages.append({"role": "assistant", "content": response})
