<!-- TODO: [AI生成-未检测] 本文件由 AI 生成，尚未经人工检测与审查。 -->
# app_config.py — 应用配置容器

对应代码：`infra/config/app_config.py`

## 职责

把 settings 目录下的所有 YAML 配置聚合成一个容器，并内置一个系统配置 section（`system`）。构造时传入 settings 根目录与可选 `workspace_path`（`${workspace_path}` 占位符根目录），内部据此构造替换表并创建共享 `ConfigWatcher`，对每个 `.yaml/.yml` 建立一个 `SingleFileConfig`，以文件名（stem）为 key 存入字典、透传替换表做占位符替换；另内置一个 `SystemConfig` 作为 `system` section（懒调用实时取数、无热更能力）。查询方式与 `SingleFileConfig` 一致，只是所有参数后移一位、第一个参数变成 section 名。

## 用法

```python
from infra.config.app_config import AppConfig

conf = AppConfig("datas/settings", workspace_path="datas")

conf["restapi"]["port"]            # 两层索引 → 5001
conf.get("restapi", "port")        # get(section, key, default=None)
conf.get_required("log", "cli_log_level")
conf["system"]["cpu_count"]        # 内置系统配置 section（懒调用实时取数）
conf.get("system", "hostname")     # 系统配置宽松读取
"restapi" in conf                  # section 是否存在
conf.data                          # {section: {键: 值}, ...} 快照（含 system）
list(conf.keys())                  # ['base', 'database', 'log', 'restapi', 'system', ...]

conf["restapi"].on_change(lambda keys: print(keys))   # 单 section 回调
conf.reload("restapi")             # 重载指定 section
conf.stop_auto_reload()            # 注销全部监听
conf.watcher.stop()                # 停止共享 watcher
```

## 工作流（生命周期）

1. **构造** `AppConfig(settings_dir, workspace_path=None)`
   - 记录 `settings_dir`；创建共享 `ConfigWatcher(settings_dir)`
   - 有 `workspace_path` 时内部构造替换表 `{"workspace_path": ...}`，对每个 `.yaml/.yml` 建 `SingleFileConfig(path, watcher, replacements)` → `self._sections[stem]`（各子配置构造即自行注册监听）
   - 内置 `self._sections["system"] = SystemConfig()`（懒调用实时取数，无热更能力）
2. **查询**：`conf[section][key]` / `conf.get(section, key, default)` / `conf.get_required(section, key)` / `conf.data`
3. **热更**：任一文件变化 → watcher 按 `src_path` 分发到对应 `SingleFileConfig.reload()` → 触发该 section 的 `on_change` 回调
4. **停止**：`stop_auto_reload()`（注销全部监听）；`watcher.stop()`（停止监听线程）

## 设计思路

- **共享 watcher（方案 A）**：容器统一创建唯一 `ConfigWatcher(settings_dir)`，注入所有子配置共用，只占一份监听线程（1 emitter + 1 dispatcher），详见 `watcher.md`。
- **组合根**：容器是各 `SingleFileConfig` 的组合根，子配置不自行创建 watcher，构造即 `register`。
- **参数后移**：容器查询方法与 `SingleFileConfig` 同名，仅第一个参数变为 section 名，便于按文件定位配置；`conf[section]` 返回子配置实例以支持链式查询。
- **fail-fast 传递**：某 YAML 缺失/解析失败时，其 `SingleFileConfig` 构造抛错，容器构造随之失败——避免带病启动。
- **workspace_path → 替换表**：容器接收一次 `workspace_path`（展开 `~`、绝对化），内部自行构造替换表 `{"workspace_path": ...}` 并透传给各 YAML 子配置，仅对含占位符的配置（如 database/log）生效；不传则不替换。
- **内置系统 section**：容器固定内置 `system`（`SystemConfig`），与 YAML 子配置共用同一套查询接口（都实现 `ConfigContentManager`），可用 `conf["system"]["cpu_count"]` 统一取系统信息；其 reload 无操作（实时取数）。
- **热更能力区分**：`on_change` / `stop_auto_reload` 属文件源（`SingleFileConfig`）扩展能力，`system` 无此能力——容器对无热更能力的 section 自动跳过（`stop_auto_reload`）或明确报错（`on_change` 抛 `TypeError`）。

## API 概览

| 方法 | 说明 |
|------|------|
| `conf[section]` | 返回该 section 的 `ConfigContentManager`，可链式查询 |
| `conf["system"]` | 内置系统配置 section（`SystemConfig`，懒调用实时取数） |
| `get(section, key, default=None)` | section 内宽松读取 |
| `get_required(section, key)` | section 内严格读取，缺失抛 KeyError |
| `section in conf` | section 是否存在 |
| `keys()` / `items()` / `values()` | section 视图 |
| `data` | 所有 section 配置快照 `{section: dict}` |
| `reload(section=None)` | 重载指定或全部，返回是否有变化 |
| `on_change(section, cb)` | 注册指定 section 变更回调 |
| `stop_auto_reload(section=None)` | 注销指定或全部监听（幂等） |
| `is_auto_reload_running` | 共享 watcher 是否运行 |
