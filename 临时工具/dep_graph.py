#!/usr/bin/env python3
"""
存储依赖关系图生成工具

绘制 Device → SuperDevice → Volume → SuperVolume 之间的分层依赖关系，
粒度精确到每一个实例（按 serial 区分）。

输出格式: PDF / PNG / SVG（默认 PDF）

依赖:
    pip install graphviz
    brew install graphviz           # macOS
    sudo apt install graphviz       # Ubuntu/Debian

用法:
    python 临时工具/dep_graph.py                          # 使用默认数据库路径
    python 临时工具/dep_graph.py -o output.pdf             # 指定输出文件
    python 临时工具/dep_graph.py -f png                   # 指定输出格式
    python 临时工具/dep_graph.py --db /path/to/database.db # 指定数据库

原理说明:
    这种从左到右按层级排列的依赖关系图称为「分层依赖图」
    （Layered Dependency Graph），用 Graphviz 的 dot 布局引擎
    可以完美呈现。
"""

import argparse
import os
import sqlite3
import sys

# ── 将项目根目录加入 sys.path ──────────────────────────────────────────────
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

# ══════════════════════════════════════════════════════════════════════════════
#  数据查询
# ══════════════════════════════════════════════════════════════════════════════


def find_database(default_db: str | None = None) -> str:
    """按优先级查找可用的 SQLite 数据库文件。"""
    candidates = []

    # 1) 传入的默认路径
    if default_db and os.path.isfile(default_db):
        candidates.append(default_db)

    # 2) assets 下的数据库
    assets_db = os.path.join(PROJECT_ROOT, "assets", "database.db")
    if os.path.isfile(assets_db):
        candidates.append(assets_db)

    # 3) datas 下的数据库
    datas_db = os.path.join(PROJECT_ROOT, "datas", "database.db")
    if os.path.isfile(datas_db):
        candidates.append(datas_db)

    if not candidates:
        print("错误: 找不到数据库文件。请通过 --db 参数指定路径。")
        print(f"  项目根目录: {PROJECT_ROOT}")
        print("  例如: python 临时工具/dep_graph.py --db /path/to/database.db")
        sys.exit(1)

    chosen = candidates[0]
    if len(candidates) > 1:
        print(f"找到多个数据库，使用: {chosen}")
    else:
        print(f"数据库: {chosen}")

    return chosen


def query_devices(conn: sqlite3.Connection) -> list[dict]:
    """查询所有设备 (Device)。"""
    rows = conn.execute(
        "SELECT serial, name, type, state FROM devices ORDER BY serial"
    ).fetchall()
    return [
        {"serial": r[0], "name": r[1], "type": r[2], "state": r[3]}
        for r in rows
    ]


def query_super_devices(conn: sqlite3.Connection) -> list[dict]:
    """查询所有超级设备 (SuperDevice) 及其关联的子设备。"""
    rows = conn.execute(
        "SELECT serial, name, type, state FROM super_devices ORDER BY serial"
    ).fetchall()
    super_devices = [
        {"serial": r[0], "name": r[1], "type": r[2], "state": r[3]}
        for r in rows
    ]

    # 查询每个超级设备关联了哪些子设备（只取 USING 状态的）
    dev_map = conn.execute(
        """SELECT super_device_id, sub_device_id
           FROM device_structures
           WHERE state = 'using'
           ORDER BY super_device_id, sub_device_id"""
    ).fetchall()

    # 构建 serial → [device_serials] 的映射
    children: dict[str, list[str]] = {sd["serial"]: [] for sd in super_devices}
    for super_id, sub_id in dev_map:
        if super_id in children:
            children[super_id].append(sub_id)

    for sd in super_devices:
        sd["devices"] = children.get(sd["serial"], [])

    return super_devices


def query_volumes(conn: sqlite3.Connection) -> list[dict]:
    """查询所有卷 (Volume)。"""
    rows = conn.execute(
        "SELECT serial, device_id, name, file_system, state FROM volumes ORDER BY serial"
    ).fetchall()
    return [
        {"serial": r[0], "device_id": r[1], "name": r[2], "file_system": r[3], "state": r[4]}
        for r in rows
    ]


