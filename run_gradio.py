# In run_gradio.py
import gradio as gr
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import os

from backend import initialize_all_components
from gradio_ui import create_gradio_app

# Initialize backend components
initialize_all_components()

# Get the URLs from environment variables
FLASK_BASE_URL = os.getenv("FLASK_BASE_URL")
GRADIO_SERVICE_URL = os.getenv("GRADIO_APP_URL") # This should be 'https://intellaw-gradio-app.onrender.com'

app = FastAPI()

# Add CORS middleware to allow the Flask app to connect
app.add_middleware(
    CORSMiddleware,
    allow_origins=[FLASK_BASE_URL],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

gradio_ui = create_gradio_app()

# Mount the Gradio UI using the older 'root_path' argument
app = gr.mount_gradio_app(
    app=app,
    blocks=gradio_ui,
    path="/",
    root_path=GRADIO_SERVICE_URL  # <-- Use the older, more compatible argument
)