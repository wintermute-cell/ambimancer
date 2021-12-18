from flask import Blueprint, send_from_directory
from definitions import ROOT_DIR
import os.path

bp = Blueprint('core', __name__)


@bp.route('/')
def base():
    p = os.path.join(ROOT_DIR, 'client/public')
    return send_from_directory(p, 'index.html')


# Path for all the static files (compiled JS/CSS, etc.)
@bp.route("/<path:path>")
def home(path):
    p = os.path.join(ROOT_DIR, 'client/public')
    return send_from_directory(p, path)
