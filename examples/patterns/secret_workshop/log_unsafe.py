"""INTENTIONALLY UNSAFE synthetic fixture: forwards headers and exception text."""
def log_record(event, error=None):
    return {**event, 'error':str(error) if error else None}
