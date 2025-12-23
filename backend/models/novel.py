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
    type: Optional[str] = None # Genre/Type e.g. "Horror", "Comedy"

class ChapterGenerate(BaseModel):
    chapter_num: int
    prompt: Optional[str] = None
    mode: GenerationMode = GenerationMode.API
    context_window: int = 1000 # Increased default context
    include_assets: bool = True
    plot_choice: Optional[str] = None # User selected plot direction

class PlotChoiceRequest(BaseModel):
    chapter_num: int
    context_window: int = 1000

class OutlineGenerate(BaseModel):
    type: str

class OutlineUpdate(BaseModel):
    outline: str

class ChapterUpdate(BaseModel):
    content: Optional[str] = None
    images: Optional[List[str]] = None

class IllustrationGenerate(BaseModel):
    chapter_num: int

class Asset(BaseModel):
    id: Union[str, int]
    type: AssetType
    name: str
    role: Optional[str] = None
    tags: List[str] = []
    duration: Optional[str] = None
    date: Optional[str] = None
    img: Optional[str] = None
    details: Optional[str] = None # Wiki/Encyclopedia content

class PipelineStatus(BaseModel):
    status: str
    current_stage: str
    progress: int
    task_name: str
