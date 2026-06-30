"""
Main FastAPI Application — Entry Point Backend
"""
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import os

from config import settings
from models.database import create_db_and_tables
from routers import auth, folders, files, streaming, sharing, settings as settings_router, setup

@asynccontextmanager
async def lifespan(app: FastAPI):
    create_db_and_tables()
    print("Database siap.")
    print(f"API Docs: http://localhost:{settings.backend_port}/api/docs")

    # ── Auto-reconnect: jika session file ada, konek ulang tanpa login ──
    from routers.setup import get_stored_telegram_config
    from services.telegram_client import telegram_manager
    import os

    cfg = get_stored_telegram_config()
    session_path = os.path.join(settings.session_dir, "user.session")

    if cfg and os.path.exists(session_path):
        try:
            await telegram_manager.initialize(cfg["api_id"], cfg["api_hash"])
            if await telegram_manager.is_authorized():
                print("🔄 Session Telegram dipulihkan otomatis.")
            else:
                print("⚠️  Session file ada tapi tidak authorized. Perlu login ulang.")
        except Exception as e:
            print(f"⚠️  Gagal auto-reconnect Telegram: {e}")
    yield
    # Cleanup here if needed

app = FastAPI(
    title="Telegram Drive Web — API",
    description="Backend API untuk Telegram Drive Web. Dibangun dengan FastAPI + Telethon.",
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    lifespan=lifespan,
)

# ─── CORS Middleware ───────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ─── Routers ──────────────────────────────────────────────
app.include_router(setup.router)           # /api/setup (publik)
app.include_router(auth.router, prefix="/api")
app.include_router(folders.router, prefix="/api")
app.include_router(files.router, prefix="/api")
app.include_router(streaming.router, prefix="/api")
app.include_router(sharing.router)         # /api/share & /s/{token} (publik)
app.include_router(settings_router.router) # /api/settings

# ─── Health Check ─────────────────────────────────────────
@app.get("/api/health", tags=["Health"])
async def health():
    return {"status": "ok", "service": "Telegram Drive Web API"}

# ─── Serve Frontend SPA ───────────────────────────────────
# Berfungsi jika ada folder 'static' yang berisi build dari React
if os.path.exists("static"):
    app.mount("/assets", StaticFiles(directory="static/assets"), name="assets")
    
    @app.get("/{full_path:path}", include_in_schema=False)
    async def serve_spa(full_path: str):
        # Jika request API yang tidak valid (404), biarkan FastAPI menangani
        if full_path.startswith("api/"):
            raise HTTPException(status_code=404, detail="Not Found")
            
        # Cek file statis lainnya (vite.svg, favicon.ico, dll)
        path = os.path.join("static", full_path)
        if os.path.isfile(path):
            return FileResponse(path)
            
        # Fallback ke index.html untuk React Router
        return FileResponse("static/index.html")
