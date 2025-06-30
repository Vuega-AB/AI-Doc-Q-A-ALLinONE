from starlette.applications import Starlette
from starlette.routing import Mount  # <<< THE CORRECT IMPORT
from a2wsgi import ASGIMiddleware
import gradio as gr

# Import the FACTORY functions
from main_flask_app import create_flask_app
from gradio_server import create_gradio_demo

def create_app():
    """
    This factory creates the final combined ASGI application using a master
    Starlette router to host both Flask and Gradio on different paths.
    """
    print("--- Running Final App Factory with Master Starlette Router ---")
    
    # 1. Create the underlying app instances
    flask_app = create_flask_app()
    gradio_demo = create_gradio_demo()
    
    # 2. Convert the Flask WSGI app into an ASGI app
    flask_asgi = ASGIMiddleware(flask_app)

    # 3. Create the raw ASGI app from the Gradio Blocks
    gradio_asgi = gr.routes.App.create_app(gradio_demo)

    # 4. Create the master router application
    master_app = Starlette(routes=[
        # A request to "/gradio" or "/gradio/..." will be handled by the Gradio app
        Mount("/gradio", app=gradio_asgi, name="gradio_app"),  # <<< THE CORRECT USAGE
        
        # Any other request will fall through and be handled by the Flask app
        Mount("/", app=flask_asgi, name="flask_app"), # <<< THE CORRECT USAGE
    ])
    
    return master_app