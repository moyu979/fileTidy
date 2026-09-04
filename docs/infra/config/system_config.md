# system_config.py — 系统配置读取器（懒调用）

对应代码：`infra/config/system_config.py`

## 职责

封装操作系统级信息获取（hostname / platform / cpu_count / 内存等），实现 `ConfigContentManager` 纯接口（见 `interface.md`）。采用「方法注册表 + 实时系统调用」的懒调用设计：每个配置项对应一个直接系统调用的 getter，注册在内置字典 `_methods`，取数时按 key 查表并调用返回。

## 用法

```python
from infra.config.system_config import SystemConfig

config = SystemConfig()
config.get("hostname")            # 宽松：无此 key 返回 default
config["platform"]                # 严格：无此 key 抛 KeyError
config.get_required("cpu_count")
"cpu_count" in config
config.data                       # 实时全量快照
config.get_memory_used()          # 专用 getter：直接系统调用
```

## 工作流（取数流程）

1. **构造** `SystemConfig()`：注册 `_methods`，key → 实时系统调用 getter（不预采集任何数据）
2. **取数**：按 key 从 `_methods` 查方法
   - 无此 key → `get` 返回 default；`get_required` / `__getitem__` 抛 `KeyError`
   - 有方法 → 调用并返回其返回值（实时系统调用）
3. **刷新**：`reload()` 无操作（实时取数，无缓存可刷新），返回 False
4. **摘要**：`summary()` 基于 `self.data`（实时取全部 key）

## 设计思路

- **懒调用 vs 快照**：不预采集、不缓存——每次取数是真实系统调用，永远拿到最新值；省去缓存一致性/失效问题，契合系统参数「变动不频繁、读多」的场景。
- **方法注册表**：`_methods: dict[str, Callable]` 把「配置项 key」映射到「取数方法」，统一走查表 + 调用；新增配置项 = 新增一个 getter + 注册一行，扩展成本低。
- **只读、无锁**：系统配置不参与写入/热更，无需锁；也正因只读，`reload` 无意义（置为无操作）。
- **与 SingleFileConfig 的差异被接口吸收**：两者都实现 `ConfigContentManager`，但锁/热更/占位符替换（`${key}`）属于文件源特有，系统源只保留实时取数——`get` / `data` 等查询入口完全一致。
- **单次采样**：`get_memory_info()` 用一次 `psutil.virtual_memory()` 采样内存各字段，避免多次调用产生不一致；`summary()` 则容忍逐 key 取数的微小漂移。

## API 概览

| 方法 | 说明 |
|------|------|
| `get(key, default=None)` | 宽松读取，无此 key 返回 default |
| `get_required(key)` | 严格读取，无此 key 抛 KeyError |
| `config[key]` | 同 `get_required` |
| `data` | 实时全量快照 `{key: 值}` |
| `reload()` | 无操作（实时取数），返回 False |
| `get_hostname()` / `get_platform()` / ... | 专用 getter，直接系统调用 |
| `get_memory_info()` | 内存单次采样快照 |
| `summary()` | 常用信息摘要 |
