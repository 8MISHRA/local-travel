"""Property-based tests for API response format consistency and error handling.

**Validates: Requirements 21.1, 21.2, 21.4**

Property 26: API response format consistency
- All successful responses follow {"success": true, "data": ..., "message": ...} format.
- All error responses follow {"success": false, "error": {"code": ..., "message": ..., "details": ...}} format.

Property 31: Unhandled exceptions return generic 500
- When unhandled exceptions occur, the API returns HTTP 500 with a generic error message
  not exposing internals.
"""

import json

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from app import create_app
from app.utils.response import success_response, error_response


# --- Strategies ---

# Strategy for arbitrary JSON-serializable data payloads
json_primitives = st.one_of(
    st.none(),
    st.booleans(),
    st.integers(min_value=-1_000_000, max_value=1_000_000),
    st.floats(allow_nan=False, allow_infinity=False),
    st.text(min_size=0, max_size=200),
)

json_values = st.recursive(
    json_primitives,
    lambda children: st.one_of(
        st.lists(children, max_size=5),
        st.dictionaries(st.text(min_size=1, max_size=20), children, max_size=5),
    ),
    max_leaves=10,
)

# Strategy for non-empty message strings
message_strategy = st.text(min_size=1, max_size=200)

# Strategy for error codes (uppercase with underscores)
error_code_strategy = st.from_regex(r"[A-Z][A-Z0-9_]{1,30}", fullmatch=True)

# Strategy for valid success HTTP status codes
success_status_codes = st.sampled_from([200, 201])

# Strategy for valid error HTTP status codes
error_status_codes = st.sampled_from([400, 401, 403, 404, 409, 422, 429, 500])

# Strategy for error details (None or a dict)
error_details_strategy = st.one_of(
    st.none(),
    st.dictionaries(st.text(min_size=1, max_size=20), json_primitives, max_size=5),
)


# --- Fixtures ---

@pytest.fixture
def app():
    """Create a Flask application configured for testing."""
    app = create_app("testing")
    return app


@pytest.fixture
def client(app):
    """Create a test client for the Flask application."""
    return app.test_client()


# --- Property 26: API response format consistency ---

class TestSuccessResponseFormat:
    """Property 26 (success): success_response always produces the correct format.

    **Validates: Requirements 21.1**
    """

    @given(
        data=json_values,
        message=message_strategy,
        status_code=success_status_codes,
    )
    @settings(max_examples=100)
    def test_success_response_has_required_keys(self, data, message, status_code):
        """All successful responses contain 'success', 'data', and 'message' keys."""
        app = create_app("testing")
        with app.app_context():
            response, code = success_response(data, message=message, status_code=status_code)
            body = json.loads(response.get_data(as_text=True))

            assert "success" in body
            assert "data" in body
            assert "message" in body

    @given(
        data=json_values,
        message=message_strategy,
        status_code=success_status_codes,
    )
    @settings(max_examples=100)
    def test_success_response_success_field_is_true(self, data, message, status_code):
        """The 'success' field is always True for success responses."""
        app = create_app("testing")
        with app.app_context():
            response, code = success_response(data, message=message, status_code=status_code)
            body = json.loads(response.get_data(as_text=True))

            assert body["success"] is True

    @given(
        data=json_values,
        message=message_strategy,
        status_code=success_status_codes,
    )
    @settings(max_examples=100)
    def test_success_response_returns_correct_status_code(self, data, message, status_code):
        """The returned HTTP status code matches the requested status code."""
        app = create_app("testing")
        with app.app_context():
            response, code = success_response(data, message=message, status_code=status_code)

            assert code == status_code

    @given(
        data=json_values,
        message=message_strategy,
    )
    @settings(max_examples=100)
    def test_success_response_message_matches_input(self, data, message):
        """The 'message' field matches the provided message."""
        app = create_app("testing")
        with app.app_context():
            response, code = success_response(data, message=message)
            body = json.loads(response.get_data(as_text=True))

            assert body["message"] == message

    @given(data=json_values)
    @settings(max_examples=100)
    def test_success_response_no_extra_top_level_keys(self, data):
        """Success responses contain exactly 'success', 'data', and 'message' keys."""
        app = create_app("testing")
        with app.app_context():
            response, code = success_response(data)
            body = json.loads(response.get_data(as_text=True))

            assert set(body.keys()) == {"success", "data", "message"}


