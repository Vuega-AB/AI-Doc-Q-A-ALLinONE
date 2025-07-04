# In main.py

import os
import gradio as gr  # <<< IMPORTANT: Import gradio
from fastapi import FastAPI
from starlette.middleware.wsgi import WSGIMiddleware
from dotenv import load_dotenv
from gradio_ui import create_gradio_app

def create_gradio_demo():
    print("--- Creating Gradio Demo Instance ---")
    load_dotenv()
    demo = create_gradio_app()
    return demo
# Import your app creation functions
from main_flask_app import create_flask_app
# from gradio_server import create_gradio_demo  # <<< Use the new function name

# Create the main FastAPI app that will act as the router
app = FastAPI()

# --- NEW MOUNTING LOGIC ---

# 1. Get the Gradio UI object (the gr.Blocks instance)
gradio_interface = create_gradio_demo()

flask_app = create_flask_app()
# 2. Use the official Gradio function to mount the UI onto our FastAPI app.
#    This handles all the complex pathing internally.
#    This must be done BEFORE mounting the Flask app.
app = gr.mount_gradio_app(
    app=app,                  # The FastAPI app to mount onto
    blocks=gradio_interface,  # The Gradio UI object
    path="/gradio"            # The path to mount it at
)

# 3. Create the Flask app and mount it at the root.
#    This should be done LAST so it handles any routes not caught by Gradio.

app.mount("/", WSGIMiddleware(flask_app))