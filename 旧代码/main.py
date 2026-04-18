import sys
from apps.core.initer import init
from apps.infra.restapi.restapi import start_rest_api
from apps.infra.cli.cli import main as start_cli

if __name__ == "__main__":
    # 初始化系统（配置、日志、数据库等）
    init()
    
    # 根据命令行参数选择启动模式
    if len(sys.argv) > 1:
        mode = sys.argv[1].lower()
        if mode == 'cli' or mode == '--cli':
            # 启动 CLI 命令行工具
            start_cli()
        elif mode == 'api' or mode == '--api':
            # 启动 REST API 服务器
            start_rest_api()
        else:
            print(f"未知模式: {mode}")
            print("用法: python main.py [cli|api]")
            print("  cli  - 启动命令行工具（网络 API 失效时的临时工具组）")
            print("  api  - 启动 REST API 服务器")
            sys.exit(1)
    else:
        # 默认启动 REST API
        start_rest_api()