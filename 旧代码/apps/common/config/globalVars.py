from pathlib import Path

# 应用根目录（apps 目录）
APP_ROOT = Path(__file__).parent.parent.parent

# 资源文件路径
ASSETS_DIR = APP_ROOT / "assets"
DEFAULT_CONFIG_FILE = ASSETS_DIR / "confs.json"

# 工作目录路径
WORKSPACE_PATH = "./data"
CONFIG_PATH = "./data/conf.json"
LOG_PATH = "./data/log"
FILE_LOG_PATH = "./data/file_log"
DATABASE_PATH = "./data/database.db"