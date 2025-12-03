import streamlit as st
import requests
import json

# --- CONFIGURATION ---
GEMINI_MODEL = 'gemini-2.5-flash-preview-09-2025'
# Note: Added https:// to ensure the URL is correct
API_URL = f"https://generativelanguage.googleapis.com/v1beta/models/{GEMINI_MODEL}:generateContent?key="

st.set_page_config(page_title="BMCC International Guide", page_icon="🗽", layout="centered")

# --- KNOWLEDGE BASE ---
BMCC_KNOWLEDGE_BASE = """
GENERAL BMCC RULES:
- BMCC is a CUNY college. Applications go through CUNY.
- Application Fee: $65.
- English Proficiency: TOEFL (45), IELTS (5.0), Duolingo (75), or PTE (39).
- Exempt from English test if: From English-speaking country or completed English Comp I at a US college with C or better.

TRANSCRIPT EVALUATION (For education outside US):
- Must use a NACES member agency (like WES, ECE, Josef Silny).
- Required for all students with non-US transcripts.

SEVIS TRANSFER (For F-1 Students Currently in US):
- ACADEMIC STATUS: If coming from ESL school -> Apply as Freshman. If coming from University -> Apply as Transfer.
- IMMIGRATION STATUS: Both must do "SEVIS Transfer".
- Process: 1. Get Acceptance Letter. 2. Fill out Transfer Release Form. 3. Current school releases SEVIS record.

CHANGE OF STATUS (B1/B2/J1 to F-1):
- BMCC does NOT assist with the legal application (Form I-539).
- BMCC ONLY provides the Form I-20 labeled "Initial Attendance - Change of Status".
- User must consult an immigration lawyer.
- B1/B2 holders CANNOT study until status is officially changed to F-1.

DEADLINES:
- Fall: Feb 1 (Priority).
- Spring: Sep 15 (Priority).
"""

# --- SESSION STATE INITIALIZATION ---
if 'step' not in st.session_state:
    st.session_state.step = 1
if 'profile' not in st.session_state:
    st.session_state.profile = {
        'location': None,       # Inside/Outside US
        'visa_status': None,    # F-1, B-1/B-2, None
        'school_type': None,    # ESL vs University (for F-1)
        'academic_type': None,  # Freshman vs Transfer
        'immigration_needs': None # SEVIS Transfer vs New Visa vs Change of Status
    }
if 'messages' not in st.session_state:
    st.session_state.messages = []

