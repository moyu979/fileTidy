# single_file_config.py — 单文件配置通用类（热更新）

对应代码：`infra/config/single_file_config.py`

## 职责

抽象单个 YAML 配置文件（如 `restapi.yaml` / `database.yaml` / `hash.yaml` / `log.yaml`）的加载、读取与热更新逻辑。实现 `ConfigContentManager` 纯接口（见 `interface.md`）；锁、热更框架与占位符替换（`${key}`，替换表由参数传入）均在本类内部，是接口契约的「文件源」实现。传入配置路径、共享 ConfigWatcher 与可选 `replacements` 替换表即可实例化，一个类覆盖全部 `xxx_config` 场景。

## 用法

```python
from infra.config.watcher import ConfigWatcher
from infra.config.single_file_config import SingleFileConfig

watcher = ConfigWatcher("datas/settings")                    # 顶端唯一创建
restapi = SingleFileConfig("datas/settings/restapi.yaml", watcher)
db      = SingleFileConfig("datas/settings/database.yaml", watcher,
                           replacements={"workspace_path": "/path/to/datas"})
log     = SingleFileConfig("datas/settings/log.yaml", watcher,
                           replacements={"workspace_path": "/path/to/datas"})

restapi["restapi_port"]        # 必填项，缺失抛 KeyError
db.get("timeout", 30)          # 可选项，缺失返回默认
restapi.on_change(lambda keys: print(keys))
```

`replacements` 替换表仅对包含 `${key}` 占位符的配置文件有意义（如 `database.yaml` 的 `path`、`log.yaml` 的日志路径）；表内每个 key 都会替换，不传则不替换。实际使用中替换表由 `AppConfig` 按 `workspace_path` 参数内部构造后透传（见 `app_config.md`）。

## 工作流（生命周期）

1. **构造** `SingleFileConfig(path, watcher, replacements=None)`
   - 记录 `path`（展开 `~`、绝对化）；可选 `replacements` 用于 `${key}` 占位符替换
   - `load()` 首次读取 YAML → 递归替换 `${key}` → `self._data`
   - `watcher.register(path, self.reload)` — 构造即开始监听
2. **热更监听**（watchdog，由 `watcher.py` 驱动）
   - 文件变化 → ConfigWatcher 按 `src_path` 分发 → `reload()`
   - `reload()`：mtime 变了才重读 → 替换占位符 → 计算变化的键 → 原子替换 `_data` → 触发 `on_change`
3. **读取**：`config[key]` / `get_required()` / `get(key, default)`
4. **停止**：`stop_auto_reload()` 注销监听（幂等）

## 设计思路

- **fail-fast 读取**：必填项缺失直接抛 `KeyError`（错误信息含配置文件路径），不做静默缺省——避免 YAML 笔误/漏配被默认值掩盖，到运行时才暴露。可选项才用 `get(key, default)`。
- **占位符替换**：`${key}` 按 `replacements` 表递归替换（str/dict/list/tuple），每个 key 独立替换；替换表为空则原样返回。表由 `AppConfig` 根据 `workspace_path` 内部构造后透传。
- **共享监听（方案 A）**：由配置系统顶端创建唯一 `ConfigWatcher(settings_dir)`，所有配置文件共用一份监听线程（1 emitter + 1 dispatcher），详见 `watcher.md`。
- **线程安全**：`RLock` 保护 `_data`；变更回调在锁外执行，避免死锁。
- **reload 幂等**：解析失败保留旧配置并刷新 mtime，避免反复重试同一错误文件。

## API 概览

| 方法 | 说明 |
|------|------|
| `get(key, default=None)` | 宽松读取，仅用于可选项 |
| `get_required(key)` | 严格读取必填项，缺失抛 KeyError |
| `config[key]` | 同 `get_required` |
| `reload()` | 热重载，返回是否有变化 |
| `on_change(cb)` | 注册变更回调（收到变化的键名列表） |
| `stop_auto_reload()` | 注销监听（幂等） |
| `is_auto_reload_running` | 共享 watcher 是否运行 |
