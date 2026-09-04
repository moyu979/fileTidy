# watcher.py — 共享 ConfigWatcher（方案 A）

对应代码：`infra/config/watcher.py`

## 职责

让所有 xxx_config 共用一份文件监听线程：单个 watchdog Observer 监听配置根目录一次，事件按 `src_path` 分发到各自注册的 `reload()`。watchdog 不可用时自动降级为单个轮询线程。由配置系统顶端的 config 手动实例化并注入各子配置类。

## 工作流

1. **实例化**：顶端 `ConfigWatcher(settings_dir)`，传配置根目录；一个 watcher 注入多个子配置类
2. **注册**：子配置类构造时 `watcher.register(restapi_path, reload)` — 自行登记自己的文件 → 首次注册自动 `start()`
3. **启动** `start()`（幂等）：
   - 优先 watchdog：一个 `Observer` + 一个 `_Handler`，对配置根目录 `schedule` **一次**（单 emitter）
   - 降级：单个 daemon 轮询线程，定时对每个已注册文件调 `reload()`
4. **事件分发**：Handler 收到事件 → 过滤（非目录、且 `.yaml`/`.yml`）→ 按 `src_path` 查注册表 → 去抖（300ms）→ 调 `reload()`
5. **停止**：`stop()`（stop observer + 轮询线程）

## 设计思路

- **方案 A vs 多目录 schedule**：watchdog 每个不同 watch 各建一个 emitter 线程；只有「监听公共父目录一次」才能真正只占 1 个 emitter 线程。实测：3 个目录各 schedule = 3 emitter；schedule 公共父目录 1 次 = 1 emitter。详见下方「线程模型」。
- **为什么共享**：多个子配置类注入同一个 ConfigWatcher 实例，线程数不随配置类数量线性增长。
- **去抖**：编辑器连续保存（含原子保存的 temp+rename）会触发多次事件，300ms 内合并为一次 reload，`on_moved` 用 `dest_path` 兜住重命名覆盖场景。
- **降级轮询无副作用**：`reload()` 内部自带 mtime 判断，轮询重复调用是幂等的。
- **handler 职责单一**：只负责按路径路由，不持有配置状态。

## 线程模型（watchdog）

- `EventEmitter` 是线程（生产者），`Observer` 自身是派发线程（消费者）。
- 线程数 = 1（dispatcher）+ 每个不同 watch 一个 emitter。
- 因此「共享一个 Observer 但 schedule 多个目录」仍是多个 emitter 线程；真正省线程要合并成公共父目录一次 schedule。

## 注意

- watchdog 线程均为 daemon，脚本退出不阻塞。
- 监听目录需存在；目录不存在则自动降级为轮询。
