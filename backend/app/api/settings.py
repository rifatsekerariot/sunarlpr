import os
import json
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from app.core.config import settings
from app.api.auth import get_current_user

router = APIRouter(prefix="/settings", tags=["Settings"])

class EBASettingsSchema(BaseModel):
    EBA_ENABLED: bool = Field(..., description="eBA entegrasyonunun aktiflik durumu")
    EBA_API_TYPE: str = Field(..., description="Entegrasyon protokolü (REST veya SOAP)")
    EBA_SOAP_URL: str = Field(..., description="Bimser eBA SOAP web servis adresi")
    EBA_REST_URL: str = Field(..., description="Bimser eBA REST API adresi")
    EBA_USER: str = Field(..., description="Servis kullanıcısı adı")
    EBA_PASSWORD: str = Field(..., description="Servis kullanıcısı şifresi")

@router.get("/eba", response_model=EBASettingsSchema, summary="eBA Entegrasyon Ayarlarını Getir", description="Aktif olan Bimser eBA entegrasyon parametrelerini okur.")
async def get_eba_settings(current_user = Depends(get_current_user)):
    return EBASettingsSchema(
        EBA_ENABLED=settings.EBA_ENABLED,
        EBA_API_TYPE=settings.EBA_API_TYPE,
        EBA_SOAP_URL=settings.EBA_SOAP_URL,
        EBA_REST_URL=settings.EBA_REST_URL,
        EBA_USER=settings.EBA_USER,
        EBA_PASSWORD=settings.EBA_PASSWORD
    )

@router.put("/eba", status_code=status.HTTP_200_OK, summary="eBA Entegrasyon Ayarlarını Güncelle", description="Bimser eBA entegrasyon parametrelerini günceller ve diske kaydeder. Sadece ADMIN veya MANAGER yetkisine sahip kullanıcılar güncelleyebilir.")
async def update_eba_settings(eba_in: EBASettingsSchema, current_user = Depends(get_current_user)):
    if current_user.role not in ["ADMIN", "MANAGER"]:
        raise HTTPException(status_code=403, detail="Not authorized to edit settings")

    # Update in-memory configuration settings
    settings.EBA_ENABLED = eba_in.EBA_ENABLED
    settings.EBA_API_TYPE = eba_in.EBA_API_TYPE
    settings.EBA_SOAP_URL = eba_in.EBA_SOAP_URL
    settings.EBA_REST_URL = eba_in.EBA_REST_URL
    settings.EBA_USER = eba_in.EBA_USER
    settings.EBA_PASSWORD = eba_in.EBA_PASSWORD

    # Save to eba_settings.json
    try:
        eba_json_path = os.path.join(settings.MEDIA_ROOT, "eba_settings.json")
        data = {
            "EBA_ENABLED": settings.EBA_ENABLED,
            "EBA_API_TYPE": settings.EBA_API_TYPE,
            "EBA_SOAP_URL": settings.EBA_SOAP_URL,
            "EBA_REST_URL": settings.EBA_REST_URL,
            "EBA_USER": settings.EBA_USER,
            "EBA_PASSWORD": settings.EBA_PASSWORD
        }
        with open(eba_json_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to persist settings: {str(e)}")

    return {"detail": "eBA settings updated successfully."}
