from flask import Blueprint, request
from .. import room_handler

bp = Blueprint('rooms', __name__)


@bp.route('/rooms/create')
def create_room():
    license_key = request.args.get('license_key')
    license_type = request.args.get('license_type')

    # TODO: implement proper auth here (checking license key or similar)
    if license_type == 'dev' and license_key == 'dev_key':
        # license_key is given to create room as a uid.
        uuid = room_handler.create_room(license_key)
        return {
            'state': 'success',
            'uuid': uuid
        }
    # else if license_type == 'default' and license_key ==
    else:
        return {
            'state': 'bad_license',
            'uuid': ''
        }
