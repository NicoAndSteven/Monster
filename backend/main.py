from fastapi import FastAPI, HTTPException, Body
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel
from .config import settings
from .models.novel import NovelCreate, ChapterGenerate, Asset, PipelineStatus, ChapterUpdate
from .utils import storage
from .services import novel_generator, dashboard_service
from .services.rpa_doubao import doubao_rpa
import os
import json
from docx import Document
from io import BytesIO
import tempfile
import re

class ImageGenRequest(BaseModel):
    prompt: str

app = FastAPI()

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Dashboard & Pipeline ---

@app.get("/api/dashboard/stats")
async def get_dashboard_stats():
    # Get file stats
    file_stats = dashboard_service.get_dashboard_stats()
    
    # Load pipeline status from file or use default
    pipeline_data = storage.load_json("pipeline_status.json")
    if not pipeline_data:
        pipeline_data = {
            "status": "processing",
            "current_stage": "image_gen",
            "progress": 65,
            "task_name": "Chapter 5 Generation"
        }
        # Save default to initialize
        storage.save_json("pipeline_status.json", pipeline_data)
    
    # Mock Analytics Data (in a real app, this would come from DB)
    analytics = {
        "assets_count": {
            "characters": 12,
            "scenes": 45,
            "audio_files": 88
        },
        "distribution": {
            "douyin": [120, 150, 200, 180, 250, 300, 450],
            "xiaohongshu": [80, 90, 110, 105, 130, 140, 160]
        },
        "pipeline": pipeline_data
    }
    
    return {**file_stats, "analytics": analytics}

@app.post("/api/pipeline/update")
async def update_pipeline_status(status: PipelineStatus):
    storage.save_json("pipeline_status.json", status.dict())
    return {"status": "success", "data": status}

@app.post("/api/system/clean_cache")
async def clean_system_cache():
    storage.clear_cache()
    return {"status": "success", "message": "Cache cleaned"}

# --- Novels ---

@app.post("/api/novels")
async def create_novel(novel: NovelCreate):
    storage.save_json(f"novel_{novel.id}.json", novel.dict())
    return {"status": "success", "novel": novel}

@app.get("/api/novels")
async def list_novels():
    files = storage.get_all_files("novel_*.json")
    novels = []
    for f in files:
        if "chapter" not in f: # Exclude chapters
            data = storage.load_json(os.path.basename(f))
            if data and 'title' in data:
                novels.append(data)
    return novels

@app.delete("/api/novels/{id}")
async def delete_novel(id: str):
    # Delete main novel file
    if not storage.delete_file(f"novel_{id}.json"):
        raise HTTPException(status_code=404, detail="Novel not found")
    
    # Delete all chapters
    chapter_files = storage.get_all_files(f"novel_{id}_chapter_*.json")
    for f in chapter_files:
        storage.delete_file(os.path.basename(f))
        
    return {"status": "success", "message": "Novel deleted"}

@app.get("/api/novels/{id}/chapters")
async def list_chapters(id: str):
    files = storage.get_all_files(f"novel_{id}_chapter_*.json")
    chapters = []
    for f in files:
        data = storage.load_json(os.path.basename(f))
        if data:
            chapters.append({
                "id": data.get("chapter_num"),
                "title": f"Chapter {data.get('chapter_num')}", # Simple title for now
                "chapter_num": data.get("chapter_num")
            })
    # Sort by chapter number
    chapters.sort(key=lambda x: x["chapter_num"])
    return chapters

@app.get("/api/novels/{id}/chapters/{chapter_num}")
async def get_chapter(id: str, chapter_num: int):
    data = storage.load_json(f"novel_{id}_chapter_{chapter_num}.json")
    if not data:
        # Return empty template if not exists but novel exists? 
        # Or 404? Let's return empty structure to be safe for frontend
        return {
            "novel_id": id,
            "chapter_num": chapter_num,
            "content": ""
        }
    return data

