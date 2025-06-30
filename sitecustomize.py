# This file is automatically run by Python on startup.
# This is the absolute earliest we can apply the monkey-patch.
try:
    from gevent import monkey
    # We patch everything, as this is now the first thing to run.
    monkey.patch_all()
    print("--- sitecustomize.py: Gevent monkey-patch applied successfully. ---")
except ImportError:
    print("--- sitecustomize.py: Gevent not found, skipping patch. ---")
except Exception as e:
    print(f"--- sitecustomize.py: Error during monkey-patch: {e} ---")