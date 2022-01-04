from flask import Blueprint
#from ambience_manager import ambi_manager
#from ambimancer_server.auth import auth0, requires_auth

bp = Blueprint('control', __name__)


@bp.route('/control/play/<ambience_name>')
def play_ambience(ambience_name):
#    ambi_manager.ambience_play(ambience_name)
    return {
        'success': True
    }


@bp.route('/control/stop/<ambience_name>')
def stop_ambience(ambience_name):
#    ambi_manager.ambience_stop(ambience_name)
    return {
        'success': True
    }
