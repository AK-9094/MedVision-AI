
import re
import json
import streamlit as st
from google import genai
from google.genai import types
from twilio.rest import Client

from prompts import (
    MEDICAL_SYSTEM_PROMPT,
    REPORT_ANALYSIS_PROMPT,
    MEDICINE_SCANNER_PROMPT,
    FOLLOW_UP_PROMPT,
    DOCTOR_DISCUSSION_PROMPT,
    WHATSAPP_SUMMARY_PROMPT,
)

# 1. App configuration
st.set_page_config(
    page_title="MedVision AI",
    page_icon="🏥",
    layout="wide",
)

MODEL_NAME = "gemini-3.5-flash"

#2. Session state
defaults = {
    "profile": None,
    "analysis_text": "",
    "analysis_type": "",
    "analysis_filename": "",
    "chat_history": [],
}

for key, value in defaults.items():
    if key not in st.session_state:
        st.session_state[key] = value


# 3. Gemini client
@st.cache_resource
def get_gemini_client(api_key):
    return genai.Client(api_key=api_key)


def ask_gemini(prompt, uploaded_file=None):
    """Generate a response using Gemini text or vision."""

    api_key = st.secrets.get("GEMINI_API_KEY", "")

    if not api_key:
        raise ValueError(
            "GEMINI_API_KEY is missing from secrets.toml."
        )

    client = get_gemini_client(api_key)

    contents = [
        MEDICAL_SYSTEM_PROMPT,
        prompt,
    ]

    if uploaded_file is not None:
        contents.append(
            types.Part.from_bytes(
                data=uploaded_file.getvalue(),
                mime_type=uploaded_file.type,
            )
        )

    response = client.models.generate_content(
        model=MODEL_NAME,
        contents=contents,
    )

    answer = response.text

    if not answer:
        raise ValueError(
            "Gemini returned an empty response. Please try again."
        )

    return answer.strip()


# 4. TWILIO WHATSAPP
def send_whatsapp_summary(phone_number, summary):
    """Send a summary using an approved Twilio WhatsApp template."""

    account_sid = st.secrets["TWILIO_ACCOUNT_SID"]
    auth_token = st.secrets["TWILIO_AUTH_TOKEN"]
    whatsapp_from = st.secrets["TWILIO_WHATSAPP_FROM"]
    content_sid = st.secrets["TWILIO_CONTENT_SID"]

    if not content_sid.startswith("HX"):
        raise ValueError(
            "Please configure a valid Twilio Content SID."
        )

    client = Client(account_sid, auth_token)

    message = client.messages.create(
        from_=whatsapp_from,
        to=f"whatsapp:{phone_number}",
        content_sid=content_sid,
        content_variables=json.dumps({
            "1": summary
        }),
    )

    return message.sid


# 5. onboarding
def show_onboarding():
    st.title("🏥 Welcome to MedVision AI")
    st.write(
        "Understand medical reports and medicine labels "
        "with an AI-powered healthcare information assistant."
    )

    st.info(
        "MedVision AI provides educational information. "
        "It does not diagnose conditions or replace a doctor "
        "or pharmacist."
    )

    with st.form("onboarding_form"):
        name = st.text_input(
            "Your name",
            placeholder="Enter your name",
        )

        phone = st.text_input(
            "WhatsApp number",
            placeholder="+919876543210",
            help="Use international format, including the country code.",
        )

        preference = st.selectbox(
            "What would you like to use MedVision AI for?",
            [
                "Both medical reports and medicines",
                "Medical reports",
                "Medicine information",
            ],
        )

        accepted = st.checkbox(
            "I understand that this tool provides educational "
            "information and is not a substitute for professional "
            "medical advice."
        )

        submitted = st.form_submit_button(
            "Continue",
            use_container_width=True,
        )

        if submitted:
            if not name.strip():
                st.error("Please enter your name.")

            elif not re.fullmatch(r"\+[1-9]\d{7,14}", phone.strip()):
                st.error(
                    "Enter a valid international-format number, "
                    "for example +919876543210."
                )

            elif not accepted:
                st.error(
                    "Please accept the educational-use disclaimer "
                    "to continue."
                )

            else:
                st.session_state.profile = {
                    "name": name.strip(),
                    "phone": phone.strip(),
                    "preference": preference,
                }

                st.rerun()


