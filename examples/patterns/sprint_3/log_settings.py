# Deliberate metadata allowlist. Never add request bodies, headers or exception text.
LOG_FIELDS=('request_id','route','status_code','outcome','source','model','tokens',
            'latency_ms','first_content_ms','error_category','case_id')
