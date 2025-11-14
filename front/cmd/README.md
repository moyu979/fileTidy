# API 测试命令行工具

用于测试 device 和 volume 相关的 REST API 接口的命令行工具。

## 安装依赖

```bash
pip install requests
```

## 使用方法

### 基本语法

```bash
python front/cmd/api_test.py [--url URL] <category> <action> [参数...]
```

### 设备相关 API

#### 注册设备
```bash
python front/cmd/api_test.py device reg /dev/sda
```

#### 替换设备
```bash
python front/cmd/api_test.py device replace /dev/sdb /dev/sda
```

#### 检查设备
```bash
python front/cmd/api_test.py device check /dev/sda
```

#### 检查设备是否存在
```bash
python front/cmd/api_test.py device exists /dev/sda
```

#### 根据序列号获取设备路径
```bash
python front/cmd/api_test.py device get-path <序列号>
```

#### 根据设备路径获取序列号
```bash
python front/cmd/api_test.py device get-serial /dev/sda
```

#### 获取设备容量
```bash
python front/cmd/api_test.py device get-capacity /dev/sda
```

### 卷相关 API

#### 注册卷
```bash
python front/cmd/api_test.py volume reg /mnt/volume1
python front/cmd/api_test.py volume reg /mnt/volume1 --volume-id 12345
```

#### 检查卷是否存在
```bash
# 通过路径检查
python front/cmd/api_test.py volume exists --volume-path /mnt/volume1

# 通过名称检查
python front/cmd/api_test.py volume exists --name 12345
```

#### 获取卷路径
```bash
python front/cmd/api_test.py volume get-path /dev/sda
```

#### 获取卷信息
```bash
# 非严格模式（向上查找）
python front/cmd/api_test.py volume get /path/to/file

# 严格模式
python front/cmd/api_test.py volume get /mnt/volume1 --strict
```

#### 检查卷
```bash
python front/cmd/api_test.py volume check /mnt/volume1
```

### 指定服务器地址

默认连接到 `http://127.0.0.1:5000`，可以通过 `--url` 参数指定其他地址：

```bash
python front/cmd/api_test.py --url http://192.168.1.100:5000 device reg /dev/sda
```

### 查看帮助

```bash
# 查看主帮助
python front/cmd/api_test.py --help

# 查看设备相关帮助
python front/cmd/api_test.py device --help

# 查看卷相关帮助
python front/cmd/api_test.py volume --help
```

## 示例输出

成功时会显示 JSON 格式的响应：

```json
{
  "success": true,
  "message": "设备注册成功",
  "volume_id": 12345,
  "volume_path": "/mnt/volume1"
}
```

失败时会显示错误信息并退出。

