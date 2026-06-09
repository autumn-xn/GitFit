# ─── backend/main.py ──────────────────────────────────────────────────────────
# Step 3 — Refactoring.
# Pydantic models are in api/schemas.py, and routes/logic in api/routes.py.
#
# Run with:  uvicorn main:app --reload
# Or:        python main.py
# ──────────────────────────────────────────────────────────────────────────────

import logging
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Must be called before any os.getenv() reads happen
load_dotenv()

# ─── Logging ──────────────────────────────────────────────────────────────────

logging.basicConfig(
    level=logging.INFO,
    format="%(levelname)-8s %(name)s  %(message)s",
)
log = logging.getLogger("github_analyzer")

# ─── FastAPI app ──────────────────────────────────────────────────────────────

app = FastAPI(
    title="GitHub Analyzer API",
    version="0.3.0",
    description="AI-powered GitHub repository analysis — Refactored",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://localhost:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─── Import and Register Routes ───────────────────────────────────────────────

from api.routes import router
app.include_router(router)

# ─── Dev entry point ──────────────────────────────────────────────────────────

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)