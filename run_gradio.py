# This file is ONLY for the standalone Gradio service.
import gradio as gr
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import os

# Import the function that creates your Gradio UI
from gradio_ui import create_gradio_app

# Get the URL of your main Flask app from environment variables
# This is crucial for the CORS configuration below.
FLASK_APP_URL = os.getenv("FLASK_APP_URL", "http://localhost:5000")

# 1. Create the main FastAPI app for the Gradio service
app = FastAPI()

# 2. Add CORS middleware. This is CRITICAL.
# It allows your Flask app's domain to load the Gradio iframe.
# Without this, you will get a "refused to connect" error from the browser.
app.add_middleware(
    CORSMiddleware,
    allow_origins=[FLASK_APP_URL],  # The domain of your Flask app
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 3. Create the Gradio UI object
gradio_ui = create_gradio_app()

# 4. Mount the Gradio UI onto the FastAPI app.
#    This is the modern and correct way to run Gradio with custom server settings.
app = gr.mount_gradio_app(
    app=app,
    blocks=gradio_ui,
    path="/"  # Mount it at the root, so it's accessible at the service's main URL
)

print(f"Gradio service starting. Allowing connections from: {FLASK_APP_URL}")