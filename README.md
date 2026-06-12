# GitHub Repository Code Chat Assistant

An intelligent, AI-powered conversational assistant that allows you to chat directly with any GitHub repository. Built with a premium Glassmorphism React frontend and a robust FastAPI backend powered by LangChain, ChromaDB, and Groq LLaMA-3.1.

## Features
- **Smart GitHub Ingestion**: Instantly parses entire GitHub repositories, understanding root folders and high-level project goals.
- **RAG Architecture**: Uses ChromaDB for lightning-fast semantic vector search over repository files.
- **LLM Integration**: Integrates directly with Groq (LLaMA-3.1) for <2s response times.
- **Persistent Memory**: Retains conversation history using local or MongoDB storage.
- **Premium Interface**: A modern React UI featuring a dark glassmorphism theme, dynamic animations, and native Markdown rendering.

## Tech Stack
- **Backend**: FastAPI, Python 3.10+, LangChain, ChromaDB, Groq API
- **Frontend**: React, Vite, CSS Modules, React-Markdown

## Setup Guide

### 1. Backend Configuration
1. Create a Python virtual environment:
   ```sh
   python -m venv venv
   source venv/Scripts/activate # Windows
   ```
2. Install dependencies:
   ```sh
   pip install -r requirements.txt
   ```
3. Configure environment variables. Rename `.env.example` to `.env` and add your API keys:
   ```env
   GITHUB_TOKEN=your_token
   GROQ_API_KEY=your_key
   ```
4. Start the backend server:
   ```sh
   python -m api.main
   ```

### 2. Frontend Configuration
1. Navigate to the `frontend` directory:
   ```sh
   cd frontend
   ```
2. Install Node modules:
   ```sh
   npm install
   ```
3. Start the Vite development server:
   ```sh
   npm run dev
   ```

## Usage
1. Open your browser to `http://localhost:5173`.
2. Type in any public `owner/repo` (e.g., `facebook/react`).
3. Click **Ingest Repository**.
4. Chat directly with the codebase!
