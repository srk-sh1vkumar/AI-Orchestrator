# Web UI - Quick Start

## 🚀 Start in 60 Seconds

```bash
# 1. Start backend
cd /Users/shiva/Projects/ai-orchestrator
docker-compose up -d

# 2. Start frontend
cd frontend
npm install  # First time only
npm run dev

# 3. Open browser
open http://localhost:3000
```

Done! You now have the web UI running.

---

## 🎯 Quick Actions

### Send Your First Message

1. Type in the input box at bottom: `Build a REST API`
2. Press Enter or click Send
3. Watch AI Orchestrator respond!

### Change Provider

Click any provider in left sidebar:
- **Auto-route** - Let AI choose (recommended)
- **Claude Code** - For code/DevOps tasks
- **ChatGPT** - For UI/dashboards
- **Gemini** - For prompt optimization
- **Local LLM** - For incident analysis
- **Claude** - For reasoning

### Check System Health

Look at sidebar - green checkmarks mean provider is available.

---

## 📸 What You'll See

```
┌───────────────┬─────────────────────────────┐
│ Sidebar       │ Chat Area                   │
│               │                             │
│ System Status │ Your messages appear here   │
│ ✅ healthy     │                             │
│               │ AI responses with provider  │
│ Providers:    │ info and tools executed     │
│ 🤖 Claude     │                             │
│ 💬 ChatGPT    │                             │
│ ✨ Gemini     │ [Type message here] [Send]  │
└───────────────┴─────────────────────────────┘
```

---

## 🎨 Features

- ✅ Real-time chat
- ✅ Provider selection
- ✅ Health monitoring
- ✅ Tool visualization
- ✅ Markdown rendering
- ✅ Code highlighting

---

## 🐛 Troubleshooting

**UI won't load?**
```bash
# Check backend
curl http://localhost:8000/api/health

# Restart frontend
cd frontend
npm run dev
```

**API errors?**
- Ensure backend is running on port 8000
- Check `.env` has `VITE_API_URL=http://localhost:8000`

---

## 📚 More Info

- Full guide: `WEB_UI_GUIDE.md`
- Frontend README: `frontend/README.md`
- API docs: http://localhost:8000/docs

---

**Ready to chat!** 🎉
