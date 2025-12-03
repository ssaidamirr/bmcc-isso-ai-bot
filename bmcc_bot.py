import streamlit as st
import requests
import json
import time

# --- CONFIGURATION ---
GEMINI_MODEL = 'gemini-2.5-flash-preview-09-2025'
# Note: Added https:// to ensure the URL is correct
API_URL = f"https://generativelanguage.googleapis.com/v1beta/models/{GEMINI_MODEL}:generateContent?key="

st.set_page_config(page_title="BMCC International Guide", page_icon="🗽", layout="centered")

# --- KNOWLEDGE BASE ---
BMCC_KNOWLEDGE_BASE = """
GENERAL BMCC RULES:
- BMCC is a CUNY college. All applications must be submitted via the [CUNY Application Portal](https://www.cuny.edu/admissions/undergraduate/apply/).
- Application Fee: **$65 for Freshman** applicants, **$70 for Transfer** applicants.
- **Important:** There are **NO fee waivers** available for international students.
- English Proficiency: **An English Proficiency Certificate (TOEFL/IELTS) is NOT required for admission.** All admitted international students must take the **CUNY Accuplacer ESL test** to determine their placement levels.
- Documents: High school transcripts/diplomas must be translated and evaluated.

TUITION & FEES (International Students):
- **Tuition Basis:** Tuition is charged **per credit** or per "contact hour".
- **Rate:** International students pay the Non-Resident rate of **$320 per credit**.
- **Full-Time Requirement:** To maintain F-1 status, you **MUST** take at least **12 credits** (or billable equivalent hours) per semester.
- **Estimated Tuition:** ~$8,050 USD per academic year (Tuition + Fees, excluding living expenses).

I-20 FINANCIAL REQUIREMENTS (Proof of Funds):
To receive the Form I-20, you must prove funding based on the following official calculations.

**1. Estimated Costs (One Year):**
- Tuition and Fees: **$8,050**
- Living Expenses: **$36,454**
- **One-Year Total:** $44,504
- **Two-Year Total:** $89,008

**2. Required Proof Amounts:**
- **Option A: Paying For Yourself (Self-Sponsor):** - You must show a Bank Statement with **$89,008** (Total for 2 years).
  - The account must be in your name only.
- **Option B: Sponsored by Someone Else:**
  - Sponsors must show **Annual Income** of **$133,512** (3x the one-year cost).
  - *Calculation:* ($44,504 x 3 = $133,512).
  - *Documents:* Sponsor's Tax Return (Proof of Income) AND Bank Statement (Proof of Current Finances).

**3. Reductions (Free Room & Board):**
- If living with a relative/friend in the US for free, submit a "Room and Board Affidavit" + Lease/Deed.
- Value of Room & Board Deduction: **$17,928 per year**.
- **New Total Required:** **$53,152** (Calculation: $89,008 - $17,928 [Year 1] - $17,928 [Year 2]).

**4. Dependents (F-2):**
- Spouse: Add **$8,000**.
- Child: Add **$5,000** each.

**Documents to Submit:**
- **Self-Sponsored:** Bank Statement in student's name.
- **Sponsors:** - Proof of Income: Signed Tax Return (Form 1040/1040A) OR Employer Letter + 3 months paystubs.
  - Proof of Finances: Bank statement (last 3 months).

[How to Receive I-20 Guide & Forms](https://www.bmcc.cuny.edu/admissions/international/after-you-are-accepted/the-i-20-form-applying-for-an-f-1-student-visa/)

SCHOLARSHIPS & FINANCIAL AID:
- **Federal Aid:** International students are **NOT** eligible for FAFSA or NY State aid (TAP).
- **BMCC Scholarships:** You may apply for scholarships **after your first semester** if you maintain a high GPA.
  - Examples: **BMCC Foundation Scholarship**, **SGA Scholarship**, **Out-In-Two**.
- **More Info:** [Scholarship Opportunities](https://www.bmcc.cuny.edu/students/scholarships-awards-other-opportunities/)

TRANSCRIPT EVALUATION (For education outside US):
- Transcripts must be evaluated by a NACES member agency. 
- You can find a list of approved agencies here: [NACES Members](https://www.naces.org/members).
- Common agencies include WES, ECE, and Josef Silny.

SEVIS TRANSFER (For F-1 Students Currently in US):
- ACADEMIC STATUS: If coming from ESL school -> Apply as Freshman. If coming from University -> Apply as Transfer.
- IMMIGRATION STATUS: Both must do "SEVIS Transfer".
- Process: 1. Get Acceptance Letter. 2. Fill out Transfer Release Form. 3. Current school releases SEVIS record.

CHANGE OF STATUS (B1/B2/J1 to F-1 inside US):
- **Warning:** Changing status inside the US takes a long time (often 12+ months).
- BMCC does NOT assist with the legal application (Form I-539).
- BMCC ONLY provides the Form I-20 labeled "Initial Attendance - Change of Status".
- Students **MUST** consult an immigration lawyer for the legal process.
- B1/B2 holders **CANNOT** study until status is officially approved to F-1.

APPLYING FOR F-1 VISA (Consular Processing outside US):
- For students outside US or those choosing to leave the US to apply.
- Process: 1. Get Accepted. 2. Receive I-20 from BMCC. 3. Pay SEVIS I-901 Fee. 4. Complete DS-160 and schedule interview at US Embassy.

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
if 'suggestions' not in st.session_state:
    # UPDATED: Progressive starting questions
    st.session_state.suggestions = [
        "How do I apply to BMCC?",
        "What documents do I need?",
        "When is the deadline?"
    ]

# --- HELPER: Gemini API Call ---
def get_ai_response(user_query, profile):
    try:
        api_key = st.secrets["GEMINI_API_KEY"]
    except KeyError:
        return {"answer": "Error: API Key missing. Please set it in Streamlit Secrets.", "suggestions": []}

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
        "2. Provide answers in clear, simple Step 1, Step 2, Step 3 format."
        "3. Use [Link Text](URL) format for hyperlinks provided in the context."
        "4. **FORMATTING:** Use consistent Markdown. Do NOT switch fonts. Use bolding for emphasis, but keep the text style uniform."
        "5. YOU MUST RESPOND IN JSON FORMAT with two keys: 'answer' (the string response) and 'suggestions' (a list of 3 short, relevant, PROGRESSIVE follow-up questions based on your answer. If you just explained how to apply, suggest asking about documents or tuition next)."
    )

    payload = {
        "contents": [{"role": "user", "parts": [{"text": user_query}]}],
        "systemInstruction": {"parts": [{"text": system_instruction}]},
        "generationConfig": {"responseMimeType": "application/json"}
    }

    # Retry Logic for 503 Errors
    max_retries = 5
    for attempt in range(max_retries):
        try:
            response = requests.post(
                API_URL + api_key,
                headers={'Content-Type': 'application/json'},
                data=json.dumps(payload),
                timeout=30
            )
            
            if response.status_code == 200:
                content = response.json()['candidates'][0]['content']['parts'][0]['text']
                return json.loads(content)
            
            elif response.status_code == 503:
                # 503 Service Unavailable - Wait and retry
                wait_time = 2 ** attempt # Exponential backoff: 1, 2, 4, 8, 16 seconds
                time.sleep(wait_time)
                continue
            
            else:
                return {"answer": f"Error connecting to AI: {response.status_code}", "suggestions": []}
                
        except Exception as e:
            if attempt == max_retries - 1:
                return {"answer": f"Error: {e}", "suggestions": []}
            time.sleep(2 ** attempt)
            continue

    return {"answer": "The AI service is currently busy. Please try again in a moment.", "suggestions": []}

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
            st.session_state.suggestions = [
                "How do I apply to BMCC?",
                "What documents do I need?",
                "When is the deadline?"
            ]
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
        st.session_state.step = 2.8 # Ask about plan
        st.rerun()
        
    col3, col4 = st.columns(2)
    if col3.button("J-1 (Exchange)", use_container_width=True):
        st.session_state.profile['visa_status'] = "J-1 Exchange"
        st.session_state.step = 2.8 # Ask about plan
        st.rerun()
        
    if col4.button("Other / Not Sure", use_container_width=True):
        st.session_state.profile['visa_status'] = "Other"
        st.session_state.step = 2.8 # Ask about plan
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

elif st.session_state.step == 2.8: # Non-F1 Inside US Logic
    st.subheader("Step 2b: How do you plan to obtain F-1 Status?")
    st.warning("You are currently inside the US but not on F-1 status.")
    
    if st.button("I want to Change Status inside the US", use_container_width=True):
        st.session_state.profile['immigration_needs'] = "Change of Status (Requires Lawyer)"
        st.session_state.step = 3
        st.rerun()
        
    if st.button("I will travel and apply for F-1 Visa outside the US", use_container_width=True):
        st.session_state.profile['immigration_needs'] = "Consular Processing (Apply Outside US)"
        st.session_state.step = 3
        st.rerun()

elif st.session_state.step == 3: # General Education Check
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
        elif "Change of Status" in str(p['immigration_needs']):
            greeting += " ⚠️ **Important:** You selected **Change of Status**. BMCC can provide the I-20, but you **must** work with an immigration lawyer for the legal I-539 application. You cannot study until approved."
        elif "Consular Processing" in str(p['immigration_needs']):
            greeting += " You will need to apply to BMCC, receive your I-20, and then travel to apply for your F-1 visa at a US Consulate."
        else:
            greeting += " I can help you with the application and F-1 Visa steps."
            
        st.session_state.messages.append({"role": "assistant", "content": greeting})

    # 2. Display Chat History
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    # 3. Generate Logic for Last Message (if user just typed)
    if st.session_state.messages and st.session_state.messages[-1]["role"] == "user":
        user_query = st.session_state.messages[-1]["content"]
        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                response_data = get_ai_response(user_query, st.session_state.profile)
                answer = response_data.get("answer", "Error processing response.")
                new_suggestions = response_data.get("suggestions", [])
                
                st.markdown(answer)
                st.session_state.messages.append({"role": "assistant", "content": answer})
                
                # Update suggestions if valid
                if new_suggestions:
                    st.session_state.suggestions = new_suggestions
        st.rerun()

    # 4. Dynamic Suggested Questions
    if st.session_state.messages and st.session_state.messages[-1]["role"] == "assistant":
        st.write("---")
        st.caption("Suggested Questions:")
        cols = st.columns(3)
        for i, suggestion in enumerate(st.session_state.suggestions):
            if i < 3: # Ensure max 3 buttons
                if cols[i].button(suggestion, key=f"sugg_{len(st.session_state.messages)}_{i}"):
                    handle_suggestion(suggestion)

    # 5. Chat Input
    st.caption("💡 Tip: If you don't understand any part, just ask me to explain it!")
    if prompt := st.chat_input("Ask specific questions here..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        st.rerun()
