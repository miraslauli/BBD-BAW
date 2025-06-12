from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src import router


app = FastAPI(title="ASzWoj")
app.include_router(router)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
