import gradio as gr

# Import the FACTORY functions, not the app objects
from main_flask_app import create_flask_app
from gradio_server import create_gradio_demo

def create_app():
    """
    This is our application factory. Gunicorn will call this function
    to get the final, combined application object.
    """
    print("--- Running Top-Level App Factory ---")
    
    # 1. Create the Flask app instance (this also handles DB init)
    flask_app = create_flask_app()
    
    # 2. Create the Gradio demo instance
    gradio_app = create_gradio_demo()
    
    # 3. Mount Gradio onto Flask. This must happen inside the factory.
    print("--- Mounting Gradio onto Flask ---")
    combined_app = gr.mount_gradio_app(flask_app, gradio_app, path="/gradio")
    
    return combined_app

# The Procfile command "gunicorn 'run:create_app()'" remains the same.