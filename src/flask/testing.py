from __future__ import annotations

import importlib.metadata
import typing as t
from contextlib import contextmanager
from contextlib import ExitStack
from copy import copy
from types import TracebackType
from urllib.parse import urlsplit, urlparse

import werkzeug.test
from click.testing import CliRunner
from click.testing import Result
from werkzeug.test import Client
from werkzeug.wrappers import Request as BaseRequest

from .cli import ScriptInfo
from .sessions import SessionMixin

if t.TYPE_CHECKING:  # pragma: no cover
    from _typeshed.wsgi import WSGIEnvironment
    from werkzeug.test import TestResponse

    from .app import Flask


class EnvironBuilder(werkzeug.test.EnvironBuilder):
    """An :class:`~werkzeug.test.EnvironBuilder`, that takes defaults from the
    application.

    :param app: The Flask application to configure the environment from.
    :param path: URL path being requested.
    :param base_url: Base URL where the app is being served, which
        ``path`` is relative to. If not given, built from
        :data:`PREFERRED_URL_SCHEME`, ``subdomain``,
        :data:`SERVER_NAME`, and :data:`APPLICATION_ROOT`.
    :param subdomain: Subdomain name to append to :data:`SERVER_NAME`.
    :param url_scheme: Scheme to use instead of
        :data:`PREFERRED_URL_SCHEME`.
    :param json: If given, this is serialized as JSON and passed as
        ``data``. Also defaults ``content_type`` to
        ``application/json``.
    :param args: other positional arguments passed to
        :class:`~werkzeug.test.EnvironBuilder`.
    :param kwargs: other keyword arguments passed to
        :class:`~werkzeug.test.EnvironBuilder`.
    """

    def __init__(
        self,
        app: Flask,
        path: str = "/",
        base_url: str | None = None,
        subdomain: str | None = None,
        url_scheme: str | None = None,
        *args: t.Any,
        **kwargs: t.Any,
    ) -> None:
        assert not (base_url or subdomain or url_scheme) or (
            base_url is not None
        ) != bool(subdomain or url_scheme), (
            'Cannot pass "subdomain" or "url_scheme" with "base_url".'
        )

        if base_url is None:
            http_host = app.config.get("SERVER_NAME") or "localhost"
            app_root = app.config["APPLICATION_ROOT"]

            if subdomain:
                http_host = f"{subdomain}.{http_host}"

            if url_scheme is None:
                url_scheme = app.config["PREFERRED_URL_SCHEME"]

            parsed_url = urlparse(path)
            base_url = (
                f"{parsed_url.scheme or url_scheme}://{parsed_url.netloc or http_host}"
                f"/{app_root.lstrip("/")}"
            )
            path = parsed_url.path

            if parsed_url.query:
                path = f"{path}?{parsed_url.query}"

        super().__init__(base_url=base_url, path=path, *args, **kwargs)


class FlaskClient(Client):
    """A :class:`~werkzeug.test.Client` for testing a Flask app.

    Typically created using :meth:`~flask.Flask.test_client`. See
    :ref:`testing-clients`.
    """

    def open(self, *args, **kwargs):
        if isinstance(args[0], werkzeug.wrappers.Request):
            request = args[0]
        else:
            request = super().open(*args, **kwargs)

        # Re-push contexts that were preserved during the request.
        for cm in self._new_contexts:
            self._context_stack.enter_context(cm)

        self._new_contexts.clear()
        return request

    def __enter__(self) -> FlaskClient:
        if self.preserve_context:
            raise RuntimeError("Cannot nest client invocations")
        self.preserve_context = True
        return self

    def __exit__(
        self,
        exc_type: type | None,
        exc_value: BaseException | None,
        tb: TracebackType | None,
    ) -> None:
        self.preserve_context = False
        self._context_stack.close()


class FlaskCliRunner(CliRunner):
    """A :class:`~click.testing.CliRunner` for testing a Flask app's
    CLI commands. Typically created using
    :meth:`~flask.Flask.test_cli_runner`. See :ref:`testing-cli`.
    """

    def __init__(self, app: Flask, **kwargs: t.Any) -> None:
        self.app = app
        super().__init__(**kwargs)

    def invoke(  # type: ignore
        self, cli: t.Any = None, args: t.Any = None, **kwargs: t.Any
    ) -> Result:
        """Invokes a CLI command in an isolated environment. See
        :meth:`CliRunner.invoke <click.testing.CliRunner.invoke>` for
        full method documentation. See :ref:`testing-cli` for examples.

        If the ``obj`` argument is not given, passes an instance of
        :class:`~flask.cli.ScriptInfo` that knows how to load the Flask
        app being tested.

        :param cli: Command object to invoke. Default is the app's
            :attr:`~flask.app.Flask.cli` group.
        :param args: List of strings to invoke the command with.

        :return: a :class:`~click.testing.Result` object.
        """
        if cli is None:
            cli = self.app.cli

        if "obj" not in kwargs:
            kwargs["obj"] = ScriptInfo(create_app=lambda: self.app)

        return super().invoke(cli, args, **kwargs)
