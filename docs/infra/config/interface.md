# interface.py — 配置内容管理纯接口

对应代码：`infra/config/interface.py`

## 职责

定义所有「介入配置系统」的配置类（`SingleFileConfig` / `SystemConfig` 及未来 conf）必须实现的统一取数/刷新契约（`ConfigContentManager`）。它是一个**纯接口**：不持有任何数据、锁或实现，只做方法签名约束，供配置容器（`AppConfig`）统一调度。

## 接口定义

```python
class ConfigContentManager(ABC):
    def get(self, key, default=None): ...
    def get_required(self, key): ...
    def __getitem__(self, key): ...
    def __contains__(self, key): ...
    @property
    def data(self): ...
    def reload(self): ...
```

## 工作流（生命周期）

1. **介入**：任何新配置类 `class Xxx(ConfigContentManager)` 实现全部抽象方法
2. **调度**：容器（AppConfig）通过统一接口查询，无需关心具体来源（文件 / 系统 / 未来其它）
3. **刷新**：`reload()` 语义由各实现定义（文件源：热更重读；系统源：无操作）

## 设计思路

- **纯接口**：无 `_data` / `_lock`、无任何实现——职责只在「约束契约」，不越界管状态。
- **接口 vs 实现分离**：
  - 锁、热更框架、占位符替换（`${key}`，替换表由参数传入）→ 归 `SingleFileConfig`（需要并发与热更的才有）
  - 实时系统调用、方法注册表 → 归 `SystemConfig`（只读，无锁、无缓存）
  - 各自实现的差异被接口吸收，容器只认接口。
- **热更不是通用契约**：`on_change` / `stop_auto_reload` / `is_auto_reload_running` 是 `SingleFileConfig` 的扩展能力，不放入接口——否则无热更能力的实现（如系统配置）也要被迫实现 no-op。
- **fail-fast 语义**：`get_required` / `__getitem__` 缺失抛 `KeyError`，`get` 宽松返回默认值——统一了「必填 vs 可选」的读取约定。

## API 概览

| 方法 | 契约 |
|------|------|
| `get(key, default=None)` | 宽松读取，缺失返回 default |
| `get_required(key)` | 严格读取，缺失抛 KeyError |
| `config[key]` | 同 `get_required` |
| `key in config` | 配置项是否存在 |
| `data` | 当前配置快照（拷贝） |
| `reload()` | 刷新内容，返回是否有变化 |
