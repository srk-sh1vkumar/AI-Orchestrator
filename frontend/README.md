# AI Orchestrator - Web UI

Modern web interface for the AI Orchestrator system.

## Features

- 💬 Real-time chat interface
- 🎯 Provider selection (auto-route or manual)
- 📊 Live system health monitoring
- 🛠️ Tool execution visualization
- 🎨 Modern, responsive design
- ⚡ Built with React + TypeScript + Vite

## Quick Start

### Install Dependencies

```bash
cd frontend
npm install
```

### Development

```bash
# Start dev server (with API proxy)
npm run dev

# Open browser to http://localhost:3000
```

### Build for Production

```bash
# Build optimized bundle
npm run build

# Preview production build
npm run preview
```

## Configuration

Create `.env` file:

```bash
cp .env.example .env
```

Edit `.env`:
```
VITE_API_URL=http://localhost:8000
```

## Project Structure

```
frontend/
├── src/
│   ├── components/      # React components
│   │   ├── ChatMessage.tsx
│   │   ├── ChatInput.tsx
│   │   └── Sidebar.tsx
│   ├── pages/           # Page components
│   │   └── ChatPage.tsx
│   ├── types/           # TypeScript types
│   │   └── index.ts
│   ├── utils/           # Utilities
│   │   └── api.ts       # API client
│   ├── App.tsx          # Main app component
│   ├── main.tsx         # Entry point
│   └── index.css        # Global styles
├── public/              # Static assets
├── index.html           # HTML template
├── package.json         # Dependencies
├── tsconfig.json        # TypeScript config
├── vite.config.ts       # Vite config
└── tailwind.config.js   # Tailwind CSS config
```

## Tech Stack

- **React 18** - UI framework
- **TypeScript** - Type safety
- **Vite** - Build tool
- **Tailwind CSS** - Styling
- **Lucide React** - Icons
- **Axios** - HTTP client
- **React Markdown** - Markdown rendering

## API Integration

The frontend connects to the FastAPI backend via:

- Development: Vite proxy (`/api` → `http://localhost:8000`)
- Production: Environment variable `VITE_API_URL`

## Available Commands

| Command | Description |
|---------|-------------|
| `npm run dev` | Start development server |
| `npm run build` | Build for production |
| `npm run preview` | Preview production build |
| `npm run lint` | Run ESLint |

## Deployment

### With Docker

```bash
# Build frontend
cd frontend
npm run build

# Copy dist to backend static folder
cp -r dist ../static

# Backend will serve the UI
```

### Standalone

```bash
# Build
npm run build

# Serve with any static file server
npx serve -s dist
```

## Features

### Chat Interface
- Send messages to AI Orchestrator
- View provider routing decisions
- See tool execution results
- View execution times

### Provider Selection
- Auto-route (let AI choose)
- Manual provider selection
- Live provider status
- Provider availability indicators

### System Health
- Real-time health monitoring
- Provider status indicators
- Auto-refresh every 30s
- Manual refresh button

### Response Display
- Markdown rendering
- Code syntax highlighting
- Tool execution visualization
- Collaboration step tracking

## Browser Support

- Chrome/Edge (latest)
- Firefox (latest)
- Safari (latest)

## Development Tips

### Hot Reload

Vite provides instant hot module replacement. Changes to components will reflect immediately.

### Type Checking

```bash
npx tsc --noEmit
```

### Debugging

Open React DevTools in browser for component inspection.

## Troubleshooting

### API Connection Issues

Check that backend is running:
```bash
curl http://localhost:8000/api/health
```

### Build Errors

Clear cache and reinstall:
```bash
rm -rf node_modules dist
npm install
```

### CORS Errors

Ensure backend has CORS enabled for frontend origin.

## License

MIT
