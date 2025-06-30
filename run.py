import gradio as gr
from starlette.applications import Starlette
from a2wsgi import ASGIMiddleware

# Import the FACTORY functions
from main_flask_app import create_flask_app
from gradio_server import create_gradio_demo

def create_app():
    """
    This factory creates the final combined ASGI application.
    It builds a base Starlette app to host Flask, then mounts Gradio onto it.
    """
    print("--- Running Final App Factory with Starlette Host ---")
    
    # 1. Create the pure Flask (WSGI) app instance.
    flask_app = create_flask_app()

    # 2. Create the Gradio UI Blocks instance.
    gradio_demo = create_gradio_demo()
    
    # 3. Create a clean Starlette application. Its ONLY job is to host our Flask app.
    #    This correctly converts Flask to a pure ASGI application that Gradio can understand.
    flask_host_app = Starlette()
    flask_host_app.mount("/", ASGIMiddleware(flask_app))

    # 4. Now, use Gradio's official mounting function.
    #    We give it our `flask_host_app` as the base. Gradio knows how to handle
    #    a pure Starlette app perfectly. It will add its "/gradio" route
    #    to the routes from the flask_host_app.
    final_combined_app = gr.mount_gradio_app(
        app=flask_host_app,
        blocks=gradio_demo,
        path="/gradio"
    )
    
    return final_combined_app