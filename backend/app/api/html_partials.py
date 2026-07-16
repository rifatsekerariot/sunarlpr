from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc, or_
from typing import Optional
from datetime import datetime, timezone
from app.core.database import get_db_session
from app.models.models import AccessLog, Vehicle, Camera

router = APIRouter(prefix="/html", tags=["HTML Partials"])

@router.get("/kpis", response_class=HTMLResponse)
async def get_kpis_html(db: AsyncSession = Depends(get_db_session)):
    today_start = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
    in_today = await db.scalar(select(func.count(AccessLog.id)).filter(AccessLog.timestamp >= today_start, AccessLog.direction == "IN")) or 0
    out_today = await db.scalar(select(func.count(AccessLog.id)).filter(AccessLog.timestamp >= today_start, AccessLog.direction == "OUT")) or 0
    auth_vehicles = await db.scalar(select(func.count(Vehicle.id)).filter(Vehicle.status == "AUTHORIZED", Vehicle.is_active == True)) or 0
    pending_vehicles = await db.scalar(select(func.count(Vehicle.id)).filter(Vehicle.status == "PENDING")) or 0
    inside_count = max(0, in_today - out_today)

    return f"""
    <div class="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
        <div class="p-6 rounded-xl bg-white border border-zinc-200 shadow-sm">
            <div class="text-[10px] font-bold text-zinc-500 uppercase tracking-wider">BUGÜNKÜ GİRİŞ</div>
            <div class="text-3xl font-light text-zinc-900 mt-2">{in_today}</div>
        </div>
        <div class="p-6 rounded-xl bg-white border border-zinc-200 shadow-sm">
            <div class="text-[10px] font-bold text-zinc-500 uppercase tracking-wider">BUGÜNKÜ ÇIKIŞ</div>
            <div class="text-3xl font-light text-zinc-900 mt-2">{out_today}</div>
        </div>
        <div class="p-6 rounded-xl bg-white border border-zinc-200 shadow-sm">
            <div class="text-[10px] font-bold text-zinc-500 uppercase tracking-wider">İÇERİDEKİ ARAÇ</div>
            <div class="text-3xl font-light text-zinc-900 mt-2">{inside_count}</div>
        </div>
        <div class="p-6 rounded-xl bg-white border border-zinc-200 shadow-sm">
            <div class="text-[10px] font-bold text-zinc-500 uppercase tracking-wider">BEKLEYEN İNCELEME</div>
            <div class="text-3xl font-light text-zinc-900 mt-2">{pending_vehicles}</div>
        </div>
    </div>
    """

@router.get("/logs", response_class=HTMLResponse)
async def get_logs_html(db: AsyncSession = Depends(get_db_session)):
    result = await db.execute(select(AccessLog).order_by(AccessLog.timestamp.desc()).limit(15))
    logs = result.scalars().all()
    
    rows = ""
    for log in logs:
        status_bg = "bg-emerald-55 text-emerald-700 border-emerald-200" if log.is_authorized else "bg-red-50 text-red-700 border-red-200"
        status_text = "YETKİLİ" if log.is_authorized else "BİLİNMEYEN"
        gate_bg = "bg-emerald-50 text-emerald-700 border-emerald-200" if log.gate_opened else "bg-zinc-50 text-zinc-700 border-zinc-200"
        gate_text = "AÇILDI" if log.gate_opened else "KAPALI"

        rows += f"""
        <tr class="border-b border-zinc-200 hover:bg-zinc-50 transition-colors">
            <td class="px-6 py-4 text-sm text-zinc-500">{log.timestamp.strftime('%H:%M:%S')}</td>
            <td class="px-6 py-4 text-sm font-semibold text-zinc-950 tracking-wider">{log.plate_number}</td>
            <td class="px-6 py-4 text-sm text-zinc-500">{log.direction}</td>
            <td class="px-6 py-4 text-sm text-zinc-500">%{int(log.ocr_confidence * 100)}</td>
            <td class="px-6 py-4 text-center">
                <span class="px-2.5 py-0.5 text-xs rounded-full border {status_bg} font-medium">{status_text}</span>
            </td>
            <td class="px-6 py-4 text-center">
                <span class="px-2.5 py-0.5 text-xs rounded-full border {gate_bg} font-medium">{gate_text}</span>
            </td>
            <td class="px-6 py-4 text-center">
                <button class="px-2.5 py-1 text-xs border border-zinc-200 rounded bg-white text-zinc-700 hover:bg-zinc-50 transition-colors" onclick="openDetails('{log.plate_number}')">Detay</button>
            </td>
        </tr>
        """
    return rows

