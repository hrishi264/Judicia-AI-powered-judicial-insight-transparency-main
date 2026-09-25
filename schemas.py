
from pydantic import BaseModel
from typing import List, Optional, Any
from datetime import datetime

class AnalysisBase(BaseModel):
    summary: str
    laws: str
    analysis_content: str
    web_research: str
    web_sources: Any  # JSON parsed from DB

class AnalysisCreate(AnalysisBase):
    pass

class Analysis(AnalysisBase):
    id: int
    judgment_id: int
    created_at: datetime

    model_config = {"from_attributes": True}

class JudgmentBase(BaseModel):
    filename: str

class JudgmentCreate(JudgmentBase):
    pass

class Judgment(JudgmentBase):
    id: int
    upload_date: datetime
    analyses: List[Analysis] = []

    model_config = {"from_attributes": True}

class JudgmentHistory(BaseModel):
    id: int
    filename: str
    upload_date: datetime
    summary_snippet: Optional[str] = None
