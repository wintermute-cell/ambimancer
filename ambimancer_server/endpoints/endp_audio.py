from flask import Blueprint
from flask.wrappers import Response
from definitions import ROOT_DIR
from ..room_handler import room_uuid_to_uid
import os.path

bp = Blueprint('audio', __name__)


@bp.route('/audio/ogg/<room>/<type>/<aud_id>')
def streamogg(room, type, aud_id):
    def generate():
        print(room_uuid_to_uid)
        uid = room_uuid_to_uid[room]
        fpath = os.path.join(ROOT_DIR, f'file/{uid}/audio/{type}/{aud_id}.ogg')
        with open(fpath, "rb") as fogg:
            data = fogg.read(1024)
            while data:
                yield data
                data = fogg.read(1024)
    return Response(generate(), mimetype="audio/ogg")
