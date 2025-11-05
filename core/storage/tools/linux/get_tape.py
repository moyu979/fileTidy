import os
import subprocess
import re
import logging

# 配置日志（与同目录下 get_disk.py 保持一致风格）
# logging.basicConfig(level=logging.WARNING, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def _run_mt_status(dev_path: str) -> str | None:
    """执行 `mt -f <dev> status` 并返回标准输出文本。失败返回 None。"""
    logger.warning("mt status 输出格式可能因驱动/设备/系统不同而变化，解析可能不准确")
    try:
        result = subprocess.run(
            ["mt", "-f", dev_path, "status"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        if result.returncode != 0:
            logger.warning(f"mt status 执行失败: {result.stderr.strip()}")
            return None
        return result.stdout
    except FileNotFoundError:
        # 系统未安装 mt（mt-st）
        logger.warning("未找到 mt 命令，无法获取磁带容量状态")
        return None
    except Exception as exc:
        logger.warning(f"mt status 执行异常: {exc}")
        return None


def _parse_capacity_from_mt_status(output: str) -> dict:
    """从 mt status 输出解析容量信息。

    返回：{"remaining_bytes": int|None, "maximum_bytes": int|None, "remaining_percent": float|None}
    若无法解析，对应字段为 None。
    """
    if not output:
        return {"remaining_bytes": None, "maximum_bytes": None, "remaining_percent": None}

    def _to_bytes(value: float, unit: str | None) -> int | None:
        if value is None:
            return None
        unit = (unit or "B").upper()
        factor = {
            "B": 1,
            "KB": 1024,
            "MB": 1024**2,
            "GB": 1024**3,
            "TB": 1024**4,
        }.get(unit)
        if not factor:
            return None
        try:
            return int(float(value) * factor)
        except Exception:
            return None

    # 常见格式1："Remaining capacity in Partition 0:  887.0 GB (24.2%)"
    rem_cap = re.search(r"Remaining\s+capacity[^:]*:\s*([0-9.]+)\s*(TB|GB|MB|KB|B)?\s*(?:\(([^)]+)%\))?", output, re.IGNORECASE)
    max_cap = re.search(r"Maximum\s+capacity[^:]*:\s*([0-9.]+)\s*(TB|GB|MB|KB|B)?", output, re.IGNORECASE)

    remaining_bytes = _to_bytes(float(rem_cap.group(1)) if rem_cap else None, rem_cap.group(2) if rem_cap else None)
    remaining_percent = float(rem_cap.group(3)) if (rem_cap and rem_cap.group(3)) else None
    maximum_bytes = _to_bytes(float(max_cap.group(1)) if max_cap else None, max_cap.group(2) if max_cap else None)

    # 常见格式2："Remaining tape: 96.8%  893429 MB"
    if remaining_bytes is None and maximum_bytes is None:
        rem_alt = re.search(r"Remaining\s+tape:\s*([0-9.]+)%\s+([0-9.]+)\s*(TB|GB|MB|KB|B)", output, re.IGNORECASE)
        if rem_alt:
            remaining_percent = float(rem_alt.group(1))
            remaining_bytes = _to_bytes(float(rem_alt.group(2)), rem_alt.group(3))

    return {
        "remaining_bytes": remaining_bytes,
        "maximum_bytes": maximum_bytes,
        "remaining_percent": remaining_percent,
    }


def get_tape_capacity(path: str) -> int | None:
    """获取磁带最大容量（字节），基于 mt status。失败返回 None。"""
    if not path or not os.path.exists(path):
        return None
    status_txt = _run_mt_status(path)
    if not status_txt:
        return None
    caps = _parse_capacity_from_mt_status(status_txt)
    return caps.get("maximum_bytes")

_TAPE_NAME_PATTERN = re.compile(r'^st\d+$')


def _is_tape_device_path(dev_path: str) -> bool:
    """校验是否为磁带设备（仅匹配 st* 主节点）。"""
    try:
        name = os.path.basename(str(dev_path))
        return bool(_TAPE_NAME_PATTERN.match(name))
    except Exception:
        return False


def get_tape(path=None) -> list[dict] | str | None:
    """
    获取磁带设备的序列号（ID）。

    行为：
    - 指定 path 且存在：提示用户手动输入序列号，返回列表结构 [{"id","size","path"}]。
    - 指定 path 但不存在：返回 None（与 get_disk 在无效路径时一致）。
    - 未指定 path 或空字符串：返回所有磁带设备信息列表（仿照 get_disk 的返回结构）。

    说明：容量可参考 `mt -f <dev> status`，见本模块辅助函数。
    """
    logger.warning("磁带设备未实现")
    return []
    if not path or not str(path).strip():
        # 遍历所有磁带设备，返回与 get_disk 相同结构的列表
        tape_list: list[dict] = []
        try:
            for dev in os.listdir('/dev'):
                # 只匹配 st*，避免同一物理磁带在 nst* 等节点上被重复计入
                if dev.startswith('st'):
                    dev_path = os.path.join('/dev', dev)
                    if os.path.exists(dev_path):
                        try:
                            user_input = input(f"请手动输入磁带设备 {dev_path} 的序列号(ID)，直接回车跳过: ").strip()
                        except Exception:
                            user_input = None
                        size_bytes = get_tape_capacity(dev_path)
                        tape_list.append({
                            "id": user_input or None,
                            "size": size_bytes,
                            "path": dev_path,
                        })
        except Exception as exc:
            logger.warning(f"遍历磁带设备时出错: {exc}")
        return tape_list
    if not os.path.exists(path):
        return None
    if not _is_tape_device_path(path):
        return None

    # 指定路径：返回与 get_disk 相同的列表结构
    try:
        user_input = input(f"请手动输入磁带设备 {path} 的序列号(ID)，直接回车跳过: ").strip()
    except Exception as exc:
        logger.warning(f"读取用户输入序列号失败: {exc}")
        user_input = None
    size_bytes = get_tape_capacity(path)
    return [{
        "id": user_input or None,
        "size": size_bytes,
        "path": path,
    }]


def main():
    print("=== 磁带信息手动录入测试 ===\n")
    test_paths = ["/dev/st0", "/dev/nst0"]
    for p in test_paths:
        print(f"测试路径: {p}")
        try:
            tape_id = get_tape(p)
            print(f"  返回的序列号: {tape_id}\n")
        except Exception as e:
            print(f"  获取失败: {e}\n")


if __name__ == "__main__":
    main()


