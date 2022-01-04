from flask import Blueprint, session, redirect
from ambimancer_server.auth import auth0
from os import getenv
from six.moves.urllib.parse import urlencode

bp = Blueprint('auth', __name__)


@bp.route('/auth/login')
def login():
    return auth0.authorize_redirect(
        redirect_uri='http://127.0.0.1:5000/auth/callback')


@bp.route('/auth/logout')
def logout():
    session.clear()
    params = {
        'returnTo': '/',
        'client_id': getenv('AUTH0_CLIENT_ID')
    }
    return redirect(auth0.api_base_url + '/v2/logout?' + urlencode(params))


@bp.route('/auth/callback')
def callback_handling():
    auth0.authorize_access_token()
    resp = auth0.get('userinfo')
    userinfo = resp.json()

    session['jwt_payload'] = userinfo
    session['profile'] = {
        'user_id': userinfo['sub'],
        'name': userinfo['name'],
        'picture': userinfo['picture']
    }

    return redirect('/')
