from flask import Blueprint

bp = Blueprint('motd', __name__)


@bp.route('/motd')
def motd():
    return "YEET FUCKER"