def query_super_volumes(conn: sqlite3.Connection) -> list[dict]:
    """查询所有超级卷 (SuperVolume) 及其关联的子卷。"""
    rows = conn.execute(
        "SELECT serial, name, type, method, state FROM super_volumes ORDER BY serial"
    ).fetchall()
    super_volumes = [
        {"serial": r[0], "name": r[1], "type": r[2], "method": r[3], "state": r[4]}
        for r in rows
    ]

    # 查询每个超级卷关联了哪些子卷（只取 USING 状态的）
    vol_map = conn.execute(
        """SELECT super_volume_id, volume_id
           FROM super_volume_structures
           WHERE state = 'using'
           ORDER BY super_volume_id, volume_id"""
    ).fetchall()

    children: dict[str, list[str]] = {sv["serial"]: [] for sv in super_volumes}
    for sv_id, v_id in vol_map:
        if sv_id in children:
            children[sv_id].append(v_id)

    for sv in super_volumes:
        sv["volumes"] = children.get(sv["serial"], [])

    return super_volumes


# ══════════════════════════════════════════════════════════════════════════════
#  Graphviz 渲染
# ══════════════════════════════════════════════════════════════════════════════


def _node_id(prefix: str, serial: str) -> str:
    """生成 Graphviz 节点 ID（把 serial 中的特殊字符转义为下划线）。"""
    safe = serial.replace("-", "_").replace(" ", "_").replace(".", "_")
    return f"{prefix}_{safe}"


def _node_label(name: str, serial: str, extra: str = "") -> str:
    """生成节点显示标签。"""
    label = f"«{name}»\\n{serial}" if name and name != serial else serial
    if extra:
        label += f"\\n({extra})"
    return label


def _state_color(state: str | None) -> str:
    """根据状态返回颜色（Graphviz 颜色名）。"""
    if state is None:
        return "gray80"
    s = str(state).lower()
    if s in ("healthy", "health"):
        return "#4CAF50"         # 绿色
    if s in ("danger",):
        return "#FF9800"         # 橙色
    if s in ("degrading", "degraded"):
        return "#FFC107"         # 黄色
    if s in ("fault", "error", "unknown"):
        return "#F44336"         # 红色
    if s in ("removed", "unused"):
        return "#9E9E9E"         # 灰色
    return "gray80"


def _state_font_color(state: str | None) -> str:
    """根据状态返回字体颜色。"""
    s = str(state).lower() if state else ""
    if s in ("fault", "error", "unknown", "removed", "unused"):
        return "white"
    return "black"


