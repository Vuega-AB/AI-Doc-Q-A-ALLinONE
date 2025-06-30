# Gunicorn configuration file

# This function will be called in each worker process after it's forked.
def post_fork(server, worker):
    # This is the crucial part:
    # It patches the standard libraries to be gevent-friendly.
    # This must happen before our app, which imports things like 'requests'
    # and 'threading', is loaded.
    from gevent import monkey
    monkey.patch_all()

    # Log that the patching has occurred for this worker.
    worker.log.info("Made gevent monkey-patch for worker %s" % worker.pid)