<!-- TODO: [AI生成-未检测] 本文件由 AI 生成，尚未经人工检测与审查。 -->
# tests/ —— 单元测试（unit tests）

## 测试目标

本目录对应「标准单元测试层」，**逐层、单类、单方法地验证业务规则**：

- `domain/`：领域实体、工厂分派、快照/JSON 序列化、枚举与菜单。纯逻辑，不落库。
- `application/`：应用服务编排。仓储用内存替身（`_support.py`），系统函数与事件日志用
  monkeypatch 隔离，不触真实硬件 / 数据库 / 日志文件。
- `infra/`：基础设施工具、配置热更、系统判定函数。文件系统类用例使用 `tmp_path`
  临时目录，平台探测类用例 mock `subprocess` / `input`。
- `interface/`：CLI 纯函数辅助（KV 解析、info 合并、规格采集等）。

## 运行方式

```bash
# 用项目 conda 环境（Python 3.12 + 全部运行依赖）执行
/opt/anaconda3/envs/fileTidy/bin/python -m pytest tests/unit -q

# 或只跑某一层
/opt/anaconda3/envs/fileTidy/bin/python -m pytest tests/unit/domain -q
```

## 文件约定

每个测试文件顶部都写明：**目的（测什么）、输入、期望输出**；每个测试用例
docstring 同样描述「输入 → 期望输出」。测试不允许修改生产代码，唯一允许的例外是
为测试提供构造入口，本项目当前未触发该例外。
- 测试文件命名与源码保持一致（`snake_case.py`），类/方法命名遵循 Google
  Python Style Guide；文件首行为统一的 AI 生成标记，便于 Todo Tree 审查。

## 组织原则

- 镜像源码目录：`tests/unit/domain/...`、`tests/unit/application/...`。
- mock 边界：凡是会碰真实硬件 / 交互输入 / 网络 / 全局日志的地方，一律注入替身。
- 真实 SQLite 与端到端流程放在 `func_test/`，本目录不依赖数据库。
