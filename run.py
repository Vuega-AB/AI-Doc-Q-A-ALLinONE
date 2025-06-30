import gradio as gr

# Import the FACTORY functions
from main_flask_app import create_flask_app
from gradio_server import create_gradio_demo

def create_app():
    """
    This factory creates and mounts the apps. It returns a pure ASGI application
    that Uvicorn can run directly.
    """
    print("--- Running Top-Level App Factory for Uvicorn ---")
    
    flask_app = create_flask_app()
    gradio_demo = create_gradio_demo()
    
    # This was our very first attempt, and it is the correct one for an ASGI server.
    # It returns an ASGI-compatible Starlette application.
    combined_app = gr.mount_gradio_app(flask_app, gradio_demo, path="/gradio")
    
    return combined_app