# LLM-Benchmark

LLM 并发性能测试工具，支持自动化压力测试和性能报告生成。

## 功能特点

- 多阶段并发测试（从低并发逐步提升到高并发）
- 自动化测试数据收集和分析
- 详细的性能指标统计和可视化报告
- 支持短文本和长文本测试场景
- 灵活的配置选项
- 生成 JSON 输出以便进一步分析或可视化

## 项目结构

```
llm-benchmark/
├── run_benchmarks.py     # 自动化测试脚本，执行多轮压测
├── llm_benchmark.py      # 核心并发测试实现
├── README.md            # 项目文档
└── assets/              # 资源文件夹
```

## 组件说明

- **run_benchmarks.py**:

  - 执行多轮自动化压力测试
  - 自动调整并发配置（1-300 并发）
  - 收集和汇总测试数据
  - 生成美观的性能报告

- **llm_benchmark.py**:
  - 实现核心并发测试逻辑
  - 管理并发请求和连接池
  - 收集详细性能指标
  - 支持流式响应测试

## 使用方法

安装依赖
```bash
pip install -r requirements.txt
```

运行全套性能测试：

```bash
python run_benchmarks.py \
    --llm_url "http://your-llm-server" \
    --api_key "your-api-key" \
    --model "your-model-name" \
    --use_long_context
```

运行单次并发测试：

```bash
python llm_benchmark.py \
    --llm_url "http://your-llm-server" \
    --api_key "your-api-key" \
    --model "your-model-name" \
    --num_requests 100 \
    --concurrency 10
```

## docker方式运行
构建镜像
```bash
docker build -t llm-benchmark .
```

如果不想构建，可直接拉取已存在的镜像
```bash
# 拉取镜像
docker pull samge/llm-benchmark

# 镜像重命名
docker tag samge/llm-benchmark llm-benchmark
```


创建输出目录 - 保存测试报告
```bash
mkdir -p $PWD/output
```

运行全套性能测试
```bash
docker run -it --rm -v $PWD/output:/app/output llm-benchmark \
python run_benchmarks.py \
  --llm_url "http://your-llm-server" \
  --api_key "your-api-key" \
  --model "your-model-name" \
  --use_long_context
```

运行单次并发测试
```bash
docker run -it --rm -v $PWD/output:/app/output llm-benchmark \
python llm_benchmark.py \
  --llm_url "http://your-llm-server" \
  --api_key "your-api-key" \
  --model "your-model-name" \
  --num_requests 100 \
  --concurrency 10
```

### 命令行参数

#### run_benchmarks.py 参数

| 参数               | 说明               | 默认值      |
| ------------------ | ------------------ | ----------- |
| --llm_url          | LLM 服务器 URL     | 必填        |
| --api_key          | API 密钥           | 选填        |
| --model            | 模型名称           | deepseek-r1 |
| --use_long_context | 使用长文本测试模式 | False       |

#### llm_benchmark.py 参数

| 参数              | 说明                | 默认值      |
| ----------------- | ------------------- | ----------- |
| --llm_url         | LLM 服务器 URL      | 必填        |
| --api_key         | API 密钥            | 选填        |
| --model           | 模型名称            | deepseek-r1 |
| --num_requests    | 总请求数            | 必填        |
| --concurrency     | 并发数              | 必填        |
| --output_tokens   | 输出 token 数限制   | 50          |
| --request_timeout | 请求超时时间(秒)    | 60          |
| --output_format   | 输出格式(json/line) | line        |

## 测试报告示例

![性能测试报告示例](./assets/image-20250220155605371.png)

## 开源许可

本项目采用 [MIT License](LICENSE) 开源协议。