def build_graph(
    devices: list[dict],
    super_devices: list[dict],
    volumes: list[dict],
    super_volumes: list[dict],
) -> str:
    """
    用 Graphviz DOT 语言构建依赖关系图。

    布局说明:
        从左到右四层: Device → SuperDevice → Volume → SuperVolume
        使用 subgraph + rank=same 确保同层节点对齐。
    """
    try:
        import graphviz
    except ImportError:
        print("错误: 需要 graphviz 库。")
        print("  安装: pip install graphviz")
        print("  系统依赖: brew install graphviz   (macOS)")
        print("            sudo apt install graphviz (Linux)")
        sys.exit(1)

    dot = graphviz.Digraph(
        name="storage_dependency",
        comment="存储依赖关系图 — Device → SuperDevice → Volume → SuperVolume",
        format="pdf",
    )

    # ── 全局属性 ──────────────────────────────────────────────────────────
    dot.attr(
        rankdir="LR",           # 从左到右布局
        ranksep="2.0",          # 层级间距
        nodesep="0.5",          # 同层节点间距
        splines="ortho",        # 直角连线 (更清晰)
        fontname="PingFang SC,Heiti SC,Noto Sans CJK SC,sans-serif",
        label="存储依赖关系图",
        labelloc="t",
        fontsize="20",
        pad="0.5",
        dpi="150",
        bgcolor="#FAFAFA",
    )
    dot.attr("node",
        shape="box",
        style="filled,rounded",
        penwidth="1.5",
        fontname="PingFang SC,Heiti SC,Noto Sans CJK SC,sans-serif",
        fontsize="10",
    )
    dot.attr("edge",
        penwidth="1.5",
        color="#546E7A",
        arrowhead="vee",
        fontname="PingFang SC,Heiti SC,Noto Sans CJK SC,sans-serif",
        fontsize="9",
    )

    # ── 第 1 层: Device ───────────────────────────────────────────────────
    with dot.subgraph(name="cluster_devices") as sub:
        sub.attr(
            label="Device (硬件设备)",
            style="filled",
            fillcolor="#E3F2FD",
            color="#1565C0",
            fontcolor="#1565C0",
            fontsize="14",
        )
        for dev in devices:
            nid = _node_id("dev", dev["serial"])
            color = _state_color(dev["state"])
            font_c = _state_font_color(dev["state"])
            extra = dev["type"] or ""
            sub.node(
                nid,
                label=_node_label(dev["name"], dev["serial"], extra),
                fillcolor=color,
                fontcolor=font_c,
            )

    # ── 第 2 层: SuperDevice ─────────────────────────────────────────────
    with dot.subgraph(name="cluster_super_devices") as sub:
        sub.attr(
            label="SuperDevice (超级设备)",
            style="filled",
            fillcolor="#FFF3E0",
            color="#E65100",
            fontcolor="#E65100",
            fontsize="14",
        )
        for sd in super_devices:
            nid = _node_id("sd", sd["serial"])
            color = _state_color(sd["state"])
            font_c = _state_font_color(sd["state"])
            extra = sd["type"] or ""
            sub.node(
                nid,
                label=_node_label(sd["name"], sd["serial"], extra),
                fillcolor=color,
                fontcolor=font_c,
            )

    # ── 第 3 层: Volume ──────────────────────────────────────────────────
    with dot.subgraph(name="cluster_volumes") as sub:
        sub.attr(
            label="Volume (卷)",
            style="filled",
            fillcolor="#E8F5E9",
            color="#2E7D32",
            fontcolor="#2E7D32",
            fontsize="14",
        )
        for vol in volumes:
            nid = _node_id("vol", vol["serial"])
            color = _state_color(vol["state"])
            font_c = _state_font_color(vol["state"])
            extra = vol["file_system"] or ""
            sub.node(
                nid,
                label=_node_label(vol["name"], vol["serial"], extra),
                fillcolor=color,
                fontcolor=font_c,
            )

    # ── 第 4 层: SuperVolume ─────────────────────────────────────────────
    with dot.subgraph(name="cluster_super_volumes") as sub:
        sub.attr(
            label="SuperVolume (超级卷)",
            style="filled",
            fillcolor="#F3E5F5",
            color="#6A1B9A",
            fontcolor="#6A1B9A",
            fontsize="14",
        )
        for sv in super_volumes:
            nid = _node_id("sv", sv["serial"])
            color = _state_color(sv["state"])
            font_c = _state_font_color(sv["state"])
            extra = f"{sv['type'] or ''} / {sv['method'] or ''}"
            sub.node(
                nid,
                label=_node_label(sv["name"], sv["serial"], extra),
                fillcolor=color,
                fontcolor=font_c,
            )

    # ── 边: 依赖关系 ──────────────────────────────────────────────────────

    # SuperDevice → Device
    for sd in super_devices:
        sd_id = _node_id("sd", sd["serial"])
        for dev_serial in sd["devices"]:
            dev_id = _node_id("dev", dev_serial)
            dot.edge(dev_id, sd_id, label="contains")  # Device → SuperDevice

    # Volume → Device 或 SuperDevice
    # 先建一个所有已知 serial 的集合来判断引用目标类型
    device_serials = {d["serial"] for d in devices}
    super_device_serials = {sd["serial"] for sd in super_devices}

    for vol in volumes:
        vol_id = _node_id("vol", vol["serial"])
        target = vol["device_id"]
        if target in device_serials:
            target_id = _node_id("dev", target)
        elif target in super_device_serials:
            target_id = _node_id("sd", target)
        else:
            # 引用了不存在的 serial，作为外部节点虚线显示
            target_id = _node_id("ext", target)
            dot.node(
                target_id,
                label=f"? {target}",
                fillcolor="white",
                style="dashed",
                fontcolor="gray",
            )
        dot.edge(target_id, vol_id, label="on")

    # SuperVolume → Volume 或 SuperVolume
    volume_serials = {v["serial"] for v in volumes}
    super_volume_serials = {sv["serial"] for sv in super_volumes}

    for sv in super_volumes:
        sv_id = _node_id("sv", sv["serial"])
        for child_serial in sv["volumes"]:
            if child_serial in volume_serials:
                child_id = _node_id("vol", child_serial)
            elif child_serial in super_volume_serials:
                child_id = _node_id("sv", child_serial)
            else:
                # 引用了不存在的 serial
                child_id = _node_id("ext", child_serial)
                dot.node(
                    child_id,
                    label=f"? {child_serial}",
                    fillcolor="white",
                    style="dashed",
                    fontcolor="gray",
                )
            dot.edge(child_id, sv_id, label="contains")

    return dot


