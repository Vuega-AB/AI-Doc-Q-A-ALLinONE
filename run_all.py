import subprocess
import time
import sys

# List to keep track of the running server processes
processes = []

def cleanup_processes():
    """Function to terminate all running child processes."""
    print("\n--- Shutting down server processes... ---")
    for p in processes:
        p.terminate() # Send termination signal
    print("Shutdown complete.")

if __name__ == "__main__":
    print("--- Launching Flask and Gradio servers in separate processes ---")

    # We use a try...finally block to ensure that no matter how the script exits,
    # we attempt to clean up the child processes.
    try:
        # Command to run the Flask server
        # We use sys.executable to ensure we use the same Python interpreter
        # that is running this script.
        flask_command = [sys.executable, "main_flask_app.py"]
        
        # Command to run the Gradio server
        gradio_command = [sys.executable, "gradio_server.py"]

        print(f"Starting Flask server with command: {' '.join(flask_command)}")
        flask_process = subprocess.Popen(flask_command)
        processes.append(flask_process)
        print(f"Flask server started with PID: {flask_process.pid}")

        # Small delay to allow servers to start up and print their messages cleanly
        time.sleep(2) 

        print(f"Starting Gradio server with command: {' '.join(gradio_command)}")
        gradio_process = subprocess.Popen(gradio_command)
        processes.append(gradio_process)
        print(f"Gradio server started with PID: {gradio_process.pid}")

        print("\n*** Both servers are running. Press CTRL+C to stop all. ***\n")

        # Wait indefinitely until the user interrupts
        while True:
            time.sleep(1)

    except KeyboardInterrupt:
        # This block is triggered when the user presses CTRL+C
        print("\n--- KeyboardInterrupt received. ---")
    except Exception as e:
        print(f"\n--- An unexpected error occurred: {e} ---")
    finally:
        # This block will run whether the script exits normally,
        # via CTRL+C, or from an error.
        cleanup_processes()