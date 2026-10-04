"""Fixed learner messages; no provider SDK or application imports."""

PROVIDER_FAILURES = {
    "provider_auth": "OpenRouter rejected the API key (HTTP 401). Update OPENROUTER_API_KEY in Colab Secrets, then restart the runtime and run setup again.",
    "provider_credit": "OpenRouter reported insufficient credits (HTTP 402). Check the account balance and this key's spending limit, then retry the service cell.",
    "provider_access": "OpenRouter denied this request (HTTP 403). Check the key's model permissions and account restrictions before retrying.",
    "provider_rate": "OpenRouter rate-limited the request (HTTP 429). Wait before retrying the service cell.",
    "provider_unavailable": "OpenRouter or its model provider is unavailable (HTTP 5xx). Retry the service cell later.",
    "provider_rejected": "OpenRouter rejected the request. Check the configured model and request settings.",
    "provider_timeout": "The OpenRouter request timed out. Check connectivity and retry the service cell.",
    "provider_network": "Could not connect to OpenRouter. Check runtime connectivity and retry the service cell.",
    "provider_response": "OpenRouter returned an unreadable response. Retry the service cell; report the problem if it repeats.",
    "provider_error": "The OpenRouter operation failed. Check provider access and request settings before retrying.",
}

