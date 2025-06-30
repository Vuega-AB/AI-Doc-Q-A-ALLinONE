import gradio as gr
from a2wsgi import ASGIMiddleware

# Import the FACTORY functions
from main_flask_app import create_flask_app
from gradio_server import create_gradio_demo

def create_app():
    """
    This is our application factory.
    It creates the Flask and Gradio apps and combines them manually
    for maximum compatibility with Gunicorn.
    """
    print("--- Running Top-Level App Factory ---")
    
    # 1. Create the Flask app instance (this also handles DB init)
    flask_app = create_flask_app()
    
    # 2. Create the Gradio demo instance
    gradio_demo = create_gradio_demo()
    
    # 3. THIS IS THE KEY CHANGE:
    # Instead of gr.mount_gradio_app, we create the Gradio ASGI app first.
    gradio_asgi_app = gr.routes.App.create_app(gradio_demo)
    
    # 4. Then, we mount the Gradio ASGI app as a middleware onto a specific path
    #    of our main Flask (WSGI) app.
    #    The ASGIMiddleware handles the conversion between the two protocols.
    flask_app.wsgi_app = ASGIMiddleware(
        gradio_asgi_app,
        mount_path="/gradio",
        app=flask_app.wsgi_app
    )
    
    # 5. Return the *original* Flask app. It has now been modified
    #    to internally handle the /gradio path.
    return flask_app

# The Procfile command "gunicorn 'run:create_app()'" remains the same.