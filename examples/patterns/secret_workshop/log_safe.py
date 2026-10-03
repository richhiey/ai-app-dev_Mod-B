"""Select safe diagnostic fields before serialization; never keep raw headers/errors."""
def log_record(event, error=None):
    return {'request_id':event['request_id'], 'route':event['route'],
            'outcome':event['outcome'], 'error_code':'operation_failed' if error else None}
