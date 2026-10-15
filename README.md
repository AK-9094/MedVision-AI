# MedVision AI — Healthcare Information Assistant

MedVision AI is an AI-powered healthcare information assistant built with Python, Streamlit, and Google Gemini. It helps users understand medical reports, analyze medicine images, and ask healthcare-related questions in simple language.

## Features

- **Medical Report Analysis:** Upload a medical report and receive an easy-to-understand explanation of its findings.
- **Medicine Scanner:** Upload an image of medicine packaging to extract visible medicine information.
- **AI Chat Assistant:** Ask follow-up questions about your uploaded report or medicine information.
- **Doctor Discussion Support:** Get suggestions for questions to discuss with a healthcare professional.
- **WhatsApp Summary:** Send a summary through WhatsApp using Twilio, with user confirmation.

## Tech Stack

- Python
- Streamlit
- Google Gemini API (`google-genai`)
- Twilio WhatsApp API

## Project Structure

```text
MedVision AI/
├── .streamlit/
│   └── secrets.toml
├── app.py
├── prompts.py
├── requirements.txt
├── .gitignore
└── README.md
```

## Installation and Setup

### 1. Clone the repository

```bash
git clone https://github.com/AK-9094/MedVision-AI.git
cd MedVision-AI
```

### 2. Create and activate a virtual environment

For Windows PowerShell:

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure API credentials

Create a file named `.streamlit/secrets.toml` and add your own credentials:

```toml
GEMINI_API_KEY = "YOUR_GEMINI_API_KEY"

TWILIO_ACCOUNT_SID = "YOUR_TWILIO_ACCOUNT_SID"
TWILIO_AUTH_TOKEN = "YOUR_TWILIO_AUTH_TOKEN"
TWILIO_WHATSAPP_FROM = "whatsapp:+14155238886"
TWILIO_CONTENT_SID = "YOUR_TWILIO_CONTENT_SID"
```

Replace the placeholders with your credentials. Never commit this file or expose API keys publicly.

### 5. Run the application

```powershell
streamlit run app.py
```

The application will open in your browser.

## Medical Disclaimer

MedVision AI is intended for educational and informational purposes only. It does not provide medical diagnoses or prescriptions and is not a substitute for advice from a qualified healthcare professional. Always consult a doctor or pharmacist for medical decisions.

## Author

Developed as an AI application project using Python, Streamlit, Google Gemini, and Twilio.