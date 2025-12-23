import os
import json
from ..utils import storage
from ..config import settings

def get_dashboard_stats():
    """
    Aggregate statistics for the dashboard.
    """
    all_json_files = storage.get_all_files("*.json")
    
    novels = {}
    chapters = []
    
    total_words = 0
    recent_activity = []
    
    # Track word count per novel
    # Structure: {novel_id: {"title": str, "words": int, "chapter_count": int}}
    novel_stats = {}
    
    # Asset stats
    total_assets = 0
    asset_types = {}

    for file_path in all_json_files:
        filename = os.path.basename(file_path)
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Check for asset file: novel_{id}_assets.json
            if filename.endswith('_assets.json') and isinstance(data, list):
                # It's an asset file
                local_count = len(data)
                total_assets += local_count
                for asset in data:
                    atype = asset.get('type', 'unknown')
                    # Only count as "Scene Picture" or "Character Portrait" if it has an image
                    # The Dashboard labels are "角色立绘" (Character Portrait) and "场景图" (Scene Picture)
                    if asset.get('img'):
                        asset_types[atype] = asset_types.get(atype, 0) + 1
                continue

            if 'chapter_num' in data:
                # It's a chapter
                chapters.append(data)
                content = data.get('content', '')
                word_len = len(content)
                total_words += word_len
                
                nid = data.get('novel_id')
                if nid:
                    if nid not in novel_stats:
                        novel_stats[nid] = {"title": f"Novel {nid}", "words": 0, "chapter_count": 0}
                    novel_stats[nid]["words"] += word_len
                    novel_stats[nid]["chapter_count"] += 1

                recent_activity.append({
                    "type": "chapter",
                    "name": f"Chapter {data.get('chapter_num')}",
                    "novel_id": nid,
                    "time": "Just now" 
                })
            elif 'id' in data and 'title' in data:
                # It's a novel
                novels[data['id']] = data
                
                nid = data['id']
                if nid not in novel_stats:
                    novel_stats[nid] = {"title": data['title'], "words": 0, "chapter_count": 0}
                else:
                    novel_stats[nid]["title"] = data['title']

                recent_activity.append({
                    "type": "novel",
                    "name": data.get('title'),
                    "id": data.get('id'),
                    "time": "Just now"
                })
        except Exception:
            continue

    storage_usage = storage.get_storage_usage()
    
    # Detailed storage breakdown
    storage_details = {
        "root_path": os.path.abspath(settings.STORAGE_PATH),
        "files": []
    }
    # List largest 10 files
    all_files_with_size = []
    for root, dirs, files in os.walk(settings.STORAGE_PATH):
        for name in files:
            fp = os.path.join(root, name)
            try:
                size = os.path.getsize(fp)
                all_files_with_size.append({"name": name, "size": size, "path": fp})
            except:
                pass
    
    # Sort by size desc
    all_files_with_size.sort(key=lambda x: x['size'], reverse=True)
    storage_details["files"] = all_files_with_size[:10]

    return {
        "total_novels": len(novels),
        "total_chapters": len(chapters),
        "total_words": total_words,
        "total_assets": total_assets,
        "asset_types": asset_types,
        "storage_usage": storage_usage,
        "recent_activity": recent_activity[-5:], # Last 5 items
        "details": {
            "novel_stats": list(novel_stats.values()),
            "storage_details": storage_details
        }
    }
