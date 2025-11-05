"""
Linux系统依赖检查
检查必要的系统命令和工具是否存在
"""

import shutil
import logging
import platform
from typing import Dict, List, Tuple

logger = logging.getLogger(__name__)

# 定义需要检查的依赖
LINUX_DEPENDENCIES = {
    "smartctl": {
        "package": "smartmontools",
        "description": "硬盘SMART信息检测工具",
        "install_commands": {
            "ubuntu": "sudo apt install smartmontools",
            "debian": "sudo apt install smartmontools",
            "centos": "sudo yum install smartmontools",
            "rhel": "sudo yum install smartmontools",
            "fedora": "sudo dnf install smartmontools",
            "arch": "sudo pacman -S smartmontools"
        }
    },
    "lsblk": {
        "package": "util-linux",
        "description": "块设备信息查看工具",
        "install_commands": {
            "ubuntu": "sudo apt install util-linux",
            "debian": "sudo apt install util-linux",
            "centos": "sudo yum install util-linux",
            "rhel": "sudo yum install util-linux",
            "fedora": "sudo dnf install util-linux",
            "arch": "sudo pacman -S util-linux"
        }
    },
    "mount": {
        "package": "mount",
        "description": "文件系统挂载工具",
        "install_commands": {
            "ubuntu": "sudo apt install mount",
            "debian": "sudo apt install mount",
            "centos": "sudo yum install mount",
            "rhel": "sudo yum install mount",
            "fedora": "sudo dnf install mount",
            "arch": "sudo pacman -S mount"
        }
    }
}


def detect_linux_distribution() -> str:
    """
    检测Linux发行版
    返回发行版名称（小写）
    """
    try:
        # 尝试读取 /etc/os-release
        with open("/etc/os-release", "r", encoding="utf-8") as f:
            content = f.read()
            for line in content.split("\n"):
                if line.startswith("ID="):
                    return line.split("=", 1)[1].strip().strip('"')
    except (FileNotFoundError, PermissionError):
        pass
    
    # 备用方法：检查常见发行版标识文件
    distro_files = {
        "/etc/debian_version": "debian",
        "/etc/redhat-release": "centos",  # 简化处理
        "/etc/fedora-release": "fedora",
        "/etc/arch-release": "arch"
    }
    
    for file_path, distro in distro_files.items():
        if platform.system() == "Linux" and platform.path.exists(file_path):
            return distro
    
    return "unknown"


def check_command_exists(command: str) -> bool:
    """
    检查命令是否存在
    """
    return shutil.which(command) is not None


def check_linux_dependencies() -> Tuple[bool, Dict[str, Dict]]:
    """
    检查Linux系统依赖
    
    Returns:
        Tuple[bool, Dict]: (是否所有依赖都满足, 详细检查结果)
    """
    if platform.system() != "Linux":
        logger.warning("当前系统不是Linux，跳过Linux依赖检查")
        return True, {}
    
    distro = detect_linux_distribution()
    logger.info(f"检测到Linux发行版: {distro}")
    
    results = {}
    all_satisfied = True
    
    for command, info in LINUX_DEPENDENCIES.items():
        exists = check_command_exists(command)
        results[command] = {
            "exists": exists,
            "package": info["package"],
            "description": info["description"],
            "install_command": info["install_commands"].get(distro, "未知发行版")
        }
        
        if not exists:
            all_satisfied = False
            logger.error(f"缺少依赖: {command} ({info['description']})，\n安装命令：{results[command]['install_command']}")
        else:
            pass
            # logger.info(f"✓ {command} 已安装")
    
    if all_satisfied:
        logger.info("所有Linux依赖检查通过")
    else:
        logger.error("部分Linux依赖缺失")
    
    return all_satisfied, results


def print_dependency_report(results: Dict[str, Dict]) -> None:
    """
    打印依赖检查报告
    """
    print("\n" + "="*60)
    print("Linux依赖检查报告")
    print("="*60)
    
    for command, info in results.items():
        status = "✓ 已安装" if info["exists"] else "✗ 缺失"
        print(f"{command:<15} {status}")
        print(f"{'':15} 包名: {info['package']}")
        print(f"{'':15} 描述: {info['description']}")
        
        if not info["exists"]:
            print(f"{'':15} 安装: {info['install_command']}")
        print()
    
    print("="*60)


if __name__ == "__main__":
    # 直接运行时的测试
    success, results = check_linux_dependencies()
    print_dependency_report(results)
