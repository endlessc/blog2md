import asyncio
import os
import shutil
import urllib.parse
from contextlib import asynccontextmanager
from datetime import datetime
from io import BytesIO
from typing import List

import markdown
from dotenv import load_dotenv
from fastapi import FastAPI, Request, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse, FileResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from xhtml2pdf import pisa

from main import process_url
from task_manager import TaskManager

load_dotenv()

OUTPUT_DIR = "output"
os.makedirs(OUTPUT_DIR, exist_ok=True)
templates = Jinja2Templates(directory="templates")
templates.env.filters["quote"] = urllib.parse.quote

# --- Connection Manager for Global Notifications ---
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)

    async def broadcast(self, message: str):
        # Iterate over a copy to avoid modification during iteration issues
        for connection in list(self.active_connections):
            try:
                await connection.send_text(message)
            except Exception:
                # If sending fails, assume connection is dead and remove it
                self.disconnect(connection)

manager = ConnectionManager()
task_manager = TaskManager(concurrency=2)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup logic
    loop = asyncio.get_running_loop()
    # We pass process_url directly. The worker will handle run_in_threadpool
    await task_manager.start_workers(process_url, loop, manager.broadcast)
    yield
    # Shutdown logic can go here if needed

app = FastAPI(lifespan=lifespan)

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# --- Pydantic Models ---
class FetchRequest(BaseModel):
    url: str

class ConcurrencySettings(BaseModel):
    concurrency: int

# --- Routes ---

def generate_breadcrumbs(path):
    if not path: return []
    parts = path.strip('/').split('/')
    breadcrumbs = []
    current_path = ""
    for part in parts:
        if not part: continue
        if current_path:
            current_path += "/" + part
        else:
            current_path = part
        breadcrumbs.append({"name": part, "path": current_path})
    return breadcrumbs

@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    return await browse(request, path="")

@app.get("/browse", response_class=HTMLResponse)
@app.get("/browse/{path:path}", response_class=HTMLResponse)
async def browse(request: Request, path: str = ""):
    # Security check
    if ".." in path:
        raise HTTPException(status_code=400, detail="Invalid path")
        
    full_path = os.path.join(OUTPUT_DIR, path)
    if not os.path.exists(full_path):
        raise HTTPException(status_code=404, detail="Path not found")
    
    # If it is an article (directory with index.md), redirect to article view
    if os.path.exists(os.path.join(full_path, "index.md")):
        return RedirectResponse(url=f"/article/{path}")
        
    # List contents
    items = []
    try:
        with os.scandir(full_path) as it:
            for entry in it:
                if entry.name.startswith('.'): continue
                if entry.name == "assets": continue 
                
                is_article = False
                if entry.is_dir():
                    if os.path.exists(os.path.join(entry.path, "index.md")):
                        is_article = True
                
                if entry.is_dir():
                    rel_path = os.path.join(path, entry.name) if path else entry.name
                    items.append({
                        "name": entry.name,
                        "path": rel_path,
                        "type": "article" if is_article else "folder",
                        "timestamp": entry.stat().st_ctime,
                        "date_display": datetime.fromtimestamp(entry.stat().st_ctime).strftime('%Y-%m-%d %H:%M')
                    })
    except OSError as e:
         raise HTTPException(status_code=500, detail=str(e))
            
    # Sort: Folders first, then articles (by time desc)
    items.sort(key=lambda x: (x["type"] == "article", -x["timestamp"]))
    
    return templates.TemplateResponse("browse.html", {
        "request": request, 
        "path": path, 
        "items": items,
        "breadcrumbs": generate_breadcrumbs(path)
    })

