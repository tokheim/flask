# -*- coding: utf-8 -*-
"""
    tests.appctx
    ~~~~~~~~~~~~~~~~~~~~~~

    Tests the application context.

    :copyright: (c) 2014 by Armin Ronacher.
    :license: BSD, see LICENSE for more details.
"""

import pytest

import flask
import unittest



def test_basic_url_generation():
    app = flask.Flask(__name__)
    app.config['SERVER_NAME'] = 'localhost'
    app.config['PREFERRED_URL_SCHEME'] = 'https'

    @app.route('/')
    def index():
        pass

    with app.app_context():
        rv = flask.url_for('index')
        assert rv == 'https://localhost/'

def test_url_generation_requires_server_name():
    app = flask.Flask(__name__)
    with app.app_context():
        with pytest.raises(RuntimeError):
            flask.url_for('index')

def test_url_generation_without_context_fails():
    with pytest.raises(RuntimeError):
        flask.url_for('index')

def test_request_context_means_app_context():
    app = flask.Flask(__name__)
    with app.test_request_context():
        assert flask.current_app._get_current_object() == app
    assert flask._app_ctx_stack.top == None

def test_app_context_provides_current_app():
    app = flask.Flask(__name__)
    with app.app_context():
        assert flask.current_app._get_current_object() == app
    assert flask._app_ctx_stack.top == None

def test_app_tearing_down():
    cleanup_stuff = []
    app = flask.Flask(__name__)
    @app.teardown_appcontext
    def cleanup(exception):
        cleanup_stuff.append(exception)

    with app.app_context():
        pass

    assert cleanup_stuff == [None]

def test_app_tearing_down_with_previous_exception():
    cleanup_stuff = []
    app = flask.Flask(__name__)
    @app.teardown_appcontext
    def cleanup(exception):
        cleanup_stuff.append(exception)

    try:
        raise Exception('dummy')
    except Exception:
        pass

    with app.app_context():
        pass

    assert cleanup_stuff == [None]

def test_custom_app_ctx_globals_class():
    class CustomRequestGlobals(object):
        def __init__(self):
            self.spam = 'eggs'
    app = flask.Flask(__name__)
    app.app_ctx_globals_class = CustomRequestGlobals
    with app.app_context():
        assert flask.render_template_string('{{ g.spam }}') == 'eggs'

def test_context_refcounts():
    called = []
    app = flask.Flask(__name__)
    @app.teardown_request
    def teardown_req(error=None):
        called.append('request')
    @app.teardown_appcontext
    def teardown_app(error=None):
        called.append('app')
    @app.route('/')
    def index():
        with flask._app_ctx_stack.top:
            with flask._request_ctx_stack.top:
                pass
        env = flask._request_ctx_stack.top.request.environ
        assert env['werkzeug.request'] is not None
        return u''
    c = app.test_client()
    res = c.get('/')
    assert res.status_code == 200
    assert res.data == b''
    assert called == ['request', 'app']
