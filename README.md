# 实训报告智能批改系统

基于Trae AI编程工具开发的实训报告智能批改系统，支持docx和pdf格式的报告自动批改。

## 功能特点

- 📄 支持docx和pdf格式的文档解析
- 🖼️ 图片数量统计和质量评估
- 📊 参考答案比对和差异分析
- 🎯 自动评分（百分制）
- 💬 个性化评语生成
- 📝 HTML/JSON格式报告输出
- 📦 批量处理支持

## 环境要求

- Python 3.8+
- 依赖库见 requirements.txt

## 安装步骤

```bash
# 安装依赖
pip install -r requirements.txt
```

## 运行方式

### 方式一：命令行运行

```bash
streamlit run app.py
```

### 方式二：开发模式

```bash
streamlit run app.py --server.port 8501
```

## 使用说明

1. 启动应用后，进入"单文件批改"或"批量批改"模式
2. 上传参考答案文件（docx或pdf格式）
3. 上传待批改报告或选择待批改文件夹
4. 可选：设置自定义评分规则
5. 点击"开始批改"按钮
6. 查看批改结果并下载报告

## 配置文件说明

配置文件 `config.py` 包含以下配置项：

- `DATA_DIR`: 数据目录
- `REFERENCE_DIR`: 参考答案目录
- `SUBMISSIONS_DIR`: 待批改报告目录
- `OUTPUT_DIR`: 输出目录
- `MIN_IMAGE_WIDTH/HEIGHT`: 最小图片尺寸
- `MAX_IMAGE_WIDTH/HEIGHT`: 最大图片尺寸
- `IMAGE_COUNT_TOLERANCE`: 图片数量容差
- `SECTION_KEYWORDS`: 章节关键词配置
- `DEFAULT_SCORING_RULES`: 默认评分规则权重

## 输出格式

### HTML报告
包含完整的批改结果展示，包括：
- 基本信息
- 总分展示
- 章节评分详情
- 图片分析
- 评语
- 差异对比摘要

### JSON报告
包含结构化的批改数据，便于程序处理。

## 评分规则

默认评分权重：
- 结构完整性: 20%
- 内容准确性: 40%
- 图片质量: 20%
- 分析深度: 20%

## 项目结构

```
qimo/
├── app.py              # Streamlit Web界面
├── config.py           # 配置文件
├── document_parser.py  # 文档解析模块
├── image_processor.py  # 图片处理模块
├── scoring_engine.py   # 评分引擎
├── report_generator.py # 报告生成模块
├── requirements.txt    # 依赖列表
└── data/               # 数据目录
    ├── references/     # 参考答案
    ├── submissions/    # 待批改报告
    └── output/         # 输出报告
```

## 技术说明

- 使用 python-docx 解析docx文件
- 使用 PyPDF2 解析PDF文件
- 使用 sklearn 进行文本相似度计算
- 使用 Streamlit 构建Web界面
- 支持离线运行，无需网络连接
