from fastapi import FastAPI

from database import engine, Base
import models

Base.metadata.create_all(bind=engine)

app = FastAPI(title="SmartBiz_AI")


@app.get("/")
def home():
    return {"message": "SmartBiz_AI Backend is running"}


@app.get("/health")
def health_check():
    return {"status": "ok"}