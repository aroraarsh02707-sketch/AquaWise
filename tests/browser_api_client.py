"""Test client helper that models the token behavior of the React API client."""

from flask.testing import FlaskClient
from werkzeug.datastructures import Headers


class BrowserApiTestClient(FlaskClient):
    """Fetch a CSRF token before mutations, as frontend/src/services/api.js does."""

    def open(self, *args, **kwargs):
        request = args[0] if args else None
        method = kwargs.get("method") or getattr(request, "method", None)
        path = request if isinstance(request, str) else getattr(request, "path", "")
        if (method or "GET").upper() in {"POST", "PUT", "PATCH", "DELETE"} and path != "/api/auth/csrf":
            token_response = super().open("/api/auth/csrf", method="GET")
            token = token_response.get_json()["data"]["csrf_token"]
            headers = Headers(kwargs.get("headers") or {})
            headers["X-CSRF-Token"] = token
            kwargs["headers"] = headers
        return super().open(*args, **kwargs)
