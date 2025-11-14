"""
卷相关的 API 接口，转发到 VolumeManager
"""

import logging
from flask import request, jsonify
from component.volume.volumeManager import volume_manager
from .restapi import app

logger = logging.getLogger(__name__)


@app.route('/api/volume/reg', methods=['POST'])
def reg_volume(volume_path=None, volume_id=None):
    """
    登记一个新卷到数据库
    
    Args:
        volume_path: 卷路径（必须是挂载点）（如果为 None，则从请求中获取）
        volume_id: 可选的卷ID（如果为 None，则从请求中获取）
    
    Returns:
        如果从 HTTP 请求调用，返回 JSON 响应；否则返回 Volume 实例或 None
    """
    # 如果是从 HTTP 请求调用，从 request 获取参数
    if volume_path is None:
        try:
            data = request.get_json()
            if not data:
                return jsonify({"success": False, "message": "请求体不能为空"}), 400
            
            volume_path = data.get("volume_path")
            volume_id = data.get("volume_id")
            
            if not volume_path:
                return jsonify({"success": False, "message": "volume_path 参数不能为空"}), 400
            
            volume = volume_manager.regVolume(volume_path, volume_id)
            if volume is None:
                return jsonify({"success": False, "message": "卷注册失败"}), 500
            
            return jsonify({
                "success": True, 
                "message": "卷注册成功",
                "volume_id": volume.orm_model.id,
                "volume_path": volume_path
            }), 200
        except Exception as e:
            logger.error(f"注册卷失败: {str(e)}")
            return jsonify({"success": False, "message": f"注册卷失败: {str(e)}"}), 500
    
    # 直接调用
    return volume_manager.regVolume(volume_path, volume_id)


@app.route('/api/volume/exists', methods=['POST'])
def volume_exists(volume_path=None, name=None):
    """
    检查给定的卷是否存在
    
    Args:
        volume_path: 卷路径（如果为 None，则从请求中获取）
        name: 卷名称（如果为 None，则从请求中获取）
    
    Returns:
        如果从 HTTP 请求调用，返回 JSON 响应；否则返回 bool
    """
    # 如果是从 HTTP 请求调用，从 request 获取参数
    if volume_path is None and name is None:
        try:
            data = request.get_json()
            if not data:
                return jsonify({"success": False, "message": "请求体不能为空"}), 400
            
            volume_path = data.get("volume_path")
            name = data.get("name")
            
            if not volume_path and not name:
                return jsonify({"success": False, "message": "volume_path 或 name 参数必须至少提供一个"}), 400
            
            if volume_path and name:
                return jsonify({"success": False, "message": "不能同时提供 volume_path 和 name"}), 400
            
            exists = volume_manager.exists_in_database(volume_path=volume_path, name=name)
            return jsonify({"success": True, "exists": exists, "message": "查询成功"}), 200
        except ValueError as e:
            return jsonify({"success": False, "message": str(e)}), 400
        except Exception as e:
            logger.error(f"查询卷失败: {str(e)}")
            return jsonify({"success": False, "message": f"查询卷失败: {str(e)}"}), 500
    
    # 直接调用
    return volume_manager.exists_in_database(volume_path=volume_path, name=name)


@app.route('/api/volume/path', methods=['POST'])
def get_path(device_path=None):
    """
    获取设备路径，如果卷存在但没挂载，返回None
    
    Args:
        device_path: 设备路径（如果为 None，则从请求中获取）
    
    Returns:
        如果从 HTTP 请求调用，返回 JSON 响应；否则返回路径或 None
    """
    # 如果是从 HTTP 请求调用，从 request 获取参数
    if device_path is None:
        try:
            data = request.get_json()
            if not data:
                return jsonify({"success": False, "message": "请求体不能为空"}), 400
            
            device_path = data.get("device_path")
            if not device_path:
                return jsonify({"success": False, "message": "device_path 参数不能为空"}), 400
            
            path = volume_manager.get_path(device_path)
            return jsonify({"success": True, "path": path, "message": "查询成功"}), 200
        except Exception as e:
            logger.error(f"获取路径失败: {str(e)}")
            return jsonify({"success": False, "message": f"获取路径失败: {str(e)}"}), 500
    
    # 直接调用
    return volume_manager.get_path(device_path)


@app.route('/api/volume/get', methods=['POST'])
def get_volume(volume_path=None, strict=False):
    """
    获取卷id和路径
    
    Args:
        volume_path: 要检查的路径（如果为 None，则从请求中获取）
        strict: 严格模式（如果为 None，则从请求中获取）
            - False: 向上检查目录树，获得最近的卷id和路径
            - True: 严格要求给出的路径就是卷的挂载路径
    
    Returns:
        如果从 HTTP 请求调用，返回 JSON 响应；否则返回 (volume_id, volume_path) 元组
    """
    # 如果是从 HTTP 请求调用，从 request 获取参数
    if volume_path is None:
        try:
            data = request.get_json()
            if not data:
                return jsonify({"success": False, "message": "请求体不能为空"}), 400
            
            volume_path = data.get("volume_path")
            strict = data.get("strict", False)
            
            if not volume_path:
                return jsonify({"success": False, "message": "volume_path 参数不能为空"}), 400
            
            volume_id, path = volume_manager.get_volume(volume_path, strict=strict)
            if volume_id is None:
                return jsonify({"success": True, "volume_id": None, "volume_path": None, "message": "未找到卷"}), 200
            
            return jsonify({
                "success": True, 
                "volume_id": volume_id, 
                "volume_path": path, 
                "message": "查询成功"
            }), 200
        except Exception as e:
            logger.error(f"获取卷信息失败: {str(e)}")
            return jsonify({"success": False, "message": f"获取卷信息失败: {str(e)}"}), 500
    
    # 直接调用
    return volume_manager.get_volume(volume_path, strict=strict)


@app.route('/api/volume/check', methods=['POST'])
def check_volume(volume_path=None):
    """
    检查卷的介质情况
    
    Args:
        volume_path: 卷路径（如果为 None，则从请求中获取）
    
    Returns:
        如果从 HTTP 请求调用，返回 JSON 响应；否则返回 None
    """
    # 如果是从 HTTP 请求调用，从 request 获取参数
    if volume_path is None:
        try:
            data = request.get_json()
            if not data:
                return jsonify({"success": False, "message": "请求体不能为空"}), 400
            
            volume_path = data.get("volume_path")
            if not volume_path:
                return jsonify({"success": False, "message": "volume_path 参数不能为空"}), 400
            
            volume_manager.checkVolume(volume_path)
            return jsonify({"success": True, "message": "卷检查完成"}), 200
        except Exception as e:
            logger.error(f"检查卷失败: {str(e)}")
            return jsonify({"success": False, "message": f"检查卷失败: {str(e)}"}), 500
    
    # 直接调用
    volume_manager.checkVolume(volume_path)

