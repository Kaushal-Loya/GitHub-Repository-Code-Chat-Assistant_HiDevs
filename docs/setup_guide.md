# Setup Guide

## Prerequisites
- Python 3.11+
- Groq API Key
- GitHub Personal Access Token (PAT)
- MongoDB URI (Optional)

## Local Installation

1. Create a virtual environment:
   ```bash
   python -m venv .venv
   .\venv\Scripts\activate  # Windows
   source .venv/bin/activate  # macOS/Linux
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Setup environment variables:
   Copy `.env.example` to `.env` and fill in the missing keys.

4. Run the Streamlit Application:
   ```bash
   streamlit run app.py
   ```
