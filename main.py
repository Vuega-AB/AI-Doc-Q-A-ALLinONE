import os
from fastapi import FastAPI
from starlette.middleware.wsgi import WSGIMiddleware

# Import your app creation functions
from main_flask import create_flask_app
from gradio_server import create_gradio_demo

# Create the main FastAPI app that will act as the router
app = FastAPI()

# Create instances of your Flask and Gradio apps
flask_app = create_flask_app()
gradio_app = create_gradio_demo()

# Mount the Gradio app at the "/gradio" path. 
# All requests to your-url.onrender.com/gradio/* will be handled by Gradio.
app.mount("/gradio", gradio_app)

# Mount the Flask app at the root path "/".
# This uses a WSGI-to-ASGI middleware to make Flask compatible.
# All other requests will be handled by Flask (e.g., /login, /settings, /)
app.mount("/", WSGIMiddleware(flask_app))

# This part is optional but useful for local testing without run_all.py
if __name__ == "__main__":
    import uvicorn
    # Use the port from the environment variable PORT, which Render sets
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=True)