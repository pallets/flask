"""Tests for CSRF protection using Sec-Fetch-Site header."""

from flask.views import MethodView


class TestCSRFProtection:
    """Test CSRF protection functionality."""

    def test_csrf_disabled_by_default(self, app, client):
        """CSRF protection is disabled by default."""

        @app.route("/", methods=["POST"])
        def index():
            return "ok"

        # Cross-origin request should succeed when CSRF is disabled
        rv = client.post(
            "/",
            headers={
                "Origin": "https://evil.com",
                "Sec-Fetch-Site": "cross-site",
            },
        )
        assert rv.status_code == 200

    def test_csrf_enabled_via_config(self, app, client):
        """CSRF protection can be enabled via CSRF_PROTECTION config."""
        app.config["CSRF_PROTECTION"] = True

        @app.route("/", methods=["POST"])
        def index():
            return "ok"

        # Cross-origin request should be rejected
        rv = client.post(
            "/",
            headers={
                "Origin": "https://evil.com",
                "Sec-Fetch-Site": "cross-site",
            },
        )
        assert rv.status_code == 403

    def test_csrf_enabled_via_route_param(self, app, client):
        """CSRF protection can be enabled per-route."""

        @app.route("/", methods=["POST"], csrf_protection=True)
        def index():
            return "ok"

        # Cross-origin request should be rejected
        rv = client.post(
            "/",
            headers={
                "Origin": "https://evil.com",
                "Sec-Fetch-Site": "cross-site",
            },
        )
        assert rv.status_code == 403

    def test_csrf_disabled_via_route_param_overrides_config(self, app, client):
        """Route-level csrf_protection=False overrides CSRF_PROTECTION config."""
        app.config["CSRF_PROTECTION"] = True

        @app.route("/", methods=["POST"], csrf_protection=False)
        def index():
            return "ok"

        # Cross-origin request should succeed
        rv = client.post(
            "/",
            headers={
                "Origin": "https://evil.com",
                "Sec-Fetch-Site": "cross-site",
            },
        )
        assert rv.status_code == 200

    def test_csrf_allows_same_origin(self, app, client):
        """Same-origin requests are allowed."""

        @app.route("/", methods=["POST"], csrf_protection=True)
        def index():
            return "ok"

        rv = client.post("/", headers={"Sec-Fetch-Site": "same-origin"})
        assert rv.status_code == 200

    def test_csrf_allows_none_fetch_site(self, app, client):
        """Requests with Sec-Fetch-Site: none are allowed (direct navigation)."""

        @app.route("/", methods=["POST"], csrf_protection=True)
        def index():
            return "ok"

        rv = client.post("/", headers={"Sec-Fetch-Site": "none"})
        assert rv.status_code == 200

    def test_csrf_rejects_same_site(self, app, client):
        """Same-site cross-origin requests are rejected."""

        @app.route("/", methods=["POST"], csrf_protection=True)
        def index():
            return "ok"

        rv = client.post("/", headers={"Sec-Fetch-Site": "same-site"})
        assert rv.status_code == 403

    def test_csrf_rejects_cross_site(self, app, client):
        """Cross-site requests are rejected."""

        @app.route("/", methods=["POST"], csrf_protection=True)
        def index():
            return "ok"

        rv = client.post("/", headers={"Sec-Fetch-Site": "cross-site"})
        assert rv.status_code == 403

    def test_csrf_allows_get_requests(self, app, client):
        """GET requests are not protected by CSRF (safe method)."""

        @app.route("/", methods=["GET"], csrf_protection=True)
        def index():
            return "ok"

        rv = client.get("/", headers={"Sec-Fetch-Site": "cross-site"})
        assert rv.status_code == 200

    def test_csrf_allows_head_requests(self, app, client):
        """HEAD requests are not protected by CSRF (safe method)."""

        @app.route("/", methods=["GET", "HEAD"], csrf_protection=True)
        def index():
            return "ok"

        rv = client.head("/", headers={"Sec-Fetch-Site": "cross-site"})
        assert rv.status_code == 200

    def test_csrf_allows_options_requests(self, app, client):
        """OPTIONS requests are not protected by CSRF (safe method)."""

        @app.route("/", methods=["POST", "OPTIONS"], csrf_protection=True)
        def index():
            return "ok"

        rv = client.options("/", headers={"Sec-Fetch-Site": "cross-site"})
        assert rv.status_code == 200

    def test_csrf_protects_post(self, app, client):
        """POST requests are protected."""

        @app.route("/", methods=["POST"], csrf_protection=True)
        def index():
            return "ok"

        rv = client.post("/", headers={"Sec-Fetch-Site": "cross-site"})
        assert rv.status_code == 403

    def test_csrf_protects_put(self, app, client):
        """PUT requests are protected."""

        @app.route("/", methods=["PUT"], csrf_protection=True)
        def index():
            return "ok"

        rv = client.put("/", headers={"Sec-Fetch-Site": "cross-site"})
        assert rv.status_code == 403

    def test_csrf_protects_patch(self, app, client):
        """PATCH requests are protected."""

        @app.route("/", methods=["PATCH"], csrf_protection=True)
        def index():
            return "ok"

        rv = client.patch("/", headers={"Sec-Fetch-Site": "cross-site"})
        assert rv.status_code == 403

    def test_csrf_protects_delete(self, app, client):
        """DELETE requests are protected."""

        @app.route("/", methods=["DELETE"], csrf_protection=True)
        def index():
            return "ok"

        rv = client.delete("/", headers={"Sec-Fetch-Site": "cross-site"})
        assert rv.status_code == 403


