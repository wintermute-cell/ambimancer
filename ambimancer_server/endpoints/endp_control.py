from flask import Blueprint
from ambience_manager import ambi_manager as ambi

bp = Blueprint('control', __name__)


@bp.route('/control/play/<ambience_name>')
def play_ambience(ambience_name):
    ambi.ambience_play(ambience_name)
    return {
        'success': True
    }


@bp.route('/control/stop/<ambience_name>')
def stop_ambience(ambience_name):
    ambi.ambience_stop(ambience_name)
    return {
        'success': True
    }