# ══════════════════════════════════════════════════════════════════════════════
#  入口
# ══════════════════════════════════════════════════════════════════════════════


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="存储依赖关系图生成工具 — 绘制 Device → SuperDevice → Volume → SuperVolume 的分层依赖图",
    )
    parser.add_argument(
        "--db",
        default=None,
        help="SQLite 数据库路径（默认自动查找 assets/datas 下的 database.db）",
    )
    parser.add_argument(
        "-o", "--output",
        default=None,
        help="输出文件路径（不含扩展名，默认根据格式自动命名）",
    )
    parser.add_argument(
        "-f", "--format",
        default="pdf",
        choices=("pdf", "png", "svg"),
        help="输出格式 (默认: pdf)",
    )
    parser.add_argument(
        "--engine",
        default="dot",
        choices=("dot", "neato", "fdp", "sfdp", "circo", "twopi"),
        help="Graphviz 布局引擎 (默认: dot，分层图推荐 dot)",
    )
    return parser.parse_args(argv)


def main() -> None:
    args = parse_args()

    # ── 1. 定位数据库 ─────────────────────────────────────────────────────
    db_path = find_database(args.db)

    # ── 2. 查询数据 ───────────────────────────────────────────────────────
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row

    devices = query_devices(conn)
    super_devices = query_super_devices(conn)
    volumes = query_volumes(conn)
    super_volumes = query_super_volumes(conn)

    conn.close()

    print(f"  Device:       {len(devices)} 个")
    print(f"  SuperDevice:  {len(super_devices)} 个")
    print(f"  Volume:       {len(volumes)} 个")
    print(f"  SuperVolume:  {len(super_volumes)} 个")

    if not any([devices, super_devices, volumes, super_volumes]):
        print("数据库中没有数据，无法生成依赖图。")
        sys.exit(0)

    # ── 3. 构建图 ─────────────────────────────────────────────────────────
    dot = build_graph(devices, super_devices, volumes, super_volumes)

    # ── 4. 设置输出 ───────────────────────────────────────────────────────
    dot.format = args.format
    dot.engine = args.engine

    output_name = args.output or os.path.join(
        PROJECT_ROOT, "临时工具", "dep_graph_output"
    )
    output_path = dot.render(output_name, cleanup=True)

    print(f"\n✅ 依赖关系图已生成: {output_path}")
    print(f"   布局引擎: {args.engine}，格式: {args.format}")


if __name__ == "__main__":
    main()
