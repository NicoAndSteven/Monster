from pydantic import BaseModel
from typing import Optional, List, Union
from enum import Enum

class GenerationMode(str, Enum):
    API = "api"
    RPA = "rpa"

class AssetType(str, Enum):
    CHARACTER = "character"
    SCENE = "scene"
    AUDIO = "audio"
    VIDEO = "video"
    IMAGE = "image"

class NovelCreate(BaseModel):
    id: Union[str, int]
    title: str
    description: Optional[str] = None

class ChapterGenerate(BaseModel):
    chapter_num: int
    prompt: Optional[str] = None
    mode: GenerationMode = GenerationMode.API
    context_window: int = 500  # Number of characters from previous chapter to include
    include_assets: bool = True # Whether to inject character/scene assets

class ChapterUpdate(BaseModel):
    content: str

class Asset(BaseModel):
    id: Union[str, int]
    type: AssetType
    name: str
    role: Optional[str] = None
    tags: List[str] = []
    duration: Optional[str] = None
    date: Optional[str] = None
    img: Optional[str] = None

class PipelineStatus(BaseModel):
    status: str
    current_stage: str
    progress: int
    task_name: str
