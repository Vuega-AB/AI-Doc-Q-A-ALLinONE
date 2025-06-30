# Gunicorn configuration file

# This code now runs in the master process *before* forking,
# because we will use the --preload flag.
print("--- Gunicorn config loaded. Applying gevent monkey-patch early. ---")

try:
    from gevent import monkey
    # We patch everything except 'os' to avoid a known issue with subprocesses.
    monkey.patch_all(os=False) 
    print("--- Gevent monkey-patch applied successfully. ---")
except ImportError:
    print("--- Gevent not found, skipping monkey-patch. ---")

# We no longer need the post_fork hook.
# The preload flag handles this for us.