from flask import Blueprint, request
from .. import ambience_manager

bp = Blueprint('ambiences', __name__)


@bp.route('/ambience/read')
def read():
    # uid is just license key for now.
    uid = request.args.get('uid')
    ambience_name = request.args.get('ambience_name')
    ambience_json = ambience_manager.get_by_uid(
        uid).ambience_load_json(ambience_name)

    return ambience_json


@bp.route('/ambience/list')
def list():
    uid = request.args.get('uid')
    ambience_names = ambience_manager.get_by_uid(uid).ambience_load_list()
    return {
        'ambience_names': ambience_names
    }
