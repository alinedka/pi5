from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .ia import escolher_jogada

app = FastAPI(title="PI5 IA Player")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/move")
def move(payload: dict):
    return escolher_jogada(payload)
