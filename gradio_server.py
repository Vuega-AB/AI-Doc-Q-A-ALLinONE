import os
from dotenv import load_dotenv
from gradio_ui import create_gradio_app

def create_gradio_demo(root_path: str = ""):
    print("--- Creating Gradio Demo Instance ---")
    load_dotenv()
    demo = create_gradio_app()
    demo.root_path = root_path
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