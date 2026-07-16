from pydantic import BaseModel, Field
from uuid import UUID
from datetime import datetime
from typing import List

# Camera Schemas
class CameraBase(BaseModel):
    name: str = Field(..., max_length=100)
    location: str = Field(..., max_length=200)
    direction: str = Field(..., max_length=20)
    rtsp_url: str = Field(..., max_length=500)
    is_active: bool = True

class CameraCreate(CameraBase):
    pass

class CameraResponse(CameraBase):
    id: UUID
    created_at: datetime

    class Config:
        from_attributes = True


# Vehicle Schemas
class VehicleBase(BaseModel):
    plate_number: str = Field(..., max_length=20)
    status: str = Field(..., max_length=20)  # 'AUTHORIZED', 'UNAUTHORIZED', 'PENDING'
    owner_name: str | None = None
    company: str | None = None
    department: str | None = None
    phone: str | None = None
    brand: str | None = None
    model: str | None = None
    color: str | None = None
    vehicle_type: str | None = None
    notes: str | None = None
    snapshot_path: str | None = None
    is_active: bool = True
    valid_until: datetime | None = None
    card_number: str | None = None
    rfid_tag: str | None = None
    reason: str | None = None

class VehicleCreate(VehicleBase):
    pass

class VehicleUpdate(BaseModel):
    status: str | None = None
    owner_name: str | None = None
    company: str | None = None
    department: str | None = None
    phone: str | None = None
    brand: str | None = None
    model: str | None = None
    color: str | None = None
    vehicle_type: str | None = None
    notes: str | None = None
    is_active: bool | None = None
    valid_until: datetime | None = None
    card_number: str | None = None
    rfid_tag: str | None = None
    reason: str | None = None

class VehicleResponse(VehicleBase):
    id: UUID
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class VehicleBulkDelete(BaseModel):
    ids: List[UUID]



# Detection/AccessLog Schemas
class DetectionRequest(BaseModel):
    plate_number: str
    camera_id: UUID
    direction: str
    ocr_confidence: float
    ai_confidence: float
    snapshot_path: str
    plate_crop_path: str
    review_needed: bool = False

class AccessLogResponse(BaseModel):
    id: UUID
    plate_number: str
    vehicle_id: UUID | None
    camera_id: UUID | None
    direction: str
    timestamp: datetime
    ocr_confidence: float
    ai_confidence: float
    snapshot_path: str
    plate_crop_path: str
    is_authorized: bool
    operator_id: UUID | None
    gate_opened: bool
    notes: str | None
    review_needed: bool

    class Config:
        from_attributes = True


# User / Auth Schemas
class UserBase(BaseModel):
    username: str
    role: str

class UserCreate(UserBase):
    password: str

class UserResponse(UserBase):
    id: UUID
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    token_type: str