@app.get("/article/{path:path}", response_class=HTMLResponse)
async def read_article(request: Request, path: str):
    full_path = os.path.join(OUTPUT_DIR, path)
    article_path = os.path.join(full_path, "index.md")
    
    if not os.path.exists(article_path):
         raise HTTPException(status_code=404, detail="Article not found")
    
    with open(article_path, "r", encoding="utf-8") as f:
        md_content = f.read()

    html_content = markdown.markdown(md_content, extensions=['extra', 'codehilite', 'sane_lists'])
    
    # Fix relative image paths
    encoded_path = "/".join([urllib.parse.quote(p) for p in path.split('/')])
    base_asset_url = f"/files/{encoded_path}/assets/"
    
    html_content = html_content.replace('src="assets/', f'src="{base_asset_url}')
    html_content = html_content.replace("src='assets/", f"src='{base_asset_url}")
    html_content = html_content.replace('href="assets/', f'href="{base_asset_url}')
    html_content = html_content.replace("href='assets/", f"href='{base_asset_url}")
    
    title = os.path.basename(path)
    category_path = os.path.dirname(path)
    
    # Generate breadcrumbs excluding the current article (title)
    breadcrumbs = generate_breadcrumbs(category_path)
    
    return templates.TemplateResponse("article.html", {
        "request": request, 
        "category": category_path, 
        "title": title, 
        "content": html_content,
        "path": path,
        "breadcrumbs": breadcrumbs
    })

@app.get("/files/{path:path}")
async def serve_file(path: str):
    full_path = os.path.join(OUTPUT_DIR, path)
    if not os.path.exists(full_path):
        raise HTTPException(status_code=404, detail="File not found")
    return FileResponse(full_path)

@app.get("/download/md/{path:path}")
async def download_md(path: str):
    article_path = os.path.join(OUTPUT_DIR, path, "index.md")
    
    if not os.path.exists(article_path):
        raise HTTPException(status_code=404, detail="Article not found")
    
    title = os.path.basename(path)
    return FileResponse(article_path, filename=f"{title}.md", media_type="text/markdown")

