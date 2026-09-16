from typing import List, Optional
from pydantic import BaseModel, Field


class CallerScreenRequest(BaseModel):
    phone_number: str = Field(..., description="Incoming phone number or shortcode, e.g. +1234567890 or 987")
    country_code: Optional[str] = Field(None, description="Optional ISO country code, e.g. US, ZA, MW")


class CallerScreenResponse(BaseModel):
    phone_number: str = Field(..., description="Normalized caller phone number")
    risk_level: str = Field(..., description="Low, Medium, or High risk level")
    is_known_scam_number: bool = Field(False, description="True if caller ID matches flagged SuspiciousSender DB records")
    carrier_category: str = Field("UNKNOWN", description="ROBOCALL, FINANCIAL_IMPERSONATOR, TELEMARKETER, or LEGITIMATE")
    flag_count: int = Field(0, description="Total community scam reports linked to this caller ID")
    recommended_action: str = Field("ALLOW", description="ALLOW, SILENCE, or DISALLOW")
    signals: List[str] = Field(default_factory=list, description="Specific threat signals detected for this caller ID")
