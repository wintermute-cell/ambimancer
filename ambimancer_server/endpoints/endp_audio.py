from flask import Blueprint, request
from flask.wrappers import Response
from definitions import ROOT_DIR, AUDIO_UPLOAD_EXTENSIONS
from ..room_handler import room_uuid_to_uid
import os
from werkzeug.utils import secure_filename
import subprocess

bp = Blueprint('audio', __name__)


@bp.route('/audio/ogg/<room>/<type>/<aud_id>')
def streamogg(room, type, aud_id):
    def generate():
        uid = room_uuid_to_uid[room]
        fpath = os.path.join(ROOT_DIR, f'file/{uid}/audio/{type}/{aud_id}.ogg')
        with open(fpath, "rb") as fogg:
            data = fogg.read(1024)
            while data:
                yield data
                data = fogg.read(1024)
    return Response(generate(), mimetype="audio/ogg")


# use like: /audio/getfilenames?type=<music|sfx>&room=<room_uuid>
@bp.route('/audio/getfilenames')
def get_filenames():
    type = request.args.get('type')
    room = request.args.get('room')

    uid = room_uuid_to_uid[room]

    fpath = os.path.join(ROOT_DIR, f'file/{uid}/audio/{type}')
    ls = os.listdir(fpath)
    names = [f.split('.')[0] for f in ls]

    return {
        'names': names
    }


@bp.route('/audio/upload', methods=['POST'])
def upload_audio():

    room_uuid = request.form.get('room_uuid')
    audio_type = request.form.get('type')

    if room_uuid is None or audio_type is None:
        return {
            'success': False,
            'msg': 'no_form'
        }

    uid = room_uuid_to_uid[room_uuid]

    uploaded_files = request.files.getlist('file')
    for uploaded_file in uploaded_files:
        if uploaded_file.filename is None:
            return {
                'success': False,
                'msg': 'no_filename'
            }
        fname = secure_filename(uploaded_file.filename)
        if fname != '':
            if len(fname.split('.')) > 2:
                return {
                    'success': False,
                    'msg': 'dot_in_filename'
                }
            file_name, file_ext = os.path.splitext(fname)
            print(fname)
            if file_ext not in AUDIO_UPLOAD_EXTENSIONS:
                return {
                    'success': False,
                    'msg': 'invalid_filetype'
                }
            else:
                fpath = os.path.join(
                    ROOT_DIR,
                    f'file/{uid}/audio/{audio_type}/{file_name}.{file_ext}')
                uploaded_file.save(fpath)
                if file_ext != '.ogg':
                    subprocess.run(
                        ['ffmpeg', '-i', fpath, fpath.split('.')[0]+'.ogg'])
                    os.remove(fpath)
                return {
                    'success': True,
                    'msg': 'successful_upload'
                }
