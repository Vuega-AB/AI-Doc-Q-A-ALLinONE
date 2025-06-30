import gradio as gr
from a2wsgi import ASGIMiddleware

# Import the FACTORY functions at the top
from main_flask_app import create_flask_app
from gradio_server import create_gradio_demo

def create_app():
    """
    This is our application factory.
    It creates the Flask and Gradio apps and combines them manually
    for maximum compatibility with Gunicorn.
    """
    print("--- Running Top-Level App Factory ---")
    
    flask_app = create_flask_app()
    gradio_demo = create_gradio_demo()
    
    # Create the raw ASGI app from Gradio
    gradio_asgi_app = gr.routes.App.create_app(gradio_demo)

    # This is the new, more compatible way to mount.
    class PathDispatcher:
        def __init__(self, default_app, mount_app, mount_path):
            self.default_app = default_app
            self.mount_app = mount_app
            self.mount_path = mount_path

        def __call__(self, environ, start_response):
            if environ['PATH_INFO'].startswith(self.mount_path):
                # Manually adjust the path for the mounted app
                environ['PATH_INFO'] = environ['PATH_INFO'][len(self.mount_path):]
                environ['SCRIPT_NAME'] = self.mount_path
                return self.mount_app(environ, start_response)
            else:
                return self.default_app(environ, start_response)

    # Wrap the Gradio ASGI app so it behaves like a WSGI app
    gradio_wsgi_wrapper = ASGIMiddleware(gradio_asgi_app)

    # Create the final dispatched app
    dispatched_app = PathDispatcher(flask_app.wsgi_app, gradio_wsgi_wrapper, '/gradio')

    # Set the flask app's wsgi_app to our new dispatcher
    flask_app.wsgi_app = dispatched_app
    
    return flask_app