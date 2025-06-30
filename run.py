from starlette.applications import Starlette
from a2wsgi import ASGIMiddleware
import gradio as gr

# Import the FACTORY functions
from main_flask_app import create_flask_app
from gradio_server import create_gradio_demo

def create_app():
    """
    This factory creates the final combined ASGI application that Uvicorn can run.
    It uses a master Starlette app to host both Flask and Gradio.
    """
    print("--- Running Top-Level App Factory for Uvicorn/Starlette ---")
    
    # 1. Create the pure Flask (WSGI) app instance.
    flask_app = create_flask_app()

    # 2. Create the Gradio UI Blocks instance.
    gradio_demo = create_gradio_demo()
    
    # 3. Create the raw ASGI app from Gradio.
    gradio_asgi_app = gr.routes.App.create_app(gradio_demo)

    # 4. Create the master ASGI application.
    master_app = Starlette()

    # 5. Mount the Gradio ASGI app at the "/gradio" path.
    master_app.mount("/gradio", gradio_asgi_app)
    
    # 6. Mount the Flask WSGI app at the root path ("/").
    # The ASGIMiddleware converts it to be compatible.
    # Any request that doesn't match "/gradio" will fall through to here.
    master_app.mount("/", ASGIMiddleware(flask_app))
    
    return master_app