@app.put("/api/novels/{id}/chapters/{chapter_num}")
async def update_chapter(id: str, chapter_num: int, update: ChapterUpdate):
    filename = f"novel_{id}_chapter_{chapter_num}.json"
    data = storage.load_json(filename)
    if not data:
        data = {
            "novel_id": id,
            "chapter_num": chapter_num,
            "content": "",
            "mode": "manual"
        }
    
    data["content"] = update.content
    storage.save_json(filename, data)
    return {"status": "success", "chapter": data}

@app.delete("/api/novels/{id}/chapters/{chapter_num}")
async def delete_chapter(id: str, chapter_num: int):
    filename = f"novel_{id}_chapter_{chapter_num}.json"
    if not storage.delete_file(filename):
        raise HTTPException(status_code=404, detail="Chapter not found")
    return {"status": "success", "message": "Chapter deleted"}

@app.post("/api/novels/{id}/generate")
async def generate_chapter(id: str, chapter: ChapterGenerate):
    # Check if novel exists
    novel_data = storage.load_json(f"novel_{id}.json")
    if not novel_data:
        raise HTTPException(status_code=404, detail="Novel not found")
    
    # 1. Build Context: Assets
    context_parts = []
    
    if chapter.include_assets:
        assets = storage.load_json(f"novel_{id}_assets.json")
        if assets:
            # Filter assets? For now, include all characters and scenes
            # Or maybe just names and roles to save tokens
            relevant_assets = [
                f"{a.get('type').upper()}: {a.get('name')} - {a.get('role') or 'No description'}"
                for a in assets if a.get('type') in ['character', 'scene']
            ]
            if relevant_assets:
                context_parts.append("【相关设定】\n" + "\n".join(relevant_assets))
    
    # 2. Build Context: Previous Chapter
    if chapter.chapter_num > 1:
        prev_chapter_num = chapter.chapter_num - 1
        prev_chapter = storage.load_json(f"novel_{id}_chapter_{prev_chapter_num}.json")
        if prev_chapter and prev_chapter.get("content"):
            content_preview = prev_chapter.get("content")[-chapter.context_window:]
            context_parts.append(f"【前情提要（上一章结尾）】\n...{content_preview}")
            
    full_context = "\n\n".join(context_parts)
    
    # Generate content
    content = novel_generator.generate_chapter_text(
        chapter.prompt or f"Chapter {chapter.chapter_num}",
        mode=chapter.mode,
        context=full_context
    )
    
    # Save chapter
    chapter_data = {
        "novel_id": id,
        "chapter_num": chapter.chapter_num,
        "content": content,
        "mode": chapter.mode
    }
    storage.save_json(f"novel_{id}_chapter_{chapter.chapter_num}.json", chapter_data)
    
    return {"status": "success", "chapter": chapter_data}

