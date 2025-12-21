# Blog2MD

**English** | [中文文档](README_zh.md)

**Blog2MD** is an intelligent tool designed to convert web articles (from platforms like WeChat, Toutiao, Juejin, and more) into clean, local Markdown files. 

Unlike traditional converters that rely solely on regex or simple HTML parsing, Blog2MD leverages **Large Language Models (LLMs)** (such as OpenAI GPT-4, DeepSeek, Qwen) to:
1.  Intelligently format the content into high-quality Markdown.
2.  Automatically categorize articles based on their content.
3.  Preserve and download images locally for offline access.

It comes with a modern **Web Interface** for easy management, monitoring, and reading.

![Web UI Screenshot](https://via.placeholder.com/800x450?text=Blog2MD+Web+Interface) *(Replace with actual screenshot if available)*

## ✨ Features

- **🤖 LLM-Powered Conversion**: Uses AI to strip clutter and format text perfectly.
- **📂 Auto-Categorization**: Automatically organizes articles into folders like "Technology", "Finance", "News", etc.
- **🖼️ Image Archiving**: Downloads all images to a local `assets` folder and updates links, ensuring your markdown is truly offline-ready.
- **🌍 Multi-Platform Support**:
    - **WeChat Official Accounts** (微信公众号)
    - **Toutiao** (今日头条) - Supports mobile/short links & redirects
    - **Juejin** (掘金)
    - **Generic** (Fallbacks for other websites)
- **🖥️ Modern Web UI**:
    - Built with **FastAPI** & **Tailwind CSS**.
    - **Dark Mode** support.
    - **Real-time Monitoring** of conversion tasks via WebSockets.
    - **PDF Export**: Convert your archived Markdown articles to PDF with proper font support.
    - **Management**: View, read, and delete categories or articles directly from the browser.

## 🚀 Getting Started

### Prerequisites

- Python 3.8 or higher.
- An API Key for an LLM provider (OpenAI, DeepSeek, DashScope/Qwen, etc.).

### Installation

1.  **Clone the repository**:
    ```bash
    git clone https://github.com/your-username/blog2md.git
    cd blog2md
    ```

2.  **Install dependencies**:
    ```bash
    pip install -r requirements.txt
    ```

3.  **Configure Environment**:
    Copy the example environment file and edit it:
    ```bash
    cp .env.example .env
    ```
    
    Open `.env` and set your LLM provider and API keys. Example:
    ```ini
    # Options: openai, deepseek, qwen, kimi, doubao, custom
    LLM_PROVIDER=openai

    # OpenAI Configuration
    OPENAI_API_KEY=sk-your-key-here
    OPENAI_MODEL=gpt-4o-mini
    
    # Or for DeepSeek
    # LLM_PROVIDER=deepseek
    # DEEPSEEK_API_KEY=sk-your-deepseek-key
    # DEEPSEEK_MODEL=deepseek-chat
    ```

### Docker Deployment

1.  **Build and Run with Docker Compose** (Recommended):
    ```bash
    docker-compose up -d
    ```

2.  **Access the application**:
    http://localhost:8000

3.  **Custom Configuration**:
    - **Port**: Change the port by setting the `PORT` environment variable.
      ```bash
      PORT=9000 docker-compose up -d
      ```
      Then access at http://localhost:9000
    - **Output Mapping**: The `output` directory is automatically mapped to `./output` in your project root.
    - **Fonts**: If you need custom fonts, you can uncomment the fonts volume mapping in `docker-compose.yml`.

## 📖 Usage

### Web Interface (Recommended)

Start the web server:
```bash
python server.py
```

Open your browser and navigate to:
**http://localhost:8000**

- Click **"Fetch URL"** to add a new article.
- View your knowledge base in the home page.
- Monitor background tasks in the "Monitor" tab.

### 📱 Mobile Quick Capture

Easily send articles from your phone to Blog2MD while on the same Wi-Fi.

> **Note**: Replace `192.168.1.82` in the examples below with your computer's actual LAN IP address.

#### Method 1: iOS Shortcuts (Recommended)

1.  Open the **Shortcuts** app on your iPhone.
2.  Tap **"+"** to create a new shortcut.
3.  Add action **"Get Contents of URL"**.
    *   URL: `http://192.168.1.82:8000/api/quick_add?url=`
    *   After the `=`, select **"Shortcut Input"** from the variable bar.
4.  Tap the **"i"** icon (or shortcut name) and enable **"Show in Share Sheet"**.
5.  Tap **"Receive"** settings at the top:
    *   Set to receive **"Safari web pages"** or **"URLs"**.
6.  Name it **"Save to Blog2MD"**.

**Usage**: In Safari/Apps, tap Share -> "Save to Blog2MD".

#### Method 2: Android (HTTP Shortcuts)

1.  Install **HTTP Shortcuts** app.
2.  Create a new shortcut.
3.  **Basic Settings**:
    *   Name: Save to Blog2MD
    *   URL: `http://192.168.1.82:8000/api/quick_add?url={share_text}`
4.  **Request Method**: GET
5.  Enable **"Show in Share Sheet"**.

#### Method 3: Browser Bookmarklet

Create a bookmark in your mobile browser with the following URL (Address):

```javascript
javascript:(function(){window.location.href='http://192.168.1.82:8000/api/quick_add?url='+encodeURIComponent(window.location.href);})();
```

**Usage**: While viewing an article, tap the address bar and select this bookmark.

### Command Line Interface (CLI)

You can also use the tool directly from the terminal:

```bash
python main.py https://mp.weixin.qq.com/s/some-article-url
```

Or simply run `python main.py` and paste the URL when prompted.

## 📂 Output Structure

All converted articles are saved in the `output` directory:

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

## 🛠️ Tech Stack

- **Backend**: Python, FastAPI, Uvicorn
- **Frontend**: HTML5, Jinja2 Templates, Tailwind CSS, JavaScript
- **AI/LLM**: LangChain (integrating OpenAI, DeepSeek, DashScope, etc.)
- **Scraping**: Requests, BeautifulSoup4
- **Utilities**: Markdown, xhtml2pdf

## 📝 License

[MIT License](LICENSE)
