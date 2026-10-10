import httpx
import pytest
from app.integrations import tools


@pytest.fixture(autouse=True)
def public_dns(monkeypatch):
    monkeypatch.setattr(
        tools.socket,
        "getaddrinfo",
        lambda *args, **kwargs: [(2, 1, 6, "", ("93.184.216.34", 443))],
    )


def test_private_and_non_https_sources_rejected(monkeypatch):
    with pytest.raises(tools.ToolError):
        tools.validate_url("http://example.com")
    with pytest.raises(tools.ToolError):
        tools.validate_url("https://user:password@example.com")
    monkeypatch.setattr(
        tools.socket,
        "getaddrinfo",
        lambda *a, **kw: [(2, 1, 6, "", ("127.0.0.1", 443))],
    )
    with pytest.raises(tools.ToolError):
        tools.validate_url("https://localhost")


def test_provider_http_failure_is_not_success():
    transport = httpx.MockTransport(
        lambda request: httpx.Response(503, text="internal credential-like detail")
    )
    with pytest.raises(tools.ToolError, match="HTTP 503"):
        tools.fetch_text("https://example.com", transport=transport)


def test_redirect_is_not_followed():
    transport = httpx.MockTransport(
        lambda request: httpx.Response(302, headers={"Location": "https://localhost"})
    )
    with pytest.raises(tools.ToolError, match="HTTP 302"):
        tools.fetch_text("https://example.com", transport=transport)


def test_response_size_is_bounded():
    transport = httpx.MockTransport(
        lambda request: httpx.Response(200, content=b"x" * (tools.MAX_BYTES + 1))
    )
    with pytest.raises(tools.ToolError, match="512 KB"):
        tools.fetch_text("https://example.com", transport=transport)


def test_email_without_credentials_does_not_make_http_request(monkeypatch):
    for key in ["MAILTRAP_API_TOKEN", "MAILTRAP_ACCOUNT_ID", "MAILTRAP_INBOX_ID"]:
        monkeypatch.delenv(key, raising=False)
    with pytest.raises(tools.NotConnected):
        tools.read_email(5)


def test_email_sandbox_contract_uses_real_api_shapes_with_mocked_transport(monkeypatch):
    monkeypatch.setenv("MAILTRAP_API_TOKEN", "test-token")
    monkeypatch.setenv("MAILTRAP_ACCOUNT_ID", "123")
    monkeypatch.setenv("MAILTRAP_INBOX_ID", "456")
    seen = []

    def handler(request):
        seen.append(str(request.url))
        assert request.headers["Api-Token"] == "test-token"
        if request.url.path.endswith("/body.txt"):
            return httpx.Response(
                200, text="Name: Ada Mensah\nEmail: ada.mensah@example.com\nEVT-101"
            )
        return httpx.Response(200, json=[{"id": 789, "subject": "Registration"}])

    result = tools.read_email(5, httpx.MockTransport(handler))
    assert len(result["messages"]) == 1
    assert seen == [
        "https://mailtrap.io/api/accounts/123/inboxes/456/messages",
        "https://mailtrap.io/api/accounts/123/inboxes/456/messages/789/body.txt",
    ]
    assert "test-token" not in str(result)


def configure_test_mailtrap(monkeypatch):
    monkeypatch.setenv("MAILTRAP_API_TOKEN", "test-token")
    monkeypatch.setenv("MAILTRAP_ACCOUNT_ID", "123")
    monkeypatch.setenv("MAILTRAP_INBOX_ID", "456")


def test_connected_empty_mailtrap_inbox_is_success(monkeypatch):
    configure_test_mailtrap(monkeypatch)
    calls = []

    def handler(request):
        calls.append(request.url.path)
        return httpx.Response(200, json=[])

    result = tools.read_email(1, httpx.MockTransport(handler))
    assert result["messages"] == []
    assert calls == ["/api/accounts/123/inboxes/456/messages"]


@pytest.mark.parametrize("status", [401, 403, 503])
def test_mailtrap_http_failure_is_distinct_from_empty_inbox(monkeypatch, status):
    configure_test_mailtrap(monkeypatch)
    transport = httpx.MockTransport(
        lambda request: httpx.Response(status, text="provider-private-detail")
    )
    with pytest.raises(tools.ToolError, match=f"HTTP {status}") as error:
        tools.read_email(1, transport)
    assert "provider-private-detail" not in str(error.value)
    assert "test-token" not in str(error.value)


def test_mailtrap_timeout_is_distinct_from_empty_inbox(monkeypatch):
    configure_test_mailtrap(monkeypatch)

    def handler(request):
        raise httpx.ReadTimeout("provider-private-detail", request=request)

    with pytest.raises(tools.ToolError, match="failed or timed out") as error:
        tools.read_email(1, httpx.MockTransport(handler))
    assert "provider-private-detail" not in str(error.value)


def test_mailtrap_invalid_payload_is_distinct_from_empty_inbox(monkeypatch):
    configure_test_mailtrap(monkeypatch)
    transport = httpx.MockTransport(lambda request: httpx.Response(200, json={}))
    with pytest.raises(tools.ToolError, match="invalid message response"):
        tools.read_email(1, transport)
