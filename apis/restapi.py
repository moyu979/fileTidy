"""
REST API 服务器，提供文件管理相关的 API 接口
"""

import logging
from flask import Flask, request, jsonify
from .addFile import addFile
from .moveFile import move_file
from .regFile import regFiles

logger = logging.getLogger(__name__)

app = Flask(__name__)


@app.route('/api/addFile', methods=['POST'])
def api_add_file():
    """
    将文件添加到指定的卷中
    
    Request Body (JSON):
        {
            "path": "文件路径",
            "volume_id": "卷ID"
        }
    
    Returns:
        {
            "success": true/false,
            "message": "消息"
        }
    """
    try:
        data = request.get_json()
        if not data:
            return jsonify({"success": False, "message": "请求体不能为空"}), 400
        
        path = data.get("path")
        volume_id = data.get("volume_id")
        
        if not path:
            return jsonify({"success": False, "message": "path 参数不能为空"}), 400
        if volume_id is None:
            return jsonify({"success": False, "message": "volume_id 参数不能为空"}), 400
        
        addFile(path, volume_id)
        return jsonify({"success": True, "message": "文件添加成功"}), 200
    except Exception as e:
        logger.error(f"添加文件失败: {str(e)}")
        return jsonify({"success": False, "message": f"添加文件失败: {str(e)}"}), 500


@app.route('/api/moveFile', methods=['POST'])
def api_move_file():
    """
    移动文件到新路径
    
    Request Body (JSON):
        {
            "path": "原文件路径",
            "new_path": "新文件路径"
        }
    
    Returns:
        {
            "success": true/false,
            "message": "消息"
        }
    """
    try:
        data = request.get_json()
        if not data:
            return jsonify({"success": False, "message": "请求体不能为空"}), 400
        
        path = data.get("path")
        new_path = data.get("new_path")
        
        if not path:
            return jsonify({"success": False, "message": "path 参数不能为空"}), 400
        if not new_path:
            return jsonify({"success": False, "message": "new_path 参数不能为空"}), 400
        
        move_file(path, new_path)
        return jsonify({"success": True, "message": "文件移动成功"}), 200
    except Exception as e:
        logger.error(f"移动文件失败: {str(e)}")
        return jsonify({"success": False, "message": f"移动文件失败: {str(e)}"}), 500


@app.route('/api/regFile', methods=['POST'])
def api_reg_file():
    """
    注册文件到数据库
    
    Request Body (JSON):
        {
            "path": "文件路径或目录路径"
        }
    
    Returns:
        {
            "success": true/false,
            "message": "消息"
        }
    """
    try:
        data = request.get_json()
        if not data:
            return jsonify({"success": False, "message": "请求体不能为空"}), 400
        
        path = data.get("path")
        
        if not path:
            return jsonify({"success": False, "message": "path 参数不能为空"}), 400
        
        regFiles(path)
        return jsonify({"success": True, "message": "文件注册成功"}), 200
    except Exception as e:
        logger.error(f"注册文件失败: {str(e)}")
        return jsonify({"success": False, "message": f"注册文件失败: {str(e)}"}), 500


@app.route('/api/health', methods=['GET'])
def api_health():
    """
    健康检查接口
    
    Returns:
        {
            "status": "ok"
        }
    """
    return jsonify({"status": "ok"}), 200


def start_rest_api(host='127.0.0.1', port=5000, debug=False):
    """
    启动 REST API 服务器
    
    Args:
        host: 服务器主机地址，默认为 127.0.0.1
        port: 服务器端口，默认为 5000
        debug: 是否开启调试模式，默认为 False
    """
    logger.info(f"启动 REST API 服务器，地址: {host}:{port}")
    app.run(host=host, port=port, debug=debug, threaded=True)

