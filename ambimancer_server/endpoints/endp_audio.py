from flask import Blueprint, Response
from definitions import ROOT_DIR
import os.path

bp = Blueprint('audio', __name__)


@bp.route('/audio/wav')
def streamwav():
    def generate():
        fpath = os.path.join(ROOT_DIR, 'file/audio/test.wav')
        with open(fpath, "rb") as fwav:
            data = fwav.read(1024)
            while data:
                yield data
                data = fwav.read(1024)
    return Response(generate(), mimetype="audio/x-wav")


@bp.route('/audio/ogg')
def streamogg():
    def generate():
        fpath = os.path.join(ROOT_DIR, 'file/audio/test.ogg')
        with open(fpath, "rb") as fogg:
            data = fogg.read(1024)
            while data:
                yield data
                data = fogg.read(1024)
    return Response(generate(), mimetype="audio/ogg")