# 6. Report Analysis
def analyze_report(uploaded_file):
    with st.spinner("Analyzing your medical report..."):
        result = ask_gemini(
            REPORT_ANALYSIS_PROMPT,
            uploaded_file,
        )

    st.session_state.analysis_text = result
    st.session_state.analysis_type = "Medical report"
    st.session_state.analysis_filename = uploaded_file.name
    st.session_state.chat_history = []

# 7. Medicine Scanner
def analyze_medicine(uploaded_file):
    with st.spinner("Examining the medicine label..."):
        result = ask_gemini(
            MEDICINE_SCANNER_PROMPT,
            uploaded_file,
        )

    st.session_state.analysis_text = result
    st.session_state.analysis_type = "Medicine information"
    st.session_state.analysis_filename = uploaded_file.name
    st.session_state.chat_history = []



# 8. Chat Section
def answer_follow_up(question):
    conversation = ""

    for item in st.session_state.chat_history:
        conversation += (
            f"\n{item['role'].upper()}: {item['content']}\n"
        )

    prompt = (
        FOLLOW_UP_PROMPT
        + "\n\nCURRENT ANALYSIS:\n"
        + (
            st.session_state.analysis_text
            or "No medical report or medicine analysis is available."
        )
        + "\n\nCONVERSATION HISTORY:\n"
        + conversation
        + "\n\nLATEST USER QUESTION:\n"
        + question
    )

    with st.spinner("Preparing your answer..."):
        answer = ask_gemini(prompt)

    st.session_state.chat_history.append({
        "role": "user",
        "content": question,
    })

    st.session_state.chat_history.append({
        "role": "assistant",
        "content": answer,
    })



# 9. WHATSAPP SUMMARY
def prepare_whatsapp_summary():
    prompt = (
        WHATSAPP_SUMMARY_PROMPT
        + "\n\nANALYSIS TO SUMMARIZE:\n"
        + st.session_state.analysis_text
    )

    with st.spinner("Preparing your WhatsApp summary..."):
        return ask_gemini(prompt)


# 10. Appliction 
if st.session_state.profile is None:
    show_onboarding()
    st.stop()


profile = st.session_state.profile

# Sidebar
with st.sidebar:
    st.title("🏥 MedVision AI")

    st.write(f"Welcome, **{profile['name']}**")

    st.caption(profile["preference"])

    st.divider()

    page = st.radio(
        "Choose a feature",
        [
            "Medical Report Analysis",
            "Medicine Scanner",
            "Ask a Question",
        ],
    )

    st.divider()

    st.caption(
        "Educational use only. For medical decisions, "
        "consult a qualified healthcare professional."
    )

    if st.button("Reset session", use_container_width=True):
        for key in defaults:
            st.session_state[key] = defaults[key]

        st.rerun()


# Main heading
st.title("MedVision AI")
st.write(
    "Your multimodal healthcare information assistant."
)



# 11. Medical report page
if page == "Medical Report Analysis":

    st.subheader("📄 Medical Report Explainer")

    st.write(
        "Upload a medical report to extract readable results "
        "and understand the terminology."
    )

    report_file = st.file_uploader(
        "Upload a report",
        type=["pdf", "png", "jpg", "jpeg", "webp"],
        key="report_upload",
    )

    if report_file:
        st.caption(f"Selected file: {report_file.name}")

        if st.button(
            "Analyze Medical Report",
            type="primary",
            use_container_width=True,
        ):
            try:
                analyze_report(report_file)
                st.success("Report analysis completed.")

            except Exception as error:
                st.error("Unable to analyze this report.")
                st.caption(str(error))

    if (
        st.session_state.analysis_text
        and st.session_state.analysis_type == "Medical report"
    ):
        st.divider()
        st.subheader("📊 Report Analysis")

        st.caption(st.session_state.analysis_filename)

        st.markdown(st.session_state.analysis_text)

        st.info(
            "Check extracted values and reference ranges against "
            "the original report. Contact your clinician about "
            "results that concern you."
        )

