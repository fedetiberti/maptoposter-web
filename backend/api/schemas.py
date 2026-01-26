"""
Pydantic schemas for API request/response models.
"""
from typing import Optional, Dict, List, Literal
from pydantic import BaseModel, Field


class GenerateOptions(BaseModel):
    """Optional generation parameters."""
    distance: int = Field(default=15000, ge=4000, le=30000, description="Map radius in meters")
    width: float = Field(default=12, ge=3, le=20, description="Image width in inches")
    height: float = Field(default=16, ge=3, le=24, description="Image height in inches")
    format: Literal["png", "svg", "pdf"] = Field(default="png", description="Output format")
    city_label: Optional[str] = Field(default=None, description="Override city name on poster")
    country_label: Optional[str] = Field(default=None, description="Override country name on poster")


class GenerateRequest(BaseModel):
    """Request body for poster generation."""
    city: str = Field(..., min_length=1, max_length=100, description="City name")
    country: str = Field(..., min_length=1, max_length=100, description="Country name")
    theme: str = Field(default="feature_based", description="Theme name")
    preview: bool = Field(default=False, description="Generate low-res preview instead of full resolution")
    options: GenerateOptions = Field(default_factory=GenerateOptions)


class GenerateResponse(BaseModel):
    """Response for job submission."""
    job_id: str
    status: str
    estimated_wait: int = Field(description="Estimated wait time in seconds")


class JobStatusResponse(BaseModel):
    """Response for job status check."""
    job_id: str
    status: Literal["pending", "processing", "complete", "error"]
    progress: int = Field(ge=0, le=100)
    download_url: Optional[str] = None
    expires_at: Optional[str] = None
    error: Optional[str] = None


class ThemeColors(BaseModel):
    """Color values for a theme."""
    bg: str
    text: str
    road_primary: str
    water: str
    parks: str


class Theme(BaseModel):
    """Theme information."""
    id: str
    name: str
    description: str
    colors: ThemeColors


class ThemesResponse(BaseModel):
    """Response containing all available themes."""
    themes: List[Theme]


class DimensionPreset(BaseModel):
    """A dimension preset option."""
    id: str
    name: str
    width: float
    height: float
    description: str


class PresetsResponse(BaseModel):
    """Response containing dimension presets."""
    presets: List[DimensionPreset]
