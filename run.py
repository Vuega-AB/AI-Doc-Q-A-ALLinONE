import gradio as gr

# Import the app instances from your other files
from main_flask_app import app as flask_app
from gradio_server import demo as gradio_app

def create_app():
    """
    This is our application factory. Gunicorn will call this function
    to get the final, combined application object.
    """
    print("--- Running App Factory: Mounting Gradio onto Flask ---")
    
    # Mount the Gradio app onto a path within the Flask app.
    # This returns a new, combined application object.
    combined_app = gr.mount_gradio_app(flask_app, gradio_app, path="/gradio")
    
    # Return the final app that Gunicorn will serve.
    return combined_app

# Gunicorn will be pointed to create_app() instead of a global 'app' variable.
# We don't need a global 'app' variable here anymore.