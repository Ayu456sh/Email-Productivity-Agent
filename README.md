# Email Productivity Agent

An AI-powered email management system built with FastAPI and Streamlit, featuring automated categorization, action item extraction, and intelligent draft generation.

## 🚀 Live Demo

- **Frontend**: [https://email-agent-app.onrender.com](https://email-agent-app.onrender.com)
- **API Docs**: [https://email-agent-api.onrender.com/docs](https://email-agent-api.onrender.com/docs)

## Features

- 📧 **Email Categorization**: Automatically classify emails into categories
- ✅ **Action Item Extraction**: Extract tasks, deadlines, and priorities
- ✍️ **Smart Draft Generation**: AI-powered email replies
- 💬 **Chat Interface**: Interact with your inbox using natural language
- 🧠 **Customizable Prompts**: Train the AI with your own rules

## Tech Stack

- **Backend**: FastAPI, SQLite, Google Gemini AI
- **Frontend**: Streamlit
- **Deployment**: Render.com

## Local Development

```bash
# Install dependencies
pip install -r requirements.txt

# Set up environment variables
echo "GEMINI_API_KEY=your_key_here" > email_agent/.env

# Run backend
python -m uvicorn email_agent.backend.main:app --reload

# Run frontend (in another terminal)
python -m streamlit run email_agent/app.py
```

## Environment Variables

- `GEMINI_API_KEY`: Your Google Gemini API key (required)
- `API_URL`: Backend URL (for frontend, default: http://localhost:8000)

## Project Structure

```
Email_Productivity_Agent/
├── email_agent/
│   ├── backend/
│   │   ├── main.py           # FastAPI application
│   │   ├── dal.py            # Database access layer
│   │   ├── llm_service.py    # LLM integration
│   │   ├── email_service.py  # Email handling
│   │   └── system_prompts.py # AI prompt templates
│   ├── data/
│   │   └── mock_inbox.json   # Sample email data
│   ├── app.py                # Streamlit frontend
│   └── .env                  # Environment variables
├── requirements.txt
└── render.yaml               # Deployment config
```

## Deployment

See [DEPLOYMENT.md](./DEPLOYMENT.md) for detailed hosting instructions.

## License

MIT License - Feel free to use this project!
