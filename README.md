Project Complete. 
# GitFit — AI-Powered GitHub Repository Analysis

> Instant intelligence on any GitHub repository. Paste a URL, get a complete breakdown of structure, code quality, contributors, security, and activity.

![Version](https://img.shields.io/badge/version-0.3.0-blue) ![License](https://img.shields.io/badge/license-MIT-green) ![Python](https://img.shields.io/badge/python-3.9%2B-blue) ![Node.js](https://img.shields.io/badge/node-18%2B-green)

---

## ✨ What is GitFit?

**GitFit** is a full-stack web application that analyzes any public GitHub repository and generates an intelligent, visual summary of:

- **Repository Metadata** — Stars, forks, watchers, topics, licenses
- **Code Architecture** — Detected patterns, entry points, key directories, modularity
- **Code Quality** — Test coverage signals, CI/CD presence, documentation, linting
- **Security Assessment** — Environment variable management, secret exposure detection, dependency audit recommendations
- **Contributors & Team** — Contributor breakdown, commit frequency, team concentration metrics
- **Commit Activity Timeline** — 12+ weeks of commit/add/delete patterns
- **Technology Stack** — Language breakdown with percentages and visual representation

The analysis combines **GitHub REST API data** with optional **LLM enrichment** (via Groq) to provide both raw facts and intelligent insights.

---

## 🎯 Key Features

### 🚀 Fast & Responsive
- **10-minute caching** for repeated queries
- **Concurrent API calls** minimize wall-clock time
- **Graceful fallbacks** when optional LLM is unavailable

### 🧠 Smart Analysis
- **Heuristic baselines** from file tree inspection (tests, CI, docs, linters, Docker)
- **LLM enrichment** (optional, via Groq) for architecture patterns and code quality scoring
- **Dependency detection** from package managers (npm, pip, go, cargo, maven, bundler, etc.)

### 🎨 Beautiful UI
- **Glassmorphism design** with navy, red, and sky blue palette
- **Bento grid layout** for intuitive information architecture
- **Animated charts** and interactive data visualizations
- **Responsive design** — desktop, tablet, mobile ready
- **Real-time rendering** with smooth transitions and transitions

### 🔐 Privacy First
- **No data storage** — analyze and discard
- **Public repos only** — unauthenticated requests for basic access
- **Optional GitHub token** — for higher rate limits (5,000/hour vs. 60/hour)

### 📊 Comprehensive Insights
- Commit history analysis (frequency, trends, message quality)
- Contributor metrics (concentration, Pareto analysis, bot detection)
- Architecture pattern detection (MVC, REST API, microservices, monorepo, etc.)
- Code quality scoring (0–100) with actionable notes

---

## 📋 Requirements

### Backend
- **Python 3.9+**
- **FastAPI** — web framework
- **httpx** — async HTTP client for GitHub API
- **langchain** & **langchain-groq** — LLM integration (optional)
- **pydantic** — data validation

### Frontend
- **Node.js 18+**
- **React 18+** with TypeScript
- **React Router v6** — client-side routing
- **Vite** — build tool

---

## 🚀 Quick Start

### Prerequisites
1. **GitHub Personal Access Token** (optional but recommended for higher rate limits)
   - Create at: https://github.com/settings/tokens
   - Scope: `repo` (public repo access)

2. **Groq API Key** (optional for LLM enrichment)
   - Sign up at: https://console.groq.com
   - Used for architecture insights and code quality scoring

### Installation & Setup

#### 1. Clone the repository
```bash
git clone https://github.com/autumn-xn/gitfit.git
cd gitfit
```

#### 2. Set up backend

```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Create .env file
cat > .env << EOF
GITHUB_TOKEN=ghp_your_token_here
GROQ_API_KEY=gsk_your_key_here
LLM_MODEL=llama-3.3-70b-versatile
EOF

# Run development server
python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

The backend will be available at `http://localhost:8000`

#### 3. Set up frontend

```bash
cd frontend

# Install dependencies
npm install

# Create .env file (or use defaults)
cat > .env.local << EOF
VITE_API_URL=http://localhost:8000
EOF

# Start development server
npm run dev
```

The frontend will be available at `http://localhost:5173`

#### 4. Open the app

Navigate to `http://localhost:5173` in your browser and paste a GitHub repo URL:
- `https://github.com/facebook/react`
- `owner/repo` (e.g., `vercel/next.js`)
- Short links (e.g., `lnkd.in/...`) — auto-resolved

---

## 🏗️ Architecture Overview

### Backend Flow

```
User Input (GitHub URL)
    ↓
resolve_repo_url() — Parse and follow redirects
    ↓
fetch_repo() — GitHub REST API
    ├─ GET /repos/{owner}/{repo}
    ├─ GET /repos/{owner}/{repo}/languages
    ├─ GET /repos/{owner}/{repo}/contributors
    ├─ GET /repos/{owner}/{repo}/stats/commit_activity
    ├─ GET /repos/{owner}/{repo}/stats/code_frequency
    ├─ GET /repos/{owner}/{repo}/readme
    └─ GET /repos/{owner}/{repo}/git/trees/{branch}?recursive=1
    ↓
Heuristic Analysis (file tree inspection)
    ├─ detect_quality_flags() — Tests, CI, docs, linters, Docker
    ├─ detect_entry_points() — main.py, app.js, etc.
    ├─ detect_key_directories() — src/, tests/, docs/, etc.
    └─ detect_architecture_patterns() — MVC, REST API, monorepo, etc.
    ↓
Optional: LLM Enrichment (via Groq)
    └─ Refine architecture summary & code quality scoring
    ↓
_build_result() — Assemble AnalysisResult
    ↓
Response to Frontend (JSON)
```

### Frontend Flow

```
Home Page — RepoInput Component
    ↓
User pastes GitHub URL
    ↓
useAnalysis Hook (state machine)
    ├─ POST /analyze
    └─ Polling/waiting for response
    ↓
Results Page — Full Dashboard
    ├─ ActivityGraph — Commit timeline
    ├─ TechStackChart — Language breakdown
    ├─ ArchDiagram — Architecture visualization
    ├─ StatsBadges — Stars, forks, issues
    ├─ ScoreRing — Code quality score (0–100)
    └─ Reference Strips — Links to GitHub graphs
```

### File Structure

```
gitfit/
├── backend/
│   ├── main.py                    # FastAPI app entry point
│   ├── api/
│   │   ├── routes.py              # /analyze endpoint + caching
│   │   └── schemas.py             # Pydantic models
│   ├── github/
│   │   ├── reader.py              # GitHub API fetcher
│   │   └── cloner.py              # Repository cloning (v2 feature)
│   ├── agent/
│   │   ├── workflow.py            # LangGraph workflow
│   │   ├── tools.py               # LLM call wrapper
│   │   └── state.py               # Workflow state machine
│   ├── analyzer/                  # Local analysis modules (optional)
│   │   ├── orchestrator.py        # Coordinator
│   │   ├── file_scanner.py        # File tree analysis
│   │   ├── structure_analyzer.py  # Architecture detection
│   │   ├── commit_analyzer.py     # Git history analysis
│   │   ├── contributor_analyzer.py # Contributor metrics
│   │   └── dependency_analyzer.py # Dependency graph
│   ├── prompts/
│   │   └── analysis.py            # LLM prompt templates
│   └── requirements.txt
│
└── frontend/
    ├── src/
    │   ├── main.tsx               # React entry point
    │   ├── app.tsx                # Router setup
    │   ├── pages/
    │   │   ├── Home.tsx           # URL input page
    │   │   ├── Results.tsx        # Analysis dashboard
    │   │   └── NotFound.tsx       # 404 page
    │   ├── components/
    │   │   ├── RepoInput.tsx      # Input form with examples
    │   │   ├── ActivityGraph.tsx  # Commit timeline chart
    │   │   ├── TechStackChart.tsx # Language breakdown
    │   │   ├── StatsBadge.tsx     # Metric badges
    │   │   ├── ArchDiagram.tsx    # Architecture flow
    │   │   ├── LoadingSpinner.tsx # Loading state
    │   │   └── ...
    │   ├── hooks/
    │   │   └── useAnalysis.ts     # State machine hook
    │   ├── api/
    │   │   └── client.ts          # HTTP wrapper
    │   └── types/
    │       └── index.ts           # TypeScript interfaces
    ├── package.json
    ├── vite.config.ts
    ├── tailwind.config.ts
    └── index.html
```

---

## 🔌 API Reference

### POST /analyze

**Request:**
```json
{
  "url": "https://github.com/owner/repo"
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "meta": { "owner": "...", "name": "...", ... },
    "languages": [ { "language": "TypeScript", "bytes": 123456, "percentage": 45.2 }, ... ],
    "contributors": [ { "login": "...", "contributions": 42, ... }, ... ],
    "activity": [ { "week": "2025-01-05T00:00:00Z", "commits": 10, "additions": 150, "deletions": 30 }, ... ],
    "architecture": { "summary": "...", "patterns": [ "MVC", "REST API" ], ... },
    "code_quality": { "score": 72, "has_tests": true, "notes": [...] },
    "security": { "has_env_example": true, "exposes_secrets": false, ... },
    "analyzed_at": "2025-01-20T14:30:00Z"
  }
}
```

### GET /health

**Response:**
```json
{
  "status": "ok",
  "version": "0.3.0"
}
```

---

## 🛠️ Environment Variables

### Backend (.env)

```bash
# GitHub API authentication (optional but recommended)
GITHUB_TOKEN=ghp_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx

# LLM configuration (optional)
GROQ_API_KEY=gsk_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
LLM_MODEL=llama-3.3-70b-versatile  # or llama-3-8b-8192
```

### Frontend (.env.local)

```bash
# API endpoint
VITE_API_URL=http://localhost:8000
```

---

## 📊 Data Sources

### GitHub REST API (required)

- **Repository metadata** — `/repos/{owner}/{repo}`
- **Languages** — `/repos/{owner}/{repo}/languages`
- **Contributors** — `/repos/{owner}/{repo}/contributors`
- **Weekly activity** — `/repos/{owner}/{repo}/stats/commit_activity` + `/stats/code_frequency`
- **README** — `/repos/{owner}/{repo}/readme`
- **File tree** — `/repos/{owner}/{repo}/git/trees/{branch}?recursive=1`

**Rate limits:**
- **Without token:** 60 requests/hour per IP
- **With token:** 5,000 requests/hour per user

### LLM (optional)

- **Provider:** Groq
- **Models:** `llama-3.3-70b-versatile`, `llama-3-8b-8192`
- **Used for:** Architecture insights, code quality scoring refinement
- **Fallback:** Heuristic-only if unavailable

---

## 🔒 Security & Privacy

- ✅ **No data persistence** — analysis runs in-memory, results discarded after response
- ✅ **Public repos only** — private repos require authenticated access token
- ✅ **No user account required** — completely anonymous queries
- ✅ **CORS enabled** — frontend and backend communicate securely
- ✅ **Rate limit handling** — graceful degradation when GitHub API limits hit

---

## 🎨 Design System

### Color Palette
- **Navy Blue** (`#1a3a8f`) — Primary brand color
- **Bold Red** (`#cc1f1f`) — Accent and alerts
- **Sky Blue** (`#5a8fd8`) — Secondary accents
- **Ink Dark** (`#0a1128`) — Text
- **Mist Gray** (`#f0f4f8`) — Backgrounds

### Typography
- **Syne** — Headlines (Google Fonts, wght 400–800)
- **JetBrains Mono** — Code and metrics (Google Fonts, wght 400–700)
- **Segoe UI / sans-serif** — Fallback

### Component Library
- **Glassmorphism cards** with blur and saturation
- **Animated gradient borders**
- **Bento grid layout** (CSS Grid)
- **Smooth transitions** (cubic-bezier)
- **Responsive design** (mobile-first)

---

## 🚦 Development Workflow

### Running Tests
```bash
cd backend
pytest tests/

cd ../frontend
npm run test
```

### Building for Production
```bash
# Backend
cd backend
pip install -r requirements.txt
uvicorn main:app --host 0.0.0.0 --port 8000

# Frontend
cd frontend
npm run build
npm run preview
```

### Linting & Formatting
```bash
# Backend
black backend/
flake8 backend/

# Frontend
npm run lint
npm run format
```

---

## 📈 Performance & Optimization

### Caching Strategy
- **10-minute TTL** for repository analyses
- **In-memory cache** (SimpleCache) for reduced API calls
- **Concurrent requests** via `asyncio.gather()` in `fetch_repo()`

### Frontend Optimizations
- **Code splitting** via Vite
- **Lazy component loading** with React.lazy()
- **Image optimization** via GitHub Open Graph API
- **CSS variable theming** for consistent design

### Backend Optimizations
- **Async/await** throughout for non-blocking I/O
- **Retry logic** for GitHub stats endpoints (202 handling)
- **Defensive logging** at key pipeline stages

---

## 🐛 Troubleshooting

### "Repository not found" (404)
- ✓ Check the URL is public (private repos require auth token)
- ✓ Ensure the repo exists on GitHub
- ✓ Add `GITHUB_TOKEN=ghp_...` to `.env` for higher rate limits

### "Commit activity timeline is empty"
- ✓ GitHub stats API returns data lazily — may take a few minutes for new repos
- ✓ Check `/stats/commit_activity` endpoint directly: `curl https://api.github.com/repos/owner/repo/stats/commit_activity -H "Authorization: Bearer $GITHUB_TOKEN"`
- ✓ See `routes.py` logging for diagnostic info

### "Rate limit exceeded (429)"
- ✓ Add `GITHUB_TOKEN=ghp_...` to backend `.env`
- ✓ Without token: 60 req/hour; with token: 5,000 req/hour
- ✓ Wait 1 hour for limit to reset

### "LLM analysis failed (GROQ_API_KEY not set)"
- ✓ This is non-fatal — system falls back to heuristics
- ✓ To enable LLM: set `GROQ_API_KEY=gsk_...` in `.env`

### "CORS errors when hitting backend"
- ✓ Ensure backend is running on `http://localhost:8000`
- ✓ Check `vite.config.ts` proxy settings point to correct URL
- ✓ Set `VITE_API_URL` in frontend `.env.local`

---

## 📚 Documentation

- **Architecture decision records** — See `docs/adr/` (if available)
- **API schema definitions** — `backend/api/schemas.py`
- **GitHub API reference** — https://docs.github.com/en/rest
- **Groq API docs** — https://console.groq.com/docs

---

## 🤝 Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

### Code Style
- **Backend:** Black (line length 100), flake8, type hints
- **Frontend:** Prettier, ESLint, TypeScript strict mode

---

## 📄 License

This project is licensed under the **MIT License** — see the [LICENSE](LICENSE) file for details.

---

## 👤 Author

**Shivam** — [@autumn-xn](https://github.com/autumn-xn)

---

## 🙏 Acknowledgments

- **GitHub** for the excellent REST API
- **Groq** for high-speed LLM inference
- **React**, **FastAPI**, **Vite** communities
- Inspired by GitHub's own code insights and analytics dashboards

---

## 📞 Support

- 💬 **Issues & Bugs:** [GitHub Issues](https://github.com/autumn-xn/gitfit/issues)
- 📧 **Email:** (contact info if applicable)
- 🐦 **Twitter/X:** [@autumn-xn](https://twitter.com/autumn-xn) (if applicable)

---

## 🗺️ Roadmap

- [ ] **v0.4** — Local repository cloning & deep file analysis (optional)
- [ ] **v0.5** — Batch analysis API (analyze multiple repos)
- [ ] **v1.0** — Export analysis as PDF / Markdown report
- [ ] **v1.1** — Team dashboard with repository comparison
- [ ] **v1.2** — GitHub App for integrated in-repo insights
- [ ] **v2.0** — Self-hosted deployment guide & Docker Compose

---

**Made with ❤️ by Shivam**

*Last updated: January 2025*

Project is somehow completed. 
