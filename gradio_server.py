import os
from dotenv import load_dotenv

# Import the function that creates the Gradio UI
from gradio_ui import create_gradio_app
# Import the backend initialization function
from backend import initialize_all_components

def create_gradio_demo():

    GRADIO_SERVER_INITIALIZED = False

    def run_gradio_server_initializations():
        global GRADIO_SERVER_INITIALIZED
        if not GRADIO_SERVER_INITIALIZED:
            print("Running initializations for Gradio Server process...")
            default_db = os.getenv("DEFAULT_DB_BACKEND", "MongoDB")
            initialize_all_components(default_db=default_db)
            GRADIO_SERVER_INITIALIZED = True
            print("Gradio Server initializations completed.")
        else:
            print("Gradio Server initializations already run.")

    # --- MOVED THESE LINES OUTSIDE THE __main__ BLOCK ---
    # This code will now run every time the file is processed,
    # whether it's run directly or imported by another script.

    load_dotenv() # Load .env for local development

    print("Gradio Server file is being processed...")
    run_gradio_server_initializations() # Initialize backend components

    print("Creating Gradio app object (demo)...")
    # This 'demo' is now defined at the top level, so it can be imported.
    demo = create_gradio_app()
    # --------------------------------------------------------
    return demo


    # if __name__ == "__main__":
    #     # This block will ONLY run if you execute "python gradio_server.py" directly.
    #     # It will NOT run when this file is imported by run_all.py.
        
    #     # Get the port from the environment variable set by Render (or default for local)
    #     gradio_port = int(os.getenv("GRADIO_PORT", 7860))
    #     print(f"Attempting to launch Gradio server on 0.0.0.0:{gradio_port}...")

    #     try:
    #         # The launch command stays here. run_all.py will call this method on its own.
    #         demo.launch(
    #             server_name="0.0.0.0",
    #             server_port=gradio_port,
    #             share=False,
    #             inbrowser=False,
    #         )
    #         print(f"Gradio server successfully launched and should be listening on port {gradio_port}.")
    #     except Exception as e:
    #         print(f"CRITICAL ERROR: Failed to launch Gradio server on port {gradio_port}.")
    #         print(f"Error details: {e}")
    #         import sys
    #         sys.exit(1)