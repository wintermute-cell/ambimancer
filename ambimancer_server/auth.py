from functools import wraps
from authlib.integrations.flask_client import OAuth
from os import getenv
from flask import session, redirect


oauth = OAuth()

domain = getenv('AUTH0_DOMAIN')

auth0 = oauth.register(
    'auth0',
    client_id=getenv('AUTH0_CLIENT_ID'),
    client_secret=getenv('AUTH0_CLIENT_SECRET'),
    api_base_url=getenv('AUTH0_DOMAIN'),
    access_token_url=f'{domain}/oauth/token',
    authorize_url=f'{domain}/authorize',
    client_kwargs={
        'scope': getenv('AUTH0_SCOPE')
    }
)


def requires_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'profile' not in session:
            return redirect('/')
        return f(*args, **kwargs)

    return decorated