# --- HELPER: Gemini API Call ---
def get_ai_response(user_query, profile):
    try:
        api_key = st.secrets["GEMINI_API_KEY"]
    except KeyError:
        return "Error: API Key missing. Please set it in Streamlit Secrets."

    profile_summary = (
        f"User is {profile['location']}. "
        f"Visa Status: {profile['visa_status']}. "
        f"Academic Type: {profile['academic_type']}. "
        f"Immigration Need: {profile['immigration_needs']}."
    )

    system_instruction = (
        "You are an expert International Admissions Advisor for BMCC (CUNY). "
        f"CONTEXT: {BMCC_KNOWLEDGE_BASE}\n\n"
        f"USER PROFILE: {profile_summary}\n\n"
        "RULES:"
        "1. Answer ONLY based on the context and user profile."
        "2. If user is F-1 at an ESL school, treat them as an ACADEMIC FRESHMAN but explain the SEVIS TRANSFER process."
        "3. If user is B1/B2/J1, EXPLICITLY state BMCC only provides the I-20 and they MUST consult a lawyer for status change."
        "4. Keep answers concise, friendly, and structured (Step 1, Step 2, Step 3)."
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
            return f"Error connecting to AI: {response.status_code}"
    except Exception as e:
        return f"Error: {e}"

# --- HELPER: Handle Button Click ---
def handle_suggestion(question):
    st.session_state.messages.append({"role": "user", "content": question})
    # Force a rerun so the chat updates immediately, then the AI responds
    st.rerun()

# --- UI: RESET BUTTON ---
with st.sidebar:
    st.header("Applicant Profile")
    if st.session_state.step > 4:
        p = st.session_state.profile
        st.success("✅ Profile Complete")
        st.write(f"**Loc:** {p['location']}")
        st.write(f"**Visa:** {p['visa_status']}")
        st.write(f"**Academic:** {p['academic_type']}")
        st.info(f"**Action:** {p['immigration_needs']}")
        
        if st.button("Start Over"):
            st.session_state.step = 1
            st.session_state.messages = []
            st.rerun()

# --- UI: PROFILE WIZARD ---
st.title("🗽 BMCC International Assistant")

if st.session_state.step == 1:
    st.subheader("Step 1: Where are you currently located?")
    col1, col2 = st.columns(2)
    
    if col1.button("I am Inside the US", use_container_width=True):
        st.session_state.profile['location'] = "Inside US"
        st.session_state.step = 2
        st.rerun()
    
    if col2.button("I am Outside the US", use_container_width=True):
        st.session_state.profile['location'] = "Outside US"
        st.session_state.profile['visa_status'] = "None"
        st.session_state.profile['immigration_needs'] = "Apply for F-1 Visa"
        st.session_state.step = 3 # Go to Education check
        st.rerun()

elif st.session_state.step == 2: # Inside US Flow
    st.subheader("Step 2: What is your current Visa Status?")
    col1, col2 = st.columns(2)
    
    if col1.button("F-1 Student", use_container_width=True):
        st.session_state.profile['visa_status'] = "F-1 Student"
        st.session_state.profile['immigration_needs'] = "SEVIS Transfer"
        st.session_state.step = 2.5 # Special F-1 check
        st.rerun()
        
    if col2.button("B-1 / B-2 (Visitor)", use_container_width=True):
        st.session_state.profile['visa_status'] = "B-1/B-2 Visitor"
        st.session_state.profile['immigration_needs'] = "Change of Status (Requires Lawyer)"
        st.session_state.step = 3 # Go to Education check
        st.rerun()
        
    col3, col4 = st.columns(2)
    if col3.button("J-1 (Exchange)", use_container_width=True):
        st.session_state.profile['visa_status'] = "J-1 Exchange"
        st.session_state.profile['immigration_needs'] = "Change of Status (Requires Lawyer)"
        st.session_state.step = 3
        st.rerun()
        
    if col4.button("Other / Not Sure", use_container_width=True):
        st.session_state.profile['visa_status'] = "Other"
        st.session_state.profile['immigration_needs'] = "Consult International Office"
        st.session_state.step = 3
        st.rerun()

elif st.session_state.step == 2.5: # F-1 Specific Flow
    st.subheader("Step 2b: What type of school do you attend?")
    st.info("This determines if you apply as a Transfer student or a Freshman.")
    
    if st.button("I attend a College or University", use_container_width=True):
        st.session_state.profile['school_type'] = "University"
        st.session_state.profile['academic_type'] = "International Transfer"
        st.session_state.step = 5 # Done
        st.rerun()
        
    if st.button("I attend an ESL / Language School", use_container_width=True):
        st.session_state.profile['school_type'] = "ESL School"
        st.session_state.profile['academic_type'] = "International Freshman" # Key Logic
        st.session_state.step = 5 # Done
        st.rerun()

elif st.session_state.step == 3: # General Education Check (Outside US or B1/B2)
    st.subheader("Step 3: What is your education history?")
    
    if st.button("I have High School / Secondary School only", use_container_width=True):
        st.session_state.profile['academic_type'] = "International Freshman"
        st.session_state.step = 5
        st.rerun()
        
    if st.button("I have attended some University (Inside or Outside US)", use_container_width=True):
        st.session_state.profile['academic_type'] = "International Transfer"
        st.session_state.step = 5
        st.rerun()

# --- UI: CHAT INTERFACE ---
elif st.session_state.step == 5:
    # 1. Initial Greeting
    if not st.session_state.messages:
        p = st.session_state.profile
        greeting = f"Welcome! Based on your answers, you are an **{p['academic_type']}**."
        
        if p['visa_status'] == 'F-1 Student':
            greeting += " Since you are on F-1, I can guide you through the **SEVIS Transfer** process."
        elif p['location'] == 'Outside US':
            greeting += " I can help you with the application and **F-1 Visa Interview** steps."
        elif "Change of Status" in str(p['immigration_needs']):
            greeting += " ⚠️ **Important:** Since you are on a visitor visa, you will likely need a **Change of Status**. BMCC can provide the I-20, but you must work with a lawyer for the legal process."
            
        st.session_state.messages.append({"role": "assistant", "content": greeting})

    # 2. Display Chat History
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    # 3. Generate Logic for Last Message
    if st.session_state.messages and st.session_state.messages[-1]["role"] == "user":
        user_query = st.session_state.messages[-1]["content"]
        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                response = get_ai_response(user_query, st.session_state.profile)
                st.markdown(response)
                st.session_state.messages.append({"role": "assistant", "content": response})
        st.rerun() # Rerun to show buttons below the new response

    # 4. Suggested Questions (Buttons)
    # Only show if the last message was from the assistant
    if st.session_state.messages and st.session_state.messages[-1]["role"] == "assistant":
        st.write("---")
        st.caption("Suggested Questions:")
        cols = st.columns(3)
        
        p = st.session_state.profile
        
        # Dynamic Button Logic
        if p['immigration_needs'] == "SEVIS Transfer":
            if cols[0].button("How do I transfer my SEVIS?"):
                handle_suggestion("What are the steps to transfer my SEVIS record to BMCC?")
        elif "Change of Status" in str(p['immigration_needs']):
            if cols[0].button("Process for Change of Status"):
                handle_suggestion("What documents does BMCC give for Change of Status?")
        else:
            if cols[0].button("How do I get an I-20?"):
                handle_suggestion("What documents do I need to upload for the I-20?")

        if cols[1].button("Application Deadlines"):
            handle_suggestion("When is the deadline for the next semester?")
            
        if cols[2].button("Tuition Costs"):
            handle_suggestion("How much is tuition for international students?")

    # 5. Chat Input
    if prompt := st.chat_input("Ask a specific question..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        st.rerun()
