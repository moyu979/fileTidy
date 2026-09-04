<!-- CHECK: 待检查 - 项目说明文档 -->

# fileTidy — 存储设备管理工具

![Python](https://img.shields.io/badge/Python-3.12+-blue)
![FastAPI](https://img.shields.io/badge/FastAPI-0.136+-green)


**fileTidy** 是一个基于 **领域驱动设计（DDD）** 的存储设备生命周期管理工具，提供从物理设备到文件系统的多层次抽象管理能力。支持命令行（CLI）和 REST API 两种交互方式。

---

## 目录

- [设计理念](#设计理念)
- [核心概念](#核心概念)
- [项目架构](#项目架构)
- [目录结构](#目录结构)
- [快速开始](#快速开始)
- [使用指南](#使用指南)
- [配置说明](#配置说明)
- [开发计划](#开发计划)
- [技术栈](#技术栈)

---

## 设计理念

本系统采用**四层存储抽象模型**，从底层硬件到顶层数据冗余逐层递进：

```
物理设备 (Device)
    ↓
组合设备 (SuperDevice) —— RAID / 多设备组合
    ↓
文件系统卷 (Volume) —— NTFS / exFAT / ext4 等
    ↓
超级卷 (SuperVolume) —— 跨卷冗余 / 复制策略
```

每一层都独立建模，拥有自己的生命周期、状态机、事件日志和持久化机制。

---

## 核心概念

### 1. Device（设备）

物理硬件设备的最小管理单元，代表一块实际的存储介质。

| 类型 | 描述 |
|------|------|
| `HDD` | 机械硬盘 |
| `SSD` | 固态硬盘 |
| `Tape` | 磁带（LTO-5 / LTO-6） |
| `TfSd` | TF 存储卡 |

**核心属性：** 序列号、型号、容量（字节）、状态（Unknown / Healthy / Danger / Fault / Removed）、挂载路径、添加时间、最后检查时间。

### 2. SuperDevice（超级设备 / 组合设备）

由一个或多个物理 Device 组合而成的逻辑设备，对外呈现为单一存储单元。

| 类型 | 描述 |
|------|------|
| `Raidz` | RAID-Z 冗余阵列 |
| `SingleSuperDevice` | 单设备直通（一个 Device 对应一个 SuperDevice） |

**核心属性：** 序列号、名称、类型、是否需要全部设备在线、状态（Healthy / Danger / Degrading / Fault / Removed）、容量、关联的设备列表。

### 3. Volume（卷）

建立在 Device 或 SuperDevice 之上的文件系统层，代表一个可挂载的存储分区。

| 类型 | 描述 |
|------|------|
| `NTFS` | Windows NTFS 文件系统 |
| `FAT32` | FAT32 文件系统 |
| `exFAT` | exFAT 文件系统 |
| `LTFS` | 线性磁带文件系统 |

**核心属性：** 序列号、所属 SuperDevice ID、文件系统类型、唯一挂载点、容量、状态（Unknown / Healthy / Danger / Fault / Removed）。

### 4. SuperVolume（超级卷）

跨多个 Volume 的高级抽象，用于实现数据冗余、备份和分层存储策略。

| 类型 | 描述 |
|------|------|
| `Copy` | 复制模式，多个卷内容保持一致 |
| `SnapRAID RAID5` | SnapRAID RAID5 校验冗余阵列 |

**核心属性：** 序列号、名称、组合方式（method）、状态（Unknown / Healthy / Danger / Fault / Removed）、子卷列表。

### 5. File（文件）

系统中管理的文件实体，每个文件包含来源路径和在卷内的位置信息，分别存储在 `file_sources` 和 `file_locations` 两张表中。

**核心属性：** SHA-512 哈希、MD5 哈希、大小、来源路径、所在卷、卷内路径。

---

## 项目架构

项目采用 **DDD（Domain-Driven Design）** 四层架构：

```
┌─────────────────────────────────────────────┐
│                 Interface                     │
│     CLI (cmd)          FastAPI (REST)        │
├─────────────────────────────────────────────┤
│                Application                    │
│       Device / Volume / SuperDevice          │
│              / SuperVolume Service           │
├─────────────────────────────────────────────┤
│                  Domain                       │
│     Entity · Enum · Event · Repo · Factory  │
│   Device · Volume · SuperDevice · SuperVolume│
├─────────────────────────────────────────────┤
│               Infrastructure                  │
│  Config · DB · Log · System · Path Manager   │
└─────────────────────────────────────────────┘
```

### 各层职责

| 层 | 目录 | 职责 |
|----|------|------|
| **Interface** | `interface/` | 用户交互入口，CLI 命令行界面和 FastAPI REST API |
| **Application** | `application/` | 应用服务层，编排领域对象完成业务用例 |
| **Domain** | `domain/` | 领域核心，业务实体、值对象、枚举、事件、仓储接口、工厂 |
| **Infrastructure** | `infra/` | 基础设施，配置管理、数据库持久化、日志、系统级操作 |

---

## 目录结构

```
fileTidy/
├── main.py                     # 程序入口，参数解析与模式分发
├── bootstrap.py                # 启动引导，依赖注入与初始化
├── setup.py                    # 首次运行时的目录初始化
├── requirements.txt            # Python 依赖
├── todo.md                     # 开发待办
│
├── application/                # 应用层 —— 服务编排
│   ├── app.py                  # 应用主对象，聚合所有服务
│   └── storage/
│       ├── device/             # 设备服务
│       │   ├── factory.py
│       │   └── service.py
│       ├── volume/             # 卷服务
│       │   ├── factory.py
│       │   └── service.py
│       ├── super_device/       # 超级设备服务
│       │   ├── factory.py
│       │   └── service.py
│       ├── super_volume/       # 超级卷服务
│       │   ├── factory.py
│       │   └── service.py
│       └── file/
│           └── file_service.py # 文件注册服务
│
├── domain/                     # 领域层 —— 核心业务逻辑
│   ├── fileSystem/             # 文件系统领域（预留）
│   └── storage/
│       ├── device/             # 设备领域
│       │   ├── base.py         # 抽象基类
│       │   ├── enum.py         # 状态枚举
│       │   ├── events.py       # 领域事件
│       │   ├── factory.py      # 工厂
│       │   ├── repo.py         # 仓储接口
│       │   └── variants/       # 具体实现
│       │       ├── HDD.py
│       │       ├── SSD.py
│       │       ├── Tape.py
│       │       └── TfSd.py
│       ├── volume/             # 卷领域
│       │   ├── base.py
│       │   ├── enum.py
│       │   ├── events.py
│       │   ├── factory.py
│       │   ├── repo.py
│       │   └── variants/
│       │       ├── exfat.py
│       │       ├── fat32.py
│       │       ├── ltfs.py
│       │       └── ntfs.py
│       ├── super_device/       # 超级设备领域
│       │   ├── base.py
│       │   ├── enum.py
│       │   ├── events.py
│       │   ├── factory.py
│       │   ├── repo.py
│       │   └── variants/
│       │       ├── raidz.py
│       │       └── single_super_device.py
│       ├── super_volume/       # 超级卷领域
│       │   ├── __init__.py     # eager-import 变体，填充类型注册表
│       │   ├── base.py
│       │   ├── enum.py
│       │   ├── events.py
│       │   ├── repo.py
│       │   ├── structure.py    # 超级卷-子卷关联关系
│       │   └── variants/
│       │       ├── copy.py
│       │       └── snapraid_raid5.py
│       └── file/
│           ├── events.py
│           ├── new_file.py     # 文件实体
│           └── repo.py
│
├── infra/                      # 基础设施层
│   ├── config/
│   │   └── config.py           # YAML 配置加载
│   ├── log/
│   │   └── logger.py           # 日志系统（按月轮转）
│   ├── operation_log/
│   │   └── operation_log.py   # 操作事件日志
│   ├── persistence/            # 数据库持久化
│   │   ├── database.py         # SQLAlchemy 引擎与会话
│   │   ├── init_db.py          # 数据库初始化
│   │   ├── models.py           # ORM 模型定义
│   │   ├── defaults.py         # 默认占位数据
│   │   └── storage/            # 仓储实现
│   │       ├── device_repository.py
│   │       ├── volume_repository.py
│   │       ├── super_device_repository.py
│   │       ├── super_volume_repository.py
│   │       └── file_repository.py
│   ├── common/                 # infra 内部共享工具（通用算法/工具）
│   │   ├── barcode_generator.py # 条形码生成（Code128）
│   │   ├── capacity_converter.py# 容量单位换算
│   │   ├── hash.py             # 文件哈希（完整性校验）
│   │   ├── id_generator.py     # ID 生成器（基于时间戳）
│   │   ├── merge_dir.py        # 目录合并（补缺）
│   │   ├── runCommand.py       # 命令执行工具
│   │   ├── time_defaults.py    # 时间默认值
│   │   └── xor.py              # 文件异或（字节运算）
│   └── system/                 # 系统级操作（平台适配）
│       ├── path_manager/
│       │   └── is_path.py
│       └── storage/
│           ├── device/         # 设备系统操作
│           │   ├── get_capacity.py
│           │   ├── get_healthy.py
│           │   ├── get_path.py
│           │   ├── get_serial.py
│           │   ├── get_type.py
│           │   ├── is_disk.py
│           │   └── platforms/  # 跨平台实现
│           │       ├── darwin.py
│           │       ├── linux.py
│           │       └── win32.py
│           ├── volume/         # 卷系统操作
│           │   ├── adapter.py
│           │   ├── get_file_system.py
│           │   ├── get_id.py
│           │   ├── get_path.py
│           │   ├── get_super_device_id.py
│           │   └── ...
│           └── file/
│               └── get_file_size.py
│
├── interface/                  # 接口层
│   ├── cli/                    # 命令行界面（基于 cmd 模块）
│   │   ├── cli.py              # 主 CLI
│   │   ├── device.py           # 设备子命令
│   │   ├── volume.py           # 卷子命令
│   │   ├── super_device.py     # 超级设备子命令
│   │   └── super_volume.py     # 超级卷子命令
│   └── fastapi/                # REST API
│       └── service.py          # FastAPI 服务
│
├── assets/                     # 默认资源（首次运行拷贝至 data 目录）
│   ├── logs/
│   │   ├── operation_log/
│   │   └── service_log/
│   └── settings/
│       ├── base.yaml           # 基础配置
│       ├── database.yaml       # 数据库配置
│       ├── log.yaml            # 日志配置
│       └── restapi.yaml        # REST API 配置
│
└── datas/                      # 运行时数据目录（由 assets 初始化）
```

---

## 快速开始

### 环境要求

- Python 3.12+
- 操作系统：macOS / Linux / Windows

### 安装

```bash
# 1. 克隆仓库
git clone <repo-url>
cd fileTidy

# 2. （推荐）创建虚拟环境
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 3. 安装依赖
pip install -r requirements.txt
```

### 运行

```bash
# 默认以 CLI 模式启动
python main.py

# 指定数据目录启动
python main.py --data-dir /path/to/data

# 同时启动 CLI 和 API
python main.py --mode cli --mode api

# 仅启动 API
python main.py --mode api
```

首次运行时，系统会自动将 `assets/` 目录下的默认配置和日志目录结构复制到 `datas/` 目录中。

### CLI 快捷命令

| 命令 | 功能 | 简写 |
|------|------|------|
| `device` | 进入设备管理 | `dev` |
| `volume` | 进入卷管理 | `vol` |
| `super_device` | 进入超级设备管理 | `sdev` |
| `super_volume` | 进入超级卷管理 | `svol` |
| `quit` / `exit` | 退出程序 | — |

在每个子菜单中输入 `help` 查看可用命令，`back` 或 `Ctrl+D` 返回主菜单。

---

## 配置说明

所有配置位于 `{data_dir}/settings/` 目录下，使用 YAML 格式。

### base.yaml

```yaml
workspace_path: ./data          # 工作目录路径
conf_reload_interval: 60        # 配置重载间隔（秒）
hash_once: 1024000              # 单次哈希读取的文件大小（字节）
```

### database.yaml

```yaml
path: "sqlite:///${workspace_path}/database.db"   # 数据库连接 URL
```

### log.yaml

```yaml
cli_log_level: INFO             # 命令行日志等级
file_log_level: INFO            # 文件日志等级
service_log_path: "${workspace_path}/logs/service_log"   # 服务日志路径
operation_log_path: "${workspace_path}/logs/operation_log"   # 操作日志路径
```

日志等级可选：`DEBUG` / `INFO` / `WARNING` / `ERROR` / `CRITICAL`。

### restapi.yaml

```yaml
restapi_port: 5001              # API 端口
restapi_host: 0.0.0.0          # API 监听地址
```

### 配置热重载

`Config` 支持动态重载，有两种方式：

**方式一：手动触发**

```python
config.reload()  # 重新读取所有 YAML 文件，仅文件变化时执行
```

**方式二：后台线程自动重载**

```python
config.start_auto_reload()                # 使用 YAML 中 conf_reload_interval 的值
config.start_auto_reload(interval=30)     # 或指定间隔（秒）
# ...
config.stop_auto_reload()                 # 停止重载线程
```

**注册变更回调**

```python
def on_config_changed(changed_keys: list[str]) -> None:
    print(f"配置节发生变化: {changed_keys}")

config.on_change(on_config_changed)
```

**行为说明：**
- `reload()` 先检查文件 mtime，无变化时跳过（返回 `False`）
- 重载是原子操作——解析成功才替换，失败则保留旧配置并记录错误
- 后台线程重载间隔可通过 `base.conf_reload_interval` 动态调整
- `${key}` 占位符按 `AppConfig` 的 `workspace_path` 构造的替换表在每次重载时重新计算

---

## 技术栈

| 组件 | 技术 |
|------|------|
| **语言** | Python 3.12+ |
| **Web 框架** | FastAPI + Uvicorn |
| **ORM** | SQLAlchemy 2.0+ |
| **数据库** | SQLite |
| **配置** | PyYAML |
| **CLI 框架** | Python `cmd` 标准库 |
| **图片处理** | Pillow |
| **条形码** | python-barcode |
| **架构模式** | 领域驱动设计（DDD） |

---

## 开发计划

项目当前处于 DDD 架构过渡阶段，后续开发重点：

- [ ] 完善数据库插入逻辑与兼容性检查
- [ ] Volume 注册前自动创建单设备 SuperDevice（`single_super_device`），减少用户手动操作
- [ ] **数据库层完整性约束（暂缓）**：当前所有业务约束在 `infra/persistence` 仓储层用代码实现（如「SuperDevice 独占子项」：同一时刻一个子项只能被一个 SuperDevice 以 `USING` 关联持有）。数据库层除已启用的外键外**未加额外约束**。更优做法是加**部分唯一索引** `(sub_device_id) WHERE state='USING'` 作为并发 / 直连数据库时的最后兜底（SQLAlchemy 需用方言参数如 `sqlite_where`，注意跨库写法）。因当前仅 CLI 串行、无并发写入，且约束复杂，暂缓实施——待引入并发或直连 DB 场景时再补
- [ ] 补充完整的 REST API 路由与业务接口
- [ ] 完善跨平台系统调用层（macOS / Linux / Windows）
- [ ] 补充单元测试与集成测试
- [ ] 支持更多文件系统类型（btrfs / ZFS 等）

---

## 许可

本项目尚未添加开源许可证，保留所有权利。