@app.get("/download/pdf/{path:path}")
async def download_pdf(path: str):
    article_path = os.path.join(OUTPUT_DIR, path, "index.md")
    
    if not os.path.exists(article_path):
        raise HTTPException(status_code=404, detail="Article not found")

    with open(article_path, "r", encoding="utf-8") as f:
        md_content = f.read()
    
    # Convert Markdown to HTML
    html_content = markdown.markdown(md_content, extensions=['extra', 'codehilite', 'sane_lists'])
    
    # Base path for resolving relative images
    base_path = os.path.join(os.getcwd(), OUTPUT_DIR, path)
    
    # Define a callback for resolving local files
    def link_callback(uri, rel):
        # Handle assets/ prefix in Markdown images
        if uri.startswith("assets/"):
             # Convert assets/image.jpg -> /full/path/to/assets/image.jpg
             full_path = os.path.join(base_path, uri)
             return full_path
        return uri

    # Inject CSS
    css = """
    <style>
        @page {
            size: A4;
            margin: 2cm;
        }
        body {
            font-family: "Helvetica Neue", Helvetica, Arial, sans-serif;
            line-height: 1.6;
            color: #333;
        }
        h1, h2, h3, h4, h5, h6 {
            color: #2c3e50;
            margin-top: 1.5em;
            margin-bottom: 0.5em;
        }
        h1 { font-size: 24pt; border-bottom: 2px solid #eee; padding-bottom: 10px; }
        h2 { font-size: 18pt; border-bottom: 1px solid #eee; padding-bottom: 5px; }
        img {
            max-width: 100%;
            height: auto;
            margin: 20px 0;
        }
        code, pre {
            font-family: "Courier New", Courier, monospace;
            background-color: #f5f7f9;
            padding: 2px 4px;
            border-radius: 4px;
        }
        pre {
            padding: 10px;
            overflow-x: auto;
            border: 1px solid #e1e4e8;
            white-space: pre-wrap; /* Wrap long lines */
        }
        /* Pygments Syntax Highlighting */
        .codehilite {
            background: #f8f8f8;
            border: 1px solid #e1e4e8;
            border-radius: 4px;
            padding: 10px;
            margin: 10px 0;
            white-space: pre-wrap; /* Ensure wrapping in PDF */
        }
        .codehilite pre {
            margin: 0;
            padding: 0;
            border: none;
            background: none;
            white-space: pre-wrap;
        }
        blockquote {
            border-left: 4px solid #dfe2e5;
            color: #6a737d;
            padding-left: 15px;
            margin: 0;
        }
        table {
            border-collapse: collapse;
            width: 100%;
            margin: 20px 0;
        }
        th, td {
            border: 1px solid #dfe2e5;
            padding: 6px 13px;
        }
        th {
            background-color: #f6f8fa;
        }
        a { color: #0066cc; text-decoration: none; }
    </style>
    """

    html_template = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        {css}
    </head>
    <body>
        <h1>{os.path.basename(path)}</h1>
        <div class="content">
            {html_content}
        </div>
        <div id="footer_content" style="text-align: center; color: #888; font-size: 9pt;">
            Generated by Blog2MD - Page <pdf:pagenumber> of <pdf:pagecount>
        </div>
    </body>
    </html>
    """

    result_file = BytesIO()
    pisa_status = pisa.CreatePDF(
        html_template,
        dest=result_file,
        link_callback=link_callback
    )

    if pisa_status.err:
        raise HTTPException(status_code=500, detail="PDF generation failed")

    result_file.seek(0)
    title = os.path.basename(path)
    from fastapi.responses import Response
    from urllib.parse import quote
    
    return Response(
        content=result_file.getvalue(),
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename={quote(title)}.pdf"}
    )

# --- WebSocket & Background Task Logic ---

@app.websocket("/ws/notify")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            # Keep connection alive
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket)

# Note: run_fetch_task is no longer used directly by API, but logic is inside TaskManager worker

@app.get("/monitor", response_class=HTMLResponse)
async def monitor_page(request: Request):
    return templates.TemplateResponse("monitor.html", {"request": request})

@app.get("/api/tasks")
async def get_tasks():
    # Return list of tasks sorted by creation time (newest first)
    sorted_tasks = sorted(task_manager.tasks.values(), key=lambda x: x.created_at, reverse=True)
    return sorted_tasks

@app.post("/api/settings/concurrency")
async def set_concurrency(settings: ConcurrencySettings):
    current = task_manager.concurrency
    new = settings.concurrency
    
    if new < 1 or new > 10:
        raise HTTPException(status_code=400, detail="Concurrency must be between 1 and 10")
    
    task_manager.concurrency = new
    
    # If increasing, start new workers
    if new > current:
        loop = asyncio.get_running_loop()
        diff = new - current
        for _ in range(diff):
            worker = asyncio.create_task(task_manager._worker(process_url, loop, manager.broadcast))
            task_manager.workers.append(worker)
            
    # Decreasing is harder without killing tasks, so we just update the limit for future restarts or 
    # implement a graceful shutdown mechanism later. 
    # For now, we only support dynamic increase effectively, or rely on restart for decrease.
    
    return {"status": "updated", "concurrency": new}

@app.post("/api/fetch")
async def fetch_article_endpoint(request: FetchRequest):
    task_id = task_manager.add_task(request.url)
    return {"status": "queued", "task_id": task_id, "message": "Task added to queue"}

@app.delete("/api/delete/{path:path}")
async def delete_item(path: str):
    full_path = os.path.join(OUTPUT_DIR, path)
    if not os.path.exists(full_path):
        raise HTTPException(status_code=404, detail="Item not found")
    
    try:
        if os.path.isdir(full_path):
            shutil.rmtree(full_path)
        else:
            os.remove(full_path)
        return {"status": "success", "message": f"Deleted {path}"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete: {str(e)}")

@app.get("/api/quick_add")
async def quick_add_endpoint(url: str):
    """
    Convenience endpoint for GET-based triggering (e.g., from simple Shortcuts or browser bars).
    """
    if not url:
        raise HTTPException(status_code=400, detail="URL parameter is required")
    
    task_id = task_manager.add_task(url)
    # Return a simple HTML page that closes itself or shows success
    return HTMLResponse(content=f"""
    <html>
        <head>
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Task Added</title>
            <style>
                body {{ font-family: -apple-system, sans-serif; display: flex; justify-content: center; align-items: center; height: 100vh; margin: 0; background: #f0fdf4; color: #166534; }}
                .card {{ background: white; padding: 20px; border-radius: 12px; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.1); text-align: center; }}
                h1 {{ font-size: 1.25rem; margin-bottom: 0.5rem; }}
                p {{ font-size: 0.875rem; color: #6b7280; }}
            </style>
        </head>
        <body>
            <div class="card">
                <svg style="width: 48px; height: 48px; margin-bottom: 1rem; color: #16a34a;" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"></path></svg>
                <h1>已添加到队列</h1>
                <p>Task ID: {task_id}</p>
                <script>setTimeout(() => window.close(), 2000);</script>
            </div>
        </body>
    </html>
    """)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("server:app", host="0.0.0.0", port=8000, reload=True)
