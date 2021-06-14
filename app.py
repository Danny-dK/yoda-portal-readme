#!/usr/bin/env python3

__copyright__ = 'Copyright (c) 2021, Utrecht University'
__license__   = 'GPLv3, see LICENSE'

from flask import Flask, g, redirect, request, url_for
from flask_session import Session
from flask_wtf.csrf import CSRFProtect

from api import api_bp
from datarequest.datarequest import datarequest_bp
from general.general import general_bp
from group_manager.group_manager import group_manager_bp
from intake.intake import intake_bp
from research.research import research_bp
from stats.stats import stats_bp
from user.user import user_bp
from vault.vault import vault_bp

app = Flask(__name__)

# Load configurations
with app.app_context():
    app.config.from_pyfile('flask.cfg')


# Setup values for the navigation bar used in
# general/templates/general/base.html
app.config['modules'] = [
    {'name': 'Research',       'function': 'research_bp.index'},
    {'name': 'Vault',          'function': 'vault_bp.index'},
    {'name': 'Statistics',     'function': 'stats_bp.index'},
    {'name': 'Group Manager',  'function': 'group_manager_bp.index'}
]
if app.config.get('INTAKE_ENABLED'):
    app.config['modules'].append(
        {'name': 'Intake', 'function': 'intake_bp.index'}
    )
if app.config.get('DATAREQUEST_ENABLED'):
    app.config['modules'].append(
        {'name': 'Datarequest', 'function': 'datarequest_bp.index'}
    )

# Default nr of items in browser list
app.config['browser-items-per-page'] = 10
# Default nr of items in search list
app.config['search-items-per-page'] = 10

# Start Flask-Session
Session(app)


# Register blueprints
with app.app_context():
    app.register_blueprint(general_bp)
    app.register_blueprint(group_manager_bp, url_prefix='/group')
    app.register_blueprint(research_bp, url_prefix='/research')
    app.register_blueprint(stats_bp, url_prefix='/statistics')
    app.register_blueprint(user_bp, url_prefix='/user')
    app.register_blueprint(vault_bp, url_prefix='/vault')
    app.register_blueprint(api_bp, url_prefix='/api/')
    if app.config.get('INTAKE_ENABLED'):
        app.register_blueprint(intake_bp, url_prefix='/intake/')
    if app.config.get('DATAREQUEST_ENABLED'):
        app.register_blueprint(datarequest_bp, url_prefix='/datarequest/')

# XXX CSRF needs to be disabled for API testing.
csrf = CSRFProtect(app)


@app.before_request
def protect_pages():
    """Restricted pages access protection."""
    if not request.endpoint or request.endpoint in ['general_bp.index',
                                                    'user_bp.login',
                                                    'user_bp.callback',
                                                    'api_bp.call',
                                                    'static']:
        return
    elif g.get('user', None) is not None:
        return
    else:
        return redirect(url_for('user_bp.login', redirect_target=request.full_path))


@app.after_request
def content_security_policy(response):
    """Add Content-Security-Policy headers."""
    if request.endpoint in ['research_bp.form', 'vault_bp.form']:
        response.headers['Content-Security-Policy'] = "default-src 'self'; style-src 'self' 'unsafe-inline'; script-src 'self' 'unsafe-inline'; img-src 'self' data: *.openstreetmap.org; frame-ancestors 'self'; form-action 'self'"  # noqa: E501
    else:
        response.headers['Content-Security-Policy'] = "default-src 'self'; style-src 'self' 'unsafe-inline'; script-src 'self' 'unsafe-inline'; img-src 'self' data:; frame-ancestors 'self'; form-action 'self'"  # noqa: E501
    return response
