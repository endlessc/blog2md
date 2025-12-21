# Blog2MD

[English](README.md) | **中文文档**

**Blog2MD** 是一个智能工具，旨在将网页文章（来自微信公众号、今日头条、掘金等平台）转换为干净的本地 Markdown 文件。

与仅依赖正则表达式或简单 HTML 解析的传统转换器不同，Blog2MD 利用 **大型语言模型 (LLMs)**（如 OpenAI GPT-4, DeepSeek, Qwen 等）来：

1.  智能地将内容格式化为高质量的 Markdown。
2.  根据内容自动对文章进行分类。
3.  将图片下载到本地进行归档，实现真正的离线访问。

它配备了一个现代化的 **Web 界面**，便于管理、监控和阅读。

![Web UI Screenshot](https://via.placeholder.com/800x450?text=Blog2MD+Web+Interface) *(如果有实际截图请替换)*

## ✨ 功能特性

- **🤖 LLM 驱动转换**: 使用 AI 去除杂乱内容并完美格式化文本。
- **📂 自动分类**: 自动将文章整理到 "Technology" (科技), "Finance" (财经), "News" (新闻) 等文件夹中。
- **🖼️ 图片归档**: 将所有图片下载到本地 `assets` 文件夹并更新链接，确保 Markdown 文件完全离线可用。
- **🌍 多平台支持**:
    - **微信公众号**
    - **今日头条** - 支持移动端/短链接及重定向
    - **掘金**
    - **通用模式** (针对其他网站的兜底支持)
- **🖥️ 现代 Web UI**:
    - 基于 **FastAPI** & **Tailwind CSS** 构建。
    - 支持 **深色模式**。
    - 通过 WebSocket **实时监控** 转换任务。
    - **PDF 导出**: 将归档的 Markdown 文章转换为 PDF，并支持正确字体显示。
    - **管理功能**: 直接在浏览器中查看、阅读和删除分类或文章。

## 🚀 快速开始

### 前置要求

- Python 3.8 或更高版本。
- 一个 LLM 服务商的 API Key (OpenAI, DeepSeek, DashScope/Qwen 等)。

### 安装

1.  **克隆仓库**:
    ```bash
    git clone https://github.com/your-username/blog2md.git
    cd blog2md
    ```

2.  **安装依赖**:
    ```bash
    pip install -r requirements.txt
    ```

3.  **配置环境**:
    复制示例环境变量文件并进行编辑:
    ```bash
    cp .env.example .env
    ```
    
    打开 `.env` 并设置您的 LLM 服务商和 API Key。示例:
    ```ini
    # 选项: openai, deepseek, qwen, kimi, doubao, custom
    LLM_PROVIDER=openai

    # OpenAI 配置
    OPENAI_API_KEY=sk-your-key-here
    OPENAI_MODEL=gpt-4o-mini
    
    # 或者配置 DeepSeek
    # LLM_PROVIDER=deepseek
    # DEEPSEEK_API_KEY=sk-your-deepseek-key
    # DEEPSEEK_MODEL=deepseek-chat
    ```

### Docker 部署

1.  **使用 Docker Compose 构建并运行** (推荐):
    ```bash
    docker-compose up -d
    ```

2.  **访问应用**:
    http://localhost:8000

3.  **自定义配置**:
    - **端口**: 通过设置 `PORT` 环境变量来更改端口。
      ```bash
      PORT=9000 docker-compose up -d
      ```
      然后访问 http://localhost:9000
    - **输出映射**: `output` 目录会自动映射到您项目根目录下的 `./output` 文件夹。
    - **字体**: 如果您需要自定义字体，可以在 `docker-compose.yml` 中取消注释 fonts 卷映射。

## 📖 使用说明

### Web 界面 (推荐)

启动 Web 服务器:
```bash
python server.py
```

打开浏览器并访问:
**http://localhost:8000**

- 点击 **"Fetch URL"** 添加新文章。
- 在主页查看您的知识库。
- 在 "Monitor" 标签页监控后台任务。

### 📱 手机一键转发抓取 (Mobile Quick Capture)

只要您的手机和电脑连接的是同一个 Wi-Fi，您就可以通过手机轻松将文章推送到 Blog2MD 进行抓取。

> **注意**: 请将以下示例中的 `192.168.1.82` 替换为您电脑实际的局域网 IP 地址。

#### 方案一：iOS 快捷指令 (推荐 iPhone 用户)

1.  打开 iPhone 上的 **“快捷指令” (Shortcuts)** App。
2.  点击右上角 **“+”** 新建快捷指令。
3.  点击 **“添加操作”** ，搜索并添加 **“获取 URL 的内容” (Get Contents of URL)**。
    *   URL 设置为: `http://192.168.1.82:8000/api/quick_add?url=`
    *   在等号后面，点击键盘上方的变量区域，选择 **“快捷指令输入” (Shortcut Input)**。
4.  点击底部的 **“i”** 图标（或顶部的名称），开启 **“在共享表单中显示” (Show in Share Sheet)**。
5.  回到编辑器，点击顶部的 **“接收” (Receive)** 设置:
    *   设置为接收 **“Safari 网页” (Safari web pages)** 或 **“URL”**。
6.  给快捷指令起个名字，例如 **“推送到 Blog2MD”**。

**使用方法**: 在 Safari 或其他 App 中，点击分享按钮 -> 选择 “推送到 Blog2MD”。

#### 方案二：Android (HTTP Shortcuts)

1.  安装 **HTTP Shortcuts** App。
2.  新建一个 Shortcut。
3.  **Basic Settings (基本设置)**:
    *   Name: 推送到 Blog2MD
    *   URL: `http://192.168.1.82:8000/api/quick_add?url={share_text}`
4.  **Request Method (请求方法)**: GET
5.  勾选 **"Show in Share Sheet" (在分享菜单中显示)**。

#### 方案三：浏览器书签 (通用)

在手机浏览器中添加一个书签，将地址栏内容设为以下 JavaScript 代码（书签脚本）:

```javascript
javascript:(function(){window.location.href='http://192.168.1.82:8000/api/quick_add?url='+encodeURIComponent(window.location.href);})();
```

**使用方法**: 在浏览文章页面时 -> 点击地址栏 -> 搜索或选择这个书签。

### 命令行界面 (CLI)

您也可以直接在终端使用该工具:

```bash
python main.py https://mp.weixin.qq.com/s/some-article-url
```

或者直接运行 `python main.py` 并在提示时粘贴 URL。

## 📂 输出结构

所有转换后的文章都保存在 `output` 目录中:

```
output/
├── Technology/
│   ├── Understanding_LLMs/
│   │   ├── index.md
│   │   └── assets/
│   │       ├── image1.jpg
│   │       └── image2.png
├── Finance/
│   ├── Market_Trends_2025/
│   │   ├── index.md
│   │   └── assets/
│       ...
```

## 🛠️ 技术栈

- **后端**: Python, FastAPI, Uvicorn
- **前端**: HTML5, Jinja2 Templates, Tailwind CSS, JavaScript
- **AI/LLM**: LangChain (集成 OpenAI, DeepSeek, DashScope 等)
- **爬虫**: Requests, BeautifulSoup4
- **工具**: Markdown, xhtml2pdf

## 📝 许可证

[MIT License](LICENSE)
