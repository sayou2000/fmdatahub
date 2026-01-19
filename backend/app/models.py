from sqlalchemy import Column, Integer, String, JSON, DateTime, Boolean
from sqlalchemy.sql import func
from .database import Base

class ImportedIssue(Base):
    __tablename__ = "imported_issues"

    id = Column(Integer, primary_key=True, index=True)
    
    # IDs aus OpenSpace (zur Wiedererkennung)
    openspace_id = Column(String, unique=True, index=True) 
    project_id = Column(String, index=True)
    
    # Metadaten
    title = Column(String, nullable=True)
    status = Column(String, nullable=True)
    image_url = Column(String, nullable=True) # URL zum Originalbild
    
    # Rohdaten als Backup
    raw_data = Column(JSON, nullable=True)
    
    # Status in unserem System (für später wichtig: QRmaint Sync)
    is_processed = Column(Boolean, default=False) 
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
