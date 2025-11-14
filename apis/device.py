"""
设备相关的 API 接口，转发到 DeviceManager
"""

import logging
from flask import request, jsonify
from component.device.deviceManager import device_manager
from .restapi import app

logger = logging.getLogger(__name__)


@app.route('/api/device/reg', methods=['POST'])
def reg_device(path=None):
    """
    注册一个设备到数据库
    
    Args:
        path: 设备路径（如果为 None，则从请求中获取）
    
    Returns:
        如果从 HTTP 请求调用，返回 JSON 响应；否则返回 None
    """
    # 如果是从 HTTP 请求调用，从 request 获取参数
    if path is None:
        try:
            data = request.get_json()
            if not data:
                return jsonify({"success": False, "message": "请求体不能为空"}), 400
            
            path = data.get("path")
            if not path:
                return jsonify({"success": False, "message": "path 参数不能为空"}), 400
            
            device_manager.regDevice(path)
            return jsonify({"success": True, "message": "设备注册成功"}), 200
        except Exception as e:
            logger.error(f"注册设备失败: {str(e)}")
            return jsonify({"success": False, "message": f"注册设备失败: {str(e)}"}), 500
    
    # 直接调用
    device_manager.regDevice(path)


@app.route('/api/device/replace', methods=['POST'])
def replace_device(path1=None, path2=None):
    """
    用 path1 的设备替换掉 path2 的设备
    
    Args:
        path1: 新设备路径（如果为 None，则从请求中获取）
        path2: 要被替换的设备路径（如果为 None，则从请求中获取）
    
    Returns:
        如果从 HTTP 请求调用，返回 JSON 响应；否则返回 None
    """
    # 如果是从 HTTP 请求调用，从 request 获取参数
    if path1 is None or path2 is None:
        try:
            data = request.get_json()
            if not data:
                return jsonify({"success": False, "message": "请求体不能为空"}), 400
            
            path1 = data.get("path1")
            path2 = data.get("path2")
            
            if not path1:
                return jsonify({"success": False, "message": "path1 参数不能为空"}), 400
            if not path2:
                return jsonify({"success": False, "message": "path2 参数不能为空"}), 400
            
            device_manager.replaceDevice(path1, path2)
            return jsonify({"success": True, "message": "设备替换成功"}), 200
        except Exception as e:
            logger.error(f"替换设备失败: {str(e)}")
            return jsonify({"success": False, "message": f"替换设备失败: {str(e)}"}), 500
    
    # 直接调用
    device_manager.replaceDevice(path1, path2)


@app.route('/api/device/check', methods=['POST'])
def check_device(path=None):
    """
    检查设备的介质情况
    
    Args:
        path: 设备路径（如果为 None，则从请求中获取）
    
    Returns:
        如果从 HTTP 请求调用，返回 JSON 响应；否则返回 None
    """
    # 如果是从 HTTP 请求调用，从 request 获取参数
    if path is None:
        try:
            data = request.get_json()
            if not data:
                return jsonify({"success": False, "message": "请求体不能为空"}), 400
            
            path = data.get("path")
            if not path:
                return jsonify({"success": False, "message": "path 参数不能为空"}), 400
            
            device_manager.checkDevice(path)
            return jsonify({"success": True, "message": "设备检查完成"}), 200
        except Exception as e:
            logger.error(f"检查设备失败: {str(e)}")
            return jsonify({"success": False, "message": f"检查设备失败: {str(e)}"}), 500
    
    # 直接调用
    device_manager.checkDevice(path)


@app.route('/api/device/exists', methods=['POST'])
def device_exists(path=None):
    """
    检查给定的设备是否存在
    
    Args:
        path: 设备路径（如果为 None，则从请求中获取）
    
    Returns:
        如果从 HTTP 请求调用，返回 JSON 响应；否则返回 bool
    """
    # 如果是从 HTTP 请求调用，从 request 获取参数
    if path is None:
        try:
            data = request.get_json()
            if not data:
                return jsonify({"success": False, "message": "请求体不能为空"}), 400
            
            path = data.get("path")
            if not path:
                return jsonify({"success": False, "message": "path 参数不能为空"}), 400
            
            exists = device_manager.exists_in_database(device_path=path)
            return jsonify({"success": True, "exists": exists, "message": "查询成功"}), 200
        except Exception as e:
            logger.error(f"查询设备失败: {str(e)}")
            return jsonify({"success": False, "message": f"查询设备失败: {str(e)}"}), 500
    
    # 直接调用
    return device_manager.exists_in_database(device_path=path)


@app.route('/api/device/path', methods=['POST'])
def get_path(serial=None):
    """
    根据序列号获取设备路径
    
    Args:
        serial: 设备序列号（如果为 None，则从请求中获取）
    
    Returns:
        如果从 HTTP 请求调用，返回 JSON 响应；否则返回设备路径
    """
    # 如果是从 HTTP 请求调用，从 request 获取参数
    if serial is None:
        try:
            data = request.get_json()
            if not data:
                return jsonify({"success": False, "message": "请求体不能为空"}), 400
            
            serial = data.get("serial")
            if not serial:
                return jsonify({"success": False, "message": "serial 参数不能为空"}), 400
            
            path = device_manager.get_path(serial)
            return jsonify({"success": True, "path": path, "message": "查询成功"}), 200
        except Exception as e:
            logger.error(f"获取设备路径失败: {str(e)}")
            return jsonify({"success": False, "message": f"获取设备路径失败: {str(e)}"}), 500
    
    # 直接调用
    return device_manager.get_path(serial)


@app.route('/api/device/serial', methods=['POST'])
def get_serial(path=None):
    """
    根据设备路径获取序列号
    
    Args:
        path: 设备路径（如果为 None，则从请求中获取）
    
    Returns:
        如果从 HTTP 请求调用，返回 JSON 响应；否则返回序列号
    """
    # 如果是从 HTTP 请求调用，从 request 获取参数
    if path is None:
        try:
            data = request.get_json()
            if not data:
                return jsonify({"success": False, "message": "请求体不能为空"}), 400
            
            path = data.get("path")
            if not path:
                return jsonify({"success": False, "message": "path 参数不能为空"}), 400
            
            serial = device_manager.get_Serial(path)
            return jsonify({"success": True, "serial": serial, "message": "查询成功"}), 200
        except Exception as e:
            logger.error(f"获取设备序列号失败: {str(e)}")
            return jsonify({"success": False, "message": f"获取设备序列号失败: {str(e)}"}), 500
    
    # 直接调用
    return device_manager.get_Serial(path)


@app.route('/api/device/capacity', methods=['POST'])
def get_capacity(path=None):
    """
    根据设备路径获取容量
    
    Args:
        path: 设备路径（如果为 None，则从请求中获取）
    
    Returns:
        如果从 HTTP 请求调用，返回 JSON 响应；否则返回设备容量
    """
    # 如果是从 HTTP 请求调用，从 request 获取参数
    if path is None:
        try:
            data = request.get_json()
            if not data:
                return jsonify({"success": False, "message": "请求体不能为空"}), 400
            
            path = data.get("path")
            if not path:
                return jsonify({"success": False, "message": "path 参数不能为空"}), 400
            
            capacity = device_manager.get_capacity(path)
            return jsonify({"success": True, "capacity": capacity, "message": "查询成功"}), 200
        except Exception as e:
            logger.error(f"获取设备容量失败: {str(e)}")
            return jsonify({"success": False, "message": f"获取设备容量失败: {str(e)}"}), 500
    
    # 直接调用
    return device_manager.get_capacity(path)

