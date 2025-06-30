import os
import gradio as gr

# Import the Flask app instance from your frontend file
from main_flask_app import app as flask_app
# Import the Gradio Blocks instance from your server file
from gradio_server import demo as gradio_app

# The magic line: Mount the Gradio app onto a path within the Flask app.
# Any request to your public URL at "/gradio" will now be handled by the Gradio app.
app = gr.mount_gradio_app(flask_app, gradio_app, path="/gradio")

# The gunicorn server will run this 'app' object.