class TestCSRFTrustedOrigins:
    """Test CSRF_TRUSTED_ORIGINS configuration."""

    def test_trusted_origin_allowed(self, app, client):
        """Requests from trusted origins are allowed."""
        app.config["CSRF_TRUSTED_ORIGINS"] = ["https://trusted.com"]

        @app.route("/", methods=["POST"], csrf_protection=True)
        def index():
            return "ok"

        rv = client.post(
            "/",
            headers={
                "Origin": "https://trusted.com",
                "Sec-Fetch-Site": "cross-site",
            },
        )
        assert rv.status_code == 200

    def test_untrusted_origin_rejected(self, app, client):
        """Requests from untrusted origins are rejected."""
        app.config["CSRF_TRUSTED_ORIGINS"] = ["https://trusted.com"]

        @app.route("/", methods=["POST"], csrf_protection=True)
        def index():
            return "ok"

        rv = client.post(
            "/",
            headers={
                "Origin": "https://evil.com",
                "Sec-Fetch-Site": "cross-site",
            },
        )
        assert rv.status_code == 403


class TestCSRFOriginFallback:
    """Test Origin header fallback for browsers without Sec-Fetch-Site."""

    def test_no_headers_allowed(self, app, client):
        """Requests without Sec-Fetch-Site or Origin are allowed (non-browser)."""

        @app.route("/", methods=["POST"], csrf_protection=True)
        def index():
            return "ok"

        rv = client.post("/")
        assert rv.status_code == 200

    def test_matching_origin_allowed(self, app, client):
        """Requests with matching Origin header are allowed."""

        @app.route("/", methods=["POST"], csrf_protection=True)
        def index():
            return "ok"

        rv = client.post("/", headers={"Origin": "http://localhost"})
        assert rv.status_code == 200

    def test_mismatched_origin_rejected(self, app, client):
        """Requests with mismatched Origin header are rejected."""

        @app.route("/", methods=["POST"], csrf_protection=True)
        def index():
            return "ok"

        rv = client.post("/", headers={"Origin": "https://evil.com"})
        assert rv.status_code == 403


class TestCSRFViewFunctionAttribute:
    """Test csrf_protection attribute on view functions."""

    def test_view_func_attribute_enables_csrf(self, app, client):
        """View function csrf_protection attribute enables CSRF protection."""

        def index():
            return "ok"

        index.csrf_protection = True
        app.add_url_rule("/", view_func=index, methods=["POST"])

        rv = client.post("/", headers={"Sec-Fetch-Site": "cross-site"})
        assert rv.status_code == 403

    def test_view_func_attribute_disables_csrf(self, app, client):
        """View function csrf_protection attribute disables CSRF protection."""
        app.config["CSRF_PROTECTION"] = True

        def index():
            return "ok"

        index.csrf_protection = False
        app.add_url_rule("/", view_func=index, methods=["POST"])

        rv = client.post("/", headers={"Sec-Fetch-Site": "cross-site"})
        assert rv.status_code == 200


class TestCSRFClassBasedViews:
    """Test CSRF protection with class-based views."""

    def test_method_view_csrf_protection(self, app, client):
        """MethodView with csrf_protection class attribute."""

        class MyView(MethodView):
            csrf_protection = True

            def post(self):
                return "ok"

        app.add_url_rule("/", view_func=MyView.as_view("myview"))

        rv = client.post("/", headers={"Sec-Fetch-Site": "cross-site"})
        assert rv.status_code == 403

        rv = client.post("/", headers={"Sec-Fetch-Site": "same-origin"})
        assert rv.status_code == 200

    def test_method_view_csrf_disabled(self, app, client):
        """MethodView with csrf_protection=False overrides config."""
        app.config["CSRF_PROTECTION"] = True

        class MyView(MethodView):
            csrf_protection = False

            def post(self):
                return "ok"

        app.add_url_rule("/", view_func=MyView.as_view("myview"))

        rv = client.post("/", headers={"Sec-Fetch-Site": "cross-site"})
        assert rv.status_code == 200


class TestCSRFProtectedMethods:
    """Test CSRF_PROTECTED_METHODS configuration."""

    def test_custom_protected_methods(self, app, client):
        """Custom CSRF_PROTECTED_METHODS configuration."""
        app.config["CSRF_PROTECTED_METHODS"] = frozenset({"POST"})

        @app.route("/", methods=["POST", "DELETE"], csrf_protection=True)
        def index():
            return "ok"

        # POST should still be protected
        rv = client.post("/", headers={"Sec-Fetch-Site": "cross-site"})
        assert rv.status_code == 403

        # DELETE should not be protected (not in CSRF_PROTECTED_METHODS)
        rv = client.delete("/", headers={"Sec-Fetch-Site": "cross-site"})
        assert rv.status_code == 200