# 12. Medicine scanner page
elif page == "Medicine Scanner":

    st.subheader("💊 Medicine Scanner")

    st.write(
        "Upload a clear photo of the medicine packaging or label."
    )

    medicine_file = st.file_uploader(
        "Upload a medicine image",
        type=["pdf", "png", "jpg", "jpeg", "webp"],
        key="medicine_upload",
    )

    if medicine_file:
        st.image(
            medicine_file,
            caption="Uploaded medicine image",
            use_container_width=True,
        )

        if st.button(
            "Analyze Medicine",
            type="primary",
            use_container_width=True,
        ):
            try:
                analyze_medicine(medicine_file)
                st.success("Medicine analysis completed.")

            except Exception as error:
                st.error("Unable to analyze this medicine image.")
                st.caption(str(error))

    if (
        st.session_state.analysis_text
        and st.session_state.analysis_type == "Medicine information"
    ):
        st.divider()
        st.subheader("💊 Medicine Information")

        st.caption(st.session_state.analysis_filename)

        st.markdown(st.session_state.analysis_text)

        st.warning(
            "AI identification can be wrong. Confirm the medicine "
            "and its instructions with a pharmacist. Do not change "
            "how you take a medicine based on this analysis."
        )


# 13. chat page
elif page == "Ask a Question":

    st.subheader("💬 Ask MedVision AI")

    if st.session_state.analysis_text:
        st.success(
            f"Current context: {st.session_state.analysis_type}"
        )
        st.caption(st.session_state.analysis_filename)

    else:
        st.info(
            "You can ask general educational questions. To ask "
            "about a particular report or medicine, analyze it first."
        )

    for item in st.session_state.chat_history:
        with st.chat_message(item["role"]):
            st.markdown(item["content"])

    question = st.chat_input(
        "Ask about your report or medicine..."
    )

    if question:
        try:
            answer_follow_up(question)
            st.rerun()

        except Exception as error:
            st.error("Unable to answer your question.")
            st.caption(str(error))

    if st.session_state.analysis_text:
        with st.expander("View current analysis"):
            st.markdown(st.session_state.analysis_text)

        if st.button("Suggest questions for my doctor"):
            try:
                prompt = (
                    DOCTOR_DISCUSSION_PROMPT
                    + "\n\nCURRENT ANALYSIS:\n"
                    + st.session_state.analysis_text
                )

                with st.spinner("Preparing questions..."):
                    suggestions = ask_gemini(prompt)

                st.markdown("### Questions to discuss")
                st.markdown(suggestions)

            except Exception as error:
                st.error("Unable to prepare questions.")
                st.caption(str(error))



# 14. whatsapp summary
if st.session_state.analysis_text:

    st.divider()
    st.subheader("📱 WhatsApp Summary")

    st.write(
        "Review the analysis and send a concise summary to "
        "your registered WhatsApp number when you choose."
    )

    with st.expander("Preview current analysis"):
        st.markdown(st.session_state.analysis_text)

    if st.button(
        "Prepare and Send WhatsApp Summary",
        type="primary",
        use_container_width=True,
    ):
        try:
            summary = prepare_whatsapp_summary()

            st.session_state["pending_whatsapp_summary"] = summary

        except Exception as error:
            st.error("Unable to prepare the WhatsApp summary.")
            st.caption(str(error))

    pending_summary = st.session_state.get(
        "pending_whatsapp_summary",
        "",
    )

    if pending_summary:
        st.write("### Review your message")

        edited_summary = st.text_area(
            "WhatsApp message",
            value=pending_summary,
            height=200,
            key="whatsapp_summary_editor",
        )

        st.warning(
            "Medical information is sensitive. Confirm that you "
            "want to send this message to your registered number."
        )

        confirmed = st.checkbox(
            "I have reviewed this message and want to send it "
            "to my WhatsApp number.",
            key="confirm_whatsapp_send",
        )

        if st.button(
            "Confirm and Send",
            use_container_width=True,
        ):
            if not confirmed:
                st.error("Please confirm before sending.")

            elif not edited_summary.strip():
                st.error("The message cannot be empty.")

            else:
                try:
                    with st.spinner("Sending WhatsApp message..."):
                        message_sid = send_whatsapp_summary(
                            profile["phone"],
                            edited_summary.strip(),
                        )

                    st.success(
                        "The message was submitted to Twilio."
                    )
                    st.caption(f"Twilio message SID: {message_sid}")

                    st.session_state.pop(
                        "pending_whatsapp_summary",
                        None,
                    )

                    st.session_state.pop(
                        "confirm_whatsapp_send",
                        None,
                    )

                except Exception:
                    st.error(
                        "The message could not be sent. Check your "
                        "Twilio credentials, Content SID, template "
                        "variables, recipient setup, and WhatsApp "
                        "messaging permissions."
                    )



# 15. FOOTER
st.divider()
st.caption(
    "MedVision AI is an educational information tool, not a "
    "diagnostic system. It can make mistakes. Verify extracted "
    "information and consult a qualified healthcare professional "
    "for medical decisions."
)
