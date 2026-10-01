<!-- TODO: [AI生成-未检测] 本文件由 AI 生成，尚未经人工检测与审查。 -->
# tests/ —— 测试总目录

本目录容纳全部测试，分两层：

- `unit_test/` —— 单元测试，目录与源文件**严格一一对应**（下文规则）。
- `func_test/` —— 功能测试，跨层、真实组件，扁平描述性命名。

## 组织原则：unit_test 与源码严格 1:1

对任意源文件 `a/b/c.py`，其单测必须位于 `tests/unit_test/a/b/test_c.py`：

```
domain/storage/device/base.py             →  tests/unit_test/domain/storage/device/test_base.py
application/storage/volume/service.py     →  tests/unit_test/application/storage/volume/test_service.py
infra/system/storage/volume/is_volume.py  →  tests/unit_test/infra/system/storage/volume/test_is_volume.py
interface/cli/device.py                   →  tests/unit_test/interface/cli/test_device.py
```

每个测试目录都带 `__init__.py`，使深层重名文件（如 `test_get_type.py` 在 4 个平台目录下
各一份）能被 pytest 按点分路径导入，不会触发 import file mismatch。

### 不单独建测试文件的模块

以下模块不建 `test_*.py`，其行为由所属包的主测试或 `func_test/` 覆盖：

- `errors.py` / `repo.py` / `events.py`：纯异常声明、抽象基类、事件载体。
- 私有模块 `_*.py`：如各平台 `_common.py`、`infra/persistence/_enum_utils.py`。
  例外：`infra/system/storage/device/_util.py` 的 `as_device_path` 断言并入
  `tests/unit_test/infra/system/storage/device/test_get_path.py`。
- 纯接口：`infra/config/interface.py`。
- 未实现占位：`infra/check.py`（`TODO(P0)`）。
- 根模块 `bootstrap.py` / `main.py`：由 `func_test/` 覆盖。

## 运行方式

```bash
# 用项目 conda 环境（Python 3.12 + 全部运行依赖）执行
/opt/anaconda3/envs/filetidy/bin/python -m pytest tests -q

# 只跑单元测试 / 只跑功能测试
/opt/anaconda3/envs/filetidy/bin/python -m pytest tests/unit_test -q
/opt/anaconda3/envs/filetidy/bin/python -m pytest tests/func_test -q

# 或只跑某一层
/opt/anaconda3/envs/filetidy/bin/python -m pytest tests/unit_test/domain -q
```

> `pytest.ini` 已设 `pythonpath = .` 与 `testpaths = tests`，在仓库根目录直接跑即可。

## 文件约定

每个测试文件顶部都写明：**目的（测什么）、输入、期望输出**；每个测试用例
docstring 同样描述「输入 → 期望输出」。测试不允许修改生产代码。
文件首行为统一的 AI 生成标记 `# TODO: [AI生成-未检测] ...`，便于 Todo Tree 审查。

## mock 边界

凡是会碰真实硬件 / 交互输入 / 网络 / 全局日志的地方，一律注入替身或打桩；
文件系统类用例使用 `tmp_path`。`unit_test/infra/persistence` 使用独立临时 SQLite
做隔离验证，与 `func_test/` 的真实落盘流程形成双层覆盖。
