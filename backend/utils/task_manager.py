import uuid
from datetime import datetime
from typing import Dict, Any, List

class TaskManager:
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(TaskManager, cls).__new__(cls)
            cls._instance.tasks = {}
        return cls._instance

    def create_task(self, type: str, description: str = "", stages: List[str] = None) -> str:
        task_id = str(uuid.uuid4())
        self.tasks[task_id] = {
            "id": task_id,
            "type": type,
            "description": description,
            "status": "pending",
            "progress": 0,
            "step": "Initializing...",
            "stages": stages or [],
            "current_stage_index": 0,
            "result": None,
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat()
        }
        return task_id

    def update_task(self, task_id: str, status: str = None, progress: int = None, step: str = None, current_stage_index: int = None, result: Any = None):
        if task_id in self.tasks:
            task = self.tasks[task_id]
            if status: task["status"] = status
            if progress is not None: task["progress"] = progress
            if step: task["step"] = step
            if current_stage_index is not None: task["current_stage_index"] = current_stage_index
            if result: task["result"] = result
            task["updated_at"] = datetime.now().isoformat()

    def get_task(self, task_id: str) -> Dict:
        return self.tasks.get(task_id)

    def get_active_tasks(self) -> List[Dict]:
        # Return tasks that are not completed or failed, or completed recently (5 mins)
        active_tasks = []
        now = datetime.now()
        for t in self.tasks.values():
            if t["status"] in ["pending", "processing"]:
                active_tasks.append(t)
            elif t["status"] in ["completed", "failed"]:
                updated_at = datetime.fromisoformat(t["updated_at"])
                if (now - updated_at).total_seconds() < 10:
                    active_tasks.append(t)
        
        # Sort by updated_at desc
        active_tasks.sort(key=lambda x: x["updated_at"], reverse=True)
        return active_tasks

task_manager = TaskManager()
