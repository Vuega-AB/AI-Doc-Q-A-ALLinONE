import gradio as gr
from a2wsgi import WSGIMiddleware

# Import the FACTORY functions
from main_flask_app import create_flask_app
from gradio_server import create_gradio_demo

def create_app():
    """
    This factory creates the final combined ASGI application that Uvicorn can run.
    """
    print("--- Running Top-Level App Factory for Uvicorn ---")
    
    # 1. Create the pure Flask (WSGI) app instance.
    # This also handles the single backend initialization.
    flask_app = create_flask_app()

    # 2. Create the Gradio UI Blocks instance.
    gradio_demo = create_gradio_demo()
    
    # 3. THIS IS THE CRITICAL STEP:
    # Convert the pure Flask WSGI app into an ASGI app using the middleware.
    flask_asgi_app = WSGIMiddleware(flask_app)

    # 4. Now, mount the Gradio app onto the *ASGI-converted* Flask app.
    # This will succeed because both are now speaking the same ASGI protocol.
    # gr.mount_gradio_app returns a Starlette app, which is pure ASGI.
    combined_app = gr.mount_gradio_app(
        flask_asgi_app,         # The app to mount ON (now ASGI)
        gradio_demo,            # The app to mount
        path="/gradio"          # The path for Gradio
    )
    
    return combined_app