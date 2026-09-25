
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
import datetime
from database import Base

class Judgment(Base):
    __tablename__ = "judgments"

    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String, index=True)
    upload_date = Column(DateTime, default=datetime.datetime.utcnow)
    
    analyses = relationship("Analysis", back_populates="judgment")

class Analysis(Base):
    __tablename__ = "analyses"

    id = Column(Integer, primary_key=True, index=True)
    judgment_id = Column(Integer, ForeignKey("judgments.id"))
    
    summary = Column(Text)
    laws = Column(Text)
    analysis_content = Column(Text)  # Combined precedent + logic
    web_research = Column(Text)
    web_sources = Column(Text)  # JSON string
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    judgment = relationship("Judgment", back_populates="analyses")
