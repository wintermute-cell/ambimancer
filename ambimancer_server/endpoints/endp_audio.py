from flask import Blueprint, Response
from definitions import ROOT_DIR
import os.path

bp = Blueprint('audio', __name__)


@bp.route('/audio/ogg/<type>/<aud_id>')
def streamogg(type, aud_id):
    def generate():
        fpath = os.path.join(ROOT_DIR, f'file/audio/{type}/{aud_id}.ogg')
        with open(fpath, "rb") as fogg:
            data = fogg.read(1024)
            while data:
                yield data
                data = fogg.read(1024)
    return Response(generate(), mimetype="audio/ogg")