@app.get("/api/novels/{id}/export")
async def export_novel(id: str, format: str = "docx"):
    # 1. Load Novel Info
    novel_data = storage.load_json(f"novel_{id}.json")
    if not novel_data:
        raise HTTPException(status_code=404, detail="Novel not found")
        
    # 2. Load All Chapters
    files = storage.get_all_files(f"novel_{id}_chapter_*.json")
    chapters = []
    for f in files:
        data = storage.load_json(os.path.basename(f))
        if data:
            chapters.append(data)
    
    # Sort chapters by number
    chapters.sort(key=lambda x: x.get("chapter_num", 0))

    if format == "txt":
        content_lines = []
        content_lines.append(novel_data.get("title", "Untitled Novel"))
        content_lines.append(novel_data.get("description", ""))
        content_lines.append("\n" + "="*20 + "\n")
        
        for chapter in chapters:
            chapter_num = chapter.get("chapter_num")
            content = chapter.get("content", "")
            
            # Clean HTML
            clean_content = re.sub(r'</p>', '\n', content)
            clean_content = re.sub(r'<[^>]+>', '', clean_content)
            
            content_lines.append(f"Chapter {chapter_num}")
            content_lines.append(clean_content)
            content_lines.append("\n" + "-"*10 + "\n")
            
        full_text = "\n".join(content_lines)
        
        # Save to temp file
        fd, path = tempfile.mkstemp(suffix=".txt")
        try:
            with os.fdopen(fd, 'w', encoding='utf-8') as tmp:
                tmp.write(full_text)
                
            return FileResponse(
                path,
                filename=f"{novel_data.get('title', 'novel')}.txt",
                media_type="text/plain"
            )
        except Exception as e:
            os.unlink(path)
            raise HTTPException(status_code=500, detail=str(e))

    else: # docx
        # 3. Create Word Document
        doc = Document()
        
        # Title Page
        doc.add_heading(novel_data.get("title", "Untitled Novel"), 0)
        if novel_data.get("description"):
            doc.add_paragraph(novel_data.get("description"))
        doc.add_page_break()
        
        # Chapters
        for chapter in chapters:
            chapter_num = chapter.get("chapter_num")
            content = chapter.get("content", "")
            
            # Clean HTML tags if content is HTML (from Tiptap)
            # Simple regex to strip tags, better to use BeautifulSoup but regex is faster for now
            # Replace <p> with newline, strip others
            clean_content = re.sub(r'</p>', '\n', content)
            clean_content = re.sub(r'<[^>]+>', '', clean_content)
            
            doc.add_heading(f"Chapter {chapter_num}", level=1)
            doc.add_paragraph(clean_content)
            doc.add_page_break()
            
        # 4. Save to temporary file
        # We need to save to a temp file because FileResponse needs a path
        # Or we can use StreamingResponse with BytesIO, but FileResponse is easier for cleanup if we use tempfile
        
        # Create temp file
        fd, path = tempfile.mkstemp(suffix=".docx")
        try:
            with os.fdopen(fd, 'wb') as tmp:
                doc.save(tmp)
                
            return FileResponse(
                path, 
                filename=f"{novel_data.get('title', 'novel')}.docx",
                media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
            )
        except Exception as e:
            os.unlink(path) # Clean up on error
            raise HTTPException(status_code=500, detail=str(e))

# --- Assets (Library) ---

@app.get("/api/novels/{novel_id}/assets")
async def list_assets(novel_id: str):
    assets = storage.load_json(f"novel_{novel_id}_assets.json")
    if not assets:
        assets = [] 
    return assets

@app.post("/api/novels/{novel_id}/assets")
async def create_asset(novel_id: str, asset: Asset):
    filename = f"novel_{novel_id}_assets.json"
    assets = storage.load_json(filename) or []
    
    # Ensure ID is unique or generate one if not provided (though frontend usually provides it)
    # Simple check if exists
    for a in assets:
        if str(a.get("id")) == str(asset.id):
            raise HTTPException(status_code=400, detail="Asset ID already exists")
            
    assets.append(asset.dict())
    storage.save_json(filename, assets)
    return {"status": "success", "asset": asset}

@app.put("/api/novels/{novel_id}/assets/{asset_id}")
async def update_asset(novel_id: str, asset_id: str, asset_update: Asset):
    filename = f"novel_{novel_id}_assets.json"
    assets = storage.load_json(filename) or []
    
    for i, asset in enumerate(assets):
        if str(asset.get("id")) == str(asset_id):
            assets[i] = asset_update.dict()
            storage.save_json(filename, assets)
            return {"status": "success", "asset": asset_update}
            
    raise HTTPException(status_code=404, detail="Asset not found")

@app.delete("/api/novels/{novel_id}/assets/{asset_id}")
async def delete_asset(novel_id: str, asset_id: str):
    filename = f"novel_{novel_id}_assets.json"
    assets = storage.load_json(filename) or []
    
    initial_len = len(assets)
    assets = [a for a in assets if str(a.get("id")) != str(asset_id)]
    
    if len(assets) == initial_len:
        raise HTTPException(status_code=404, detail="Asset not found")
        
    storage.save_json(filename, assets)
    return {"status": "success", "message": "Asset deleted"}

@app.post("/api/generate/image/rpa")
async def generate_image_rpa(request: ImageGenRequest):
    result = await doubao_rpa.generate_image(request.prompt)
    if "error" in result:
        raise HTTPException(status_code=500, detail=result["error"])
    return result

@app.get("/api/media/{chapter_id}/video")
async def get_video(chapter_id: str):
    return {"url": f"https://cdn.example.com/videos/{chapter_id}.mp4"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
