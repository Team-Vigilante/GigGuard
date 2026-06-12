from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from app.api.health import router as health_router
from app.api.webhook import router as webhook_router
from app.api.dashboard import router as dashboard_router
from app.config import APP_HOST, APP_PORT
import logging

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

app = FastAPI(
    title="GigGuard API",
    description="Agentic AI Advocate for India's Gig Workers",
    version="0.1.0"
)

app.include_router(health_router)
app.include_router(webhook_router)
app.include_router(dashboard_router)
app.mount("/dashboard", StaticFiles(directory="dashboard", html=True), name="dashboard")
app.mount("/pdf", StaticFiles(directory="output"), name="pdf")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host=APP_HOST, port=APP_PORT, reload=True)
