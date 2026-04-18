"""REST API 总启动端。"""

from apps.common.log.logger import Logger as logger

from apps.common.config.config import config_manager
from flask import Flask

#from apis.routes.files import files_bp

app = Flask(__name__)


def start_rest_api():
    """启动 REST API 服务器。"""
    # 注册蓝图
    #app.register_blueprint(files_bp)
    
    logger.info("REST API 服务器启动")
    app.run(debug=True, host=config_manager.get("restapi_host"), port=config_manager.get("restapi_port"))

