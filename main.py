from fastapi import FastAPI
from app.api.health import router as health_router
from app.config import APP_HOST, APP_PORT

app = FastAPI(
    title="GigGuard API",
    description="Agentic AI Advocate for India's Gig Workers",
    version="0.1.0"
)

app.include_router(health_router)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host=APP_HOST, port=APP_PORT, reload=True)
