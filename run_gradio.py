# In run_gradio.py
import gradio as gr
from fastapi import FastAPI, Request # <--- Make sure Request is imported
from fastapi.middleware.cors import CORSMiddleware
import os
from backend import initialize_all_components
from gradio_ui import create_gradio_app

initialize_all_components()

FLASK_BASE_URL = os.getenv("FLASK_BASE_URL", "http://localhost:5000")
app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=[FLASK_BASE_URL],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

gradio_ui = create_gradio_app()

app = gr.mount_gradio_app(
    app=app,
    blocks=gradio_ui,
    path="/",
    root_path_in_global_scope=False # <--- CRITICAL
)

@app.middleware("http")
async def set_root_path(request: Request, call_next): # <--- CRITICAL
    host = request.headers.get("x-forwarded-host", request.headers.get("host"))
    proto = request.headers.get("x-forwarded-proto", "http")
    request.scope["root_path"] = f"{proto}://{host}"
    response = await call_next(request)
    return response