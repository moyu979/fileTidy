"""文件相关的 API 接口。"""

from flask import Blueprint

files_bp = Blueprint('files', __name__, url_prefix='/api/v1/files')


@files_bp.route('/addFiles', methods=['POST'])
def addFiles():
    """添加文件的接口。"""
    # TODO: 实现具体逻辑
    return {'message': '接口待实现'}, 200

