"""temp 临时脚本：以 assets/settings 为配置目录、assets 为 workspace_path，打印全部配置。"""

from pathlib import Path
import sys

# 允许直接运行（python temp/main.py）：将项目根目录加入 sys.path
_PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

from infra.config.app_config import AppConfig


def main() -> None:
    """构造 AppConfig 并打印全部 section 配置。"""
    conf = AppConfig("assets/settings", workspace_path="assets")
    try:
        print("=" * 60)
        print("AppConfig sections:", sorted(conf.keys()))
        print("=" * 60)
        for section in sorted(conf.keys()):
            cfg = conf[section]
            print(f"\n[{section}]")
            for key, value in cfg.data.items():
                print(f"  {key}: {value}")
    finally:
        conf.stop_auto_reload()
        conf.watcher.stop()


if __name__ == "__main__":
    main()
