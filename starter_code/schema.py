from pydantic import BaseModel, Field
from typing import Any, Dict, Optional
from datetime import datetime

# ==========================================
# ROLE 1: LEAD DATA ARCHITECT
# ==========================================
# Your task is to define the Unified Schema for all sources.
# This is v1. Note: A breaking change is coming at 11:00 AM!

class UnifiedDocument(BaseModel):
    """Canonical v1 document shape for all ingestion sources."""

    document_id: str
    content: str
    source_type: str  # e.g., 'PDF', 'Video', 'HTML', 'CSV', 'Code'
    author: Optional[str] = "Unknown"
    timestamp: Optional[datetime] = None

    # Source-specific attributes that do not belong in top-level fields.
    source_metadata: Dict[str, Any] = Field(default_factory=dict)
