# docs

本目录镜像主代码结构，用 Markdown 记录对应 `.py` 文件的**工作流**与**设计思路**，避免把流程细节写进代码注释。

## 约定

- 目录结构对齐项目根目录：`infra/config/single_file_config.py` → `docs/infra/config/single_file_config.md`
- 代码注释只写「这个类/方法做什么」，「怎么做 / 为什么这么设计」放到本目录
- 后续新增/修改代码时，同步维护对应的 `.md`

## 现有文档

- `infra/config/single_file_config.md` — 单文件配置通用类（热更新 + fail-fast 读取 + 占位符替换）
- `infra/config/watcher.md` — 共享 ConfigWatcher（方案 A：单线程监听）
