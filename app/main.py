import os

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.auth.routes import router as auth_router
from app.reviews.routes import router as reviews_router
from app.routes.chat import router as chat_router
from app.routes.mindmap import router as mindmap_router
from app.routes.result import router as result_router
from app.routes.status import router as status_router
from app.routes.summarize import router as summarize_router
from app.routes.transcript import router as transcript_router

load_dotenv()

FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:5173")

app = FastAPI()

# ---------------- CORS ----------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=[FRONTEND_URL],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------- ROUTES ----------------
app.include_router(summarize_router)
app.include_router(status_router)
app.include_router(result_router)
app.include_router(chat_router)
app.include_router(mindmap_router)
app.include_router(transcript_router)
app.include_router(
    auth_router,
    prefix="/auth",
    tags=["Authentication"],
)
app.include_router(reviews_router)


@app.get("/")
def root():
    return {"status": "ClipMind API running"}