@router.get("/vehicles", response_class=HTMLResponse)
async def get_vehicles_html(db: AsyncSession = Depends(get_db_session), query: Optional[str] = None):
    stmt = select(Vehicle)
    if query:
        search = f"%{query}%"
        stmt = stmt.filter(
            or_(
                Vehicle.plate_number.ilike(search),
                Vehicle.owner_name.ilike(search),
                Vehicle.company.ilike(search)
            )
        )
    stmt = stmt.order_by(desc(Vehicle.created_at)).limit(50)
    result = await db.execute(stmt)
    vehicles = result.scalars().all()

    rows = ""
    for v in vehicles:
        status_bg = "bg-emerald-50 text-emerald-700 border-emerald-200" if v.status == "AUTHORIZED" else ("bg-red-50 text-red-700 border-red-200" if v.status == "UNAUTHORIZED" else "bg-amber-50 text-amber-700 border-amber-200")
        status_text = "YETKİLİ" if v.status == "AUTHORIZED" else ("YETKİSİZ" if v.status == "UNAUTHORIZED" else "BEKLEYEN")
        rows += f"""
        <tr class="border-b border-zinc-200 hover:bg-zinc-50 transition-colors">
            <td class="px-6 py-4 text-sm font-semibold text-zinc-950 tracking-wider">{v.plate_number}</td>
            <td class="px-6 py-4 text-center">
                <span class="px-2.5 py-0.5 text-xs rounded-full border {status_bg} font-medium">{status_text}</span>
            </td>
            <td class="px-6 py-4 text-sm text-zinc-700">{v.owner_name or '-'}</td>
            <td class="px-6 py-4 text-sm text-zinc-700">{v.company or '-'}</td>
            <td class="px-6 py-4 text-sm text-zinc-500">{v.vehicle_type or '-'}</td>
            <td class="px-6 py-4 text-center flex justify-center gap-2">
                <button class="px-2 py-1 text-xs border border-zinc-200 rounded bg-white text-zinc-700 hover:bg-zinc-50 transition" onclick="openDetails('{v.plate_number}')">Geçmiş</button>
                <button class="px-2 py-1 text-xs border border-zinc-200 rounded bg-indigo-50 text-indigo-700 hover:bg-indigo-100 transition" onclick="openEditWizard('{v.id}', '{v.plate_number}', '{v.status}')">Düzenle</button>
            </td>
        </tr>
        """
    return rows

@router.get("/cameras", response_class=HTMLResponse)
async def get_cameras_html(db: AsyncSession = Depends(get_db_session)):
    result = await db.execute(select(Camera).order_by(Camera.created_at.desc()))
    cameras = result.scalars().all()
    rows = ""
    for c in cameras:
        status_bg = "bg-emerald-50 text-emerald-700 border-emerald-200" if c.is_active else "bg-zinc-50 text-zinc-700 border-zinc-200"
        status_text = "AKTİF" if c.is_active else "PASİF"
        rows += f"""
        <tr class="border-b border-zinc-200 hover:bg-zinc-50 transition-colors">
            <td class="px-6 py-4 text-sm font-semibold text-zinc-950">{c.name}</td>
            <td class="px-6 py-4 text-sm text-zinc-700">{c.location}</td>
            <td class="px-6 py-4 text-sm text-zinc-500">{c.direction}</td>
            <td class="px-6 py-4 text-sm text-zinc-500 truncate max-w-xs">{c.rtsp_url}</td>
            <td class="px-6 py-4 text-center">
                <span class="px-2.5 py-0.5 text-xs rounded-full border {status_bg} font-medium">{status_text}</span>
            </td>
            <td class="px-6 py-4 text-center">
                <button class="px-2.5 py-1 text-xs border border-red-200 rounded bg-red-50 text-red-700 hover:bg-red-100 transition-colors" onclick="deleteCamera('{c.id}')">Sil</button>
            </td>
        </tr>
        """
    return rows

@router.get("/live-monitor", response_class=HTMLResponse)
async def get_live_monitor_html(db: AsyncSession = Depends(get_db_session)):
    """Returns last 4 detections with snapshot for the live camera monitor panel."""
    result = await db.execute(
        select(AccessLog).order_by(AccessLog.timestamp.desc()).limit(4)
    )
    logs = result.scalars().all()

    if not logs:
        return """
        <div class="flex flex-col items-center justify-center h-full gap-2 text-zinc-400">
            <i class="fas fa-video-slash text-2xl"></i>
            <span class="text-xs">Henüz tespit yok</span>
        </div>
        """

    cards = ""
    for log in logs:
        authorized = log.is_authorized
        border_color = "border-emerald-400" if authorized else "border-red-400"
        badge_bg = "bg-emerald-500" if authorized else "bg-red-500"
        badge_text = "YETKİLİ" if authorized else "BİLİNMEYEN"
        # Use plate_crop_path if exists, fallback to snapshot_path
        img_path = log.plate_crop_path or log.snapshot_path or ""
        img_tag = f'<img src="{img_path}" class="w-full h-14 object-cover rounded" onerror="this.style.display=\'none\'">' if img_path else ""

        ts = log.timestamp.astimezone(timezone.utc).strftime("%H:%M:%S")

        cards += f"""
        <div class="border-2 {border_color} rounded-xl overflow-hidden bg-white shadow-sm flex flex-col">
            <div class="bg-zinc-900 px-3 py-1.5 flex justify-between items-center">
                <span class="text-white font-bold tracking-widest text-sm">{log.plate_number}</span>
                <span class="text-[10px] px-2 py-0.5 rounded-full {badge_bg} text-white font-semibold">{badge_text}</span>
            </div>
            {img_tag}
            <div class="px-3 py-1 text-[10px] text-zinc-400 flex justify-between">
                <span>{log.direction}</span>
                <span>{ts}</span>
            </div>
        </div>
        """

    return f'<div class="grid grid-cols-2 gap-3 h-full">{cards}</div>'
