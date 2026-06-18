# ─── backend/main.py ──────────────────────────────────────────────────────────
import logging
import os
import sys
from pathlib import Path
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# ✅ ADD BACKEND TO PATH so it can find api module
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

# Must be called before any os.getenv() reads happen
load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(levelname)-8s %(name)s  %(message)s",
)
log = logging.getLogger("github_analyzer")

app = FastAPI(
    title="GitHub Analyzer API",
    version="0.3.0",
    description="AI-powered GitHub repository analysis — GitFit v2",
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

# ✅ NOW THIS WORKS
from api.routes import router
app.include_router(router)

@app.get("/", tags=["meta"])
async def root():
    return {
        "message": "GitFit API is running",
        "version": "0.3.0",
        "docs": "/docs",
    }

if __name__ == "__main__":
    import uvicorn
    log.info("Starting GitFit API...")
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)