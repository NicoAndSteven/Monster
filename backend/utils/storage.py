import os
import json
import glob
from fastapi import HTTPException
from ..config import settings

def save_json(filename: str, data: dict):
    path = os.path.join(settings.STORAGE_PATH, filename)
    try:
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save file: {str(e)}")

def load_json(filename: str) -> dict:
    path = os.path.join(settings.STORAGE_PATH, filename)
    if not os.path.exists(path):
        return None
    try:
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to load file: {str(e)}")

from typing import List

def get_all_files(pattern: str = "*.json") -> List[str]:
    """Get all file paths matching a pattern in storage"""
    search_path = os.path.join(settings.STORAGE_PATH, pattern)
    return glob.glob(search_path)

def get_storage_usage() -> dict:
    """Calculate total storage usage in bytes"""
    total_size = 0
    file_count = 0
    try:
        for dirpath, dirnames, filenames in os.walk(settings.STORAGE_PATH):
            for f in filenames:
                fp = os.path.join(dirpath, f)
                total_size += os.path.getsize(fp)
                file_count += 1
        return {
            "total_size_bytes": total_size,
            "file_count": file_count
        }
    except Exception as e:
        print(f"Error calculating storage: {e}")
        return {"total_size_bytes": 0, "file_count": 0}

def clear_cache():
    """Clear temporary files (implementation: remove all json for demo, or specific temp pattern)"""
    # For MVP, we won't delete actual data, maybe just return success
    # In real app, this might clear /temp or old logs
    pass

def delete_file(filename: str):
    path = os.path.join(settings.STORAGE_PATH, filename)
    if os.path.exists(path):
        try:
            os.remove(path)
            return True
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to delete file: {str(e)}")
    return False
