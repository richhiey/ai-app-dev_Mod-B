"""Supplied narrow prevention: select safe diagnostic fields before serialization."""
def log_record(event, error=None):
    return {'request_id':event['request_id'], 'route':event['route'],
            'status':event['status'], 'error_code':'upstream_failed' if error else None}
