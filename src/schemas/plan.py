from typing import List, Dict, Any, Optional
from pydantic import BaseModel

class ResearchTaskSpec(BaseModel):
    id: str
    name: str
    description: str
    crew: str
    inputs: Dict[str, Any]
    depends_on: List[str] = []
    parallelizable: bool = False

class ResearchPlan(BaseModel):
    tasks: List[ResearchTaskSpec]