class TestErrorResponseFormat:
    """Property 26 (error): error_response always produces the correct format.

    **Validates: Requirements 21.2**
    """

    @given(
        code=error_code_strategy,
        message=message_strategy,
        details=error_details_strategy,
        status_code=error_status_codes,
    )
    @settings(max_examples=100)
    def test_error_response_has_required_keys(self, code, message, details, status_code):
        """All error responses contain 'success' and 'error' top-level keys."""
        app = create_app("testing")
        with app.app_context():
            response, resp_code = error_response(code, message, details=details, status_code=status_code)
            body = json.loads(response.get_data(as_text=True))

            assert "success" in body
            assert "error" in body

    @given(
        code=error_code_strategy,
        message=message_strategy,
        details=error_details_strategy,
        status_code=error_status_codes,
    )
    @settings(max_examples=100)
    def test_error_response_success_field_is_false(self, code, message, details, status_code):
        """The 'success' field is always False for error responses."""
        app = create_app("testing")
        with app.app_context():
            response, resp_code = error_response(code, message, details=details, status_code=status_code)
            body = json.loads(response.get_data(as_text=True))

            assert body["success"] is False

    @given(
        code=error_code_strategy,
        message=message_strategy,
        details=error_details_strategy,
        status_code=error_status_codes,
    )
    @settings(max_examples=100)
    def test_error_response_error_object_has_required_fields(self, code, message, details, status_code):
        """The 'error' object contains 'code', 'message', and 'details' fields."""
        app = create_app("testing")
        with app.app_context():
            response, resp_code = error_response(code, message, details=details, status_code=status_code)
            body = json.loads(response.get_data(as_text=True))

            error_obj = body["error"]
            assert "code" in error_obj
            assert "message" in error_obj
            assert "details" in error_obj

    @given(
        code=error_code_strategy,
        message=message_strategy,
        details=error_details_strategy,
        status_code=error_status_codes,
    )
    @settings(max_examples=100)
    def test_error_response_returns_correct_status_code(self, code, message, details, status_code):
        """The returned HTTP status code matches the requested status code."""
        app = create_app("testing")
        with app.app_context():
            response, resp_code = error_response(code, message, details=details, status_code=status_code)

            assert resp_code == status_code

    @given(
        code=error_code_strategy,
        message=message_strategy,
        details=error_details_strategy,
    )
    @settings(max_examples=100)
    def test_error_response_code_and_message_match_input(self, code, message, details):
        """The error code and message match the provided inputs."""
        app = create_app("testing")
        with app.app_context():
            response, resp_code = error_response(code, message, details=details)
            body = json.loads(response.get_data(as_text=True))

            assert body["error"]["code"] == code
            assert body["error"]["message"] == message
            assert body["error"]["details"] == details

    @given(
        code=error_code_strategy,
        message=message_strategy,
        details=error_details_strategy,
        status_code=error_status_codes,
    )
    @settings(max_examples=100)
    def test_error_response_no_extra_top_level_keys(self, code, message, details, status_code):
        """Error responses contain exactly 'success' and 'error' top-level keys."""
        app = create_app("testing")
        with app.app_context():
            response, resp_code = error_response(code, message, details=details, status_code=status_code)
            body = json.loads(response.get_data(as_text=True))

            assert set(body.keys()) == {"success", "error"}

    @given(
        code=error_code_strategy,
        message=message_strategy,
        details=error_details_strategy,
        status_code=error_status_codes,
    )
    @settings(max_examples=100)
    def test_error_response_error_object_no_extra_keys(self, code, message, details, status_code):
        """The error object contains exactly 'code', 'message', and 'details' keys."""
        app = create_app("testing")
        with app.app_context():
            response, resp_code = error_response(code, message, details=details, status_code=status_code)
            body = json.loads(response.get_data(as_text=True))

            assert set(body["error"].keys()) == {"code", "message", "details"}


# --- Property 31: Unhandled exceptions return generic 500 ---

class TestUnhandledExceptionHandling:
    """Property 31: Unhandled exceptions are caught by error handlers and return generic 500.

    **Validates: Requirements 21.4**
    """

    @given(
        exception_message=st.text(min_size=1, max_size=200),
    )
    @settings(max_examples=100)
    def test_unhandled_exception_returns_500(self, exception_message):
        """Unhandled exceptions return HTTP 500 status code."""
        app = create_app("testing")

        # Register a route that raises an unhandled exception
        @app.route("/test-crash")
        def crash_route():
            raise RuntimeError(exception_message)

        with app.test_client() as client:
            response = client.get("/test-crash")

            assert response.status_code == 500

    @given(
        exception_message=st.text(min_size=1, max_size=200),
    )
    @settings(max_examples=100)
    def test_unhandled_exception_returns_error_format(self, exception_message):
        """Unhandled exceptions return the standard error response format."""
        app = create_app("testing")

        @app.route("/test-crash")
        def crash_route():
            raise RuntimeError(exception_message)

        with app.test_client() as client:
            response = client.get("/test-crash")
            body = response.get_json()

            assert body["success"] is False
            assert "error" in body
            assert "code" in body["error"]
            assert "message" in body["error"]
            assert "details" in body["error"]

    @given(
        exception_message=st.text(
            alphabet=st.characters(whitelist_categories=("L", "N"), whitelist_characters="_-!@#$%^&*"),
            min_size=10,
            max_size=200,
        ),
    )
    @settings(max_examples=100)
    def test_unhandled_exception_does_not_expose_internals(self, exception_message):
        """Unhandled exceptions do not expose internal error details in the response."""
        app = create_app("testing")

        @app.route("/test-crash")
        def crash_route():
            raise RuntimeError(exception_message)

        with app.test_client() as client:
            response = client.get("/test-crash")
            body = response.get_json()

            # The error code should be generic
            assert body["error"]["code"] == "INTERNAL_ERROR"
            # The message should be generic, not the exception message
            assert body["error"]["message"] == "An unexpected error occurred."
            # No details should be exposed
            assert body["error"]["details"] is None
            # The actual exception message must not appear in the response body
            response_text = json.dumps(body)
            assert exception_message not in response_text

    @given(
        exception_type=st.sampled_from([
            RuntimeError, ValueError, TypeError, KeyError,
            AttributeError, ZeroDivisionError, IOError,
        ]),
    )
    @settings(max_examples=100)
    def test_various_exception_types_return_generic_500(self, exception_type):
        """Various unhandled exception types all return the same generic 500 response."""
        app = create_app("testing")

        @app.route("/test-crash")
        def crash_route():
            raise exception_type("some internal error details")

        with app.test_client() as client:
            response = client.get("/test-crash")

            assert response.status_code == 500
            body = response.get_json()
            assert body["success"] is False
            assert body["error"]["code"] == "INTERNAL_ERROR"
            assert body["error"]["message"] == "An unexpected error occurred."
            assert "some internal error details" not in json.dumps(body)
