# func_test/ —— 功能测试（functional tests）

## 测试目标

这里做**跨层、真实组件**的功能验证：真实 SQLite、真实仓储、真实服务与 CLI，
只对「必须接触真实硬件/操作系统」的系统探测函数与交互输入打桩。每个用例都
在独立临时目录 + 独立数据库上运行，互不污染。

覆盖范围：

- `test_database_defaults.py` — 建表 + 默认占位数据幂等性。
- `test_persistence_repositories.py` — 五个仓储在真实数据库上的 CRUD、
  外键约束、占用校验、序列号迁移级联。
- `test_lifecycle_workflows.py` — Device → SuperDevice → Volume → SuperVolume
  的完整业务生命周期与删除/序列号变更级联。
- `test_volume_init_flow.py` — 真实目录初始化卷：文件收纳、meta 序列号、
  文件登记与事件日志。
- `test_cli_flows.py` — 通过 CLI 命令完成真实登记 / 查询 / 删除流程。
- `test_config_reload.py` — 临时 YAML 的真实重载与占位符替换。

## 运行方式

```bash
/opt/anaconda3/envs/fileTidy/bin/python -m pytest func_test -q
```

## 约定

每个文件顶部说明目的、输入与期望输出。真实 SQLite 落在 pytest 临时目录，
事件日志与 CLI 输出全部隔离，不影响工作区里的 `datas/`、日志等真实数据。

命名与单元测试一致：文件 `snake_case.py`、类 `PascalCase`、方法/变量 `snake_case`；
文件首行为 AI 生成标记 `# TODO: [AI生成-未检测] ...`。
