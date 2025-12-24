# Monster AI 小说创作工坊

Monster 是一个由 AI 驱动的创意写作平台，深度融合了基于大语言模型（LLM）的小说生成、实时可视化、智能资产管理以及多媒体合成功能，旨在为创作者提供全方位的辅助。

## 🚀 核心功能

*   **AI 小说生成**：利用先进的 LLM（通义千问 DashScope）辅助创建大纲、生成章节内容及规划剧情走向。
*   **视觉资产管理**：自动从故事中提取并管理角色、场景和关键物品，构建可视化的世界观库。
*   **实时可视化**：集成 Z-Image-Turbo，能够根据章节内容实时生成高质量插图。
*   **多媒体集成**：支持文本转语音 (TTS) 朗读及视频预览生成，让故事“动”起来。
*   **沉浸式工作台**：提供无干扰的专注写作环境，并配备实时的 AI 写作助手。
*   **数据看板**：直观展示写作进度、字数统计及资产分布情况。

## 🛠️ 技术栈

*   **前端**：Vue 3, TypeScript, Element Plus, Vite
*   **后端**：FastAPI, Python 3.8+
*   **AI 集成**：DashScope (文本生成), Z-Image-Turbo (图像生成), Edge-TTS (语音合成)
*   **数据存储**：本地 JSON 文件系统（轻量、便携、易于迁移）

## 📂 项目结构

```
monster/
├── backend/            # Python FastAPI 后端核心代码
│   ├── config/         # 配置文件 (Settings)
│   ├── models/         # Pydantic 数据模型
│   ├── services/       # 业务逻辑服务 (小说生成, 图像处理, 看板数据)
│   ├── utils/          # 工具模块 (存储管理, 任务管理)
│   └── main.py         # 应用入口文件
├── src/                # Vue 3 前端源代码
│   ├── views/          # 页面组件
│   ├── components/     # 通用 UI 组件
│   └── stores/         # Pinia 状态管理
├── storage/            # 数据持久化目录 (生成的 JSON 数据及媒体文件)
├── docs/               # 项目文档与设计资料
├── tests/              # 测试脚本
└── requirements.txt    # Python 依赖列表
```

## ⚡ 快速开始

### 前置要求

*   Python 3.8 或更高版本
*   Node.js 16 或更高版本
*   阿里云 DashScope API Key (用于文本生成服务)

### 1. 后端设置

1.  进入项目根目录。
2.  安装 Python 依赖：
    ```bash
    pip install -r requirements.txt
    ```
    *注意：如果遇到 `gradio_client` 安装时的 SSL 问题，建议使用国内镜像源或检查网络设置。*
3.  配置环境变量（可选，或直接修改 `backend/config/settings.py`）。
4.  启动后端服务器：
    ```bash
    uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
    ```

### 2. 前端设置

1.  安装 Node.js 依赖：
    ```bash
    npm install
    ```
2.  启动开发服务器：
    ```bash
    npm run dev
    ```
3.  在浏览器中访问：`http://localhost:5173`

### 🚀 一键启动（可选）

如果您已经安装了所有前后端依赖，可以直接使用以下命令同时启动前端和后端服务：

```bash
npm start
```
*注意：此命令需要您的命令行环境中能够直接运行 `uvicorn`（即已激活 Python 虚拟环境或安装在全局）。*

## 📖 文档说明

*   **设计理念**：请参阅 `docs/design_prompt.md` 查看原始的 UI/UX 设计愿景与提示词。

## 🤝 贡献指南

欢迎提交 Issue 或 Pull Request 来帮助改进这个平台。

## 📄 许可证

MIT License
