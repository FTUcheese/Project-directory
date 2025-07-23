from fastapi import FastAPI
from loguru import logger

app = FastAPI()

@app.get("/")
def read_root():
    logger.info("Root endpoint accessed")
    return {"message": "Welcome to CodePilotX API"}

@app.get("/health")
def health_check():
    logger.info("Health check endpoint accessed")
    return {"status": "ok"}

# To run: uvicorn main:app --reload