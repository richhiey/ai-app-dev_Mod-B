"""Provider failures must remain actionable without revealing requests or bodies."""
import httpx
import pytest

from module_b.openrouter import OpenRouterClient, OpenRouterError


@pytest.mark.parametrize("status, kind, expected", [
    (401, "provider_auth", "HTTP 401"),
    (402, "provider_credit", "HTTP 402"),
    (403, "provider_access", "HTTP 403"),
    (429, "provider_rate", "HTTP 429"),
    (503, "provider_unavailable", "HTTP 5xx"),
    (400, "provider_rejected", "request settings"),
])
def test_provider_status_is_safe_and_actionable(status, kind, expected):
    client = OpenRouterClient(api_key="synthetic-private-key")
    client._http.close()
    client._http = httpx.Client(transport=httpx.MockTransport(
        lambda request: httpx.Response(status, json={"error": "private-response-secret"})))
    try:
        with pytest.raises(OpenRouterError) as error:
            client.embed(["private-prompt-secret"])
        assert error.value.kind == kind
        assert expected in str(error.value)
        assert "secret" not in str(error.value) and "synthetic-private-key" not in str(error.value)
        assert error.value.__suppress_context__
    finally:
        client.close()


@pytest.mark.parametrize("failure, kind", [
    (httpx.ReadTimeout("private-url-secret"), "provider_timeout"),
    (httpx.ConnectError("private-url-secret"), "provider_network"),
])
def test_network_failures_do_not_expose_transport_details(failure, kind):
    def fail(request):
        raise failure
    client = OpenRouterClient(api_key="synthetic-private-key")
    client._http.close()
    client._http = httpx.Client(transport=httpx.MockTransport(fail))
    try:
        with pytest.raises(OpenRouterError) as error:
            client.embed(["private-prompt-secret"])
        assert error.value.kind == kind
        assert "secret" not in str(error.value)
    finally:
        client.close()
