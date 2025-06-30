import gradio as gr
from starlette.applications import Starlette
from a2wsgi import ASGIMiddleware

# Import the FACTORY functions
from main_flask_app import create_flask_app
from gradio_server import create_gradio_demo

def create_app():
    """
    This factory creates the final combined ASGI application that Uvicorn can run.
    It builds a base Starlette app for Flask, then mounts Gradio onto it.
    """
    print("--- Running Final App Factory for Uvicorn/Starlette ---")
    
    # 1. Create the pure Flask (WSGI) app instance.
    flask_app = create_flask_app()

    # 2. Create the Gradio UI Blocks instance.
    gradio_demo = create_gradio_demo()
    
    # 3. Create a clean Starlette application that will host our Flask app.
    #    This is the base that Gradio will mount onto.
    flask_host_app = Starlette()
    flask_host_app.mount("/", ASGIMiddleware(flask_app))

    # 4. Now, use Gradio's official mounting function.
    #    We give it our `flask_host_app` (which is a pure Starlette ASGI app)
    #    as the application to mount ONTO. Gradio's function knows how to handle
    #    a Starlette app perfectly.
    final_combined_app = gr.mount_gradio_app(
        app=flask_host_app,
        blocks=gradio_demo,
        path="/gradio"
    )
    
    return final_combined_app