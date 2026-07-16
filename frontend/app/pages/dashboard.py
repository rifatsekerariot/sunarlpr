from nicegui import ui
import asyncio
from app.api_client import api_client
from app.components.vehicle_modal import VehicleDetailModal
from app.components.operator_popups import UnknownVehiclePopup
from app.components.notifier import active_listeners
from app.theme import Theme

def show_dashboard():
    stats_data = {
        "today_in": 0, "today_out": 0, "inside_count": 0,
        "authorized_count": 0, "unauthorized_count": 0, "pending_count": 0,
        "active_cameras": 0, "ai_status": "OFFLINE", "database_status": "OFFLINE",
        "redis_status": "OFFLINE", "worker_status": "OFFLINE"
    }

    # 1. Statistics Cards with Minimal thin border and subtle shadow
    with ui.grid(columns=4).classes('w-full gap-6 mb-8'):
        # Today In
        with ui.card().classes('p-6 rounded-xl bg-zinc-900/50 border border-zinc-800 shadow-none'):
            ui.label("Bugünkü Giriş").classes('text-[10px] font-bold text-zinc-500 uppercase tracking-wider')
            in_label = ui.label("0").classes('text-3xl font-light text-zinc-100 mt-2')
            in_label.bind_text_from(stats_data, "today_in")

        # Today Out
        with ui.card().classes('p-6 rounded-xl bg-zinc-900/50 border border-zinc-800 shadow-none'):
            ui.label("Bugünkü Çıkış").classes('text-[10px] font-bold text-zinc-500 uppercase tracking-wider')
            out_label = ui.label("0").classes('text-3xl font-light text-zinc-100 mt-2')
            out_label.bind_text_from(stats_data, "today_out")

        # Inside Count
        with ui.card().classes('p-6 rounded-xl bg-zinc-900/50 border border-zinc-800 shadow-none'):
            ui.label("İçerideki Araç").classes('text-[10px] font-bold text-zinc-500 uppercase tracking-wider')
            inside_label = ui.label("0").classes('text-3xl font-light text-zinc-100 mt-2')
            inside_label.bind_text_from(stats_data, "inside_count")

        # Pending Approval/Review
        with ui.card().classes('p-6 rounded-xl bg-zinc-900/50 border border-zinc-800 shadow-none'):
            ui.label("Bekleyen İnceleme").classes('text-[10px] font-bold text-zinc-500 uppercase tracking-wider')
            pending_label = ui.label("0").classes('text-3xl font-light text-zinc-100 mt-2')
            pending_label.bind_text_from(stats_data, "pending_count")

    # 2. Live Log Table Header and Structure
    ui.label("Canlı Geçiş Kayıtları").classes('text-xs font-semibold tracking-wider uppercase text-zinc-400 mb-4')
    
    # Custom Table
    columns = [
        {'name': 'timestamp', 'label': 'SAAT', 'field': 'timestamp', 'align': 'left'},
        {'name': 'plate_number', 'label': 'PLAKA', 'field': 'plate_number', 'align': 'left'},
        {'name': 'direction', 'label': 'YÖN', 'field': 'direction', 'align': 'center'},
        {'name': 'ocr_confidence', 'label': 'OCR GÜVEN', 'field': 'ocr_confidence', 'align': 'center'},
        {'name': 'status', 'label': 'DURUM', 'field': 'status', 'align': 'center'},
        {'name': 'gate_opened', 'label': 'KAPI DURUMU', 'field': 'gate_opened', 'align': 'center'},
        {'name': 'actions', 'label': 'İŞLEMLER', 'field': 'actions', 'align': 'center'}
    ]
    
    log_table = ui.table(columns=columns, rows=[], row_key='id').classes('w-full rounded-xl bg-zinc-950 border border-zinc-800 shadow-none')
    
    # Table custom slot for plate clicks and actions
    log_table.add_slot('body-cell-plate_number', '''
        <q-td :props="props">
            <q-btn flat dense color="indigo" class="text-[13px] font-medium" @click="$parent.$emit('plate_clicked', props.row.plate_number)">
                {{ props.row.plate_number }}
            </q-btn>
        </q-td>
    ''')

    log_table.add_slot('body-cell-gate_opened', '''
        <q-td :props="props" class="text-center">
            <q-chip style="background-color: rgba(16, 185, 129, 0.1); color: #10b981; border: 1px solid rgba(16, 185, 129, 0.2);" dense class="text-[11px] font-medium rounded-full px-2">
                {{ props.row.gate_opened ? 'AÇILDI' : 'KAPALI' }}
            </q-chip>
        </q-td>
    ''')
    
    log_table.add_slot('body-cell-status', '''
        <q-td :props="props" class="text-center">
            <q-chip :style="props.row.is_authorized 
                ? 'background-color: rgba(16, 185, 129, 0.1); color: #10b981; border: 1px solid rgba(16, 185, 129, 0.2);' 
                : (props.row.vehicle_status === 'UNAUTHORIZED' 
                    ? 'background-color: rgba(239, 68, 68, 0.1); color: #ef4444; border: 1px solid rgba(239, 68, 68, 0.2);' 
                    : 'background-color: rgba(245, 158, 11, 0.1); color: #f59e0b; border: 1px solid rgba(245, 158, 11, 0.2);')" 
                dense class="text-[11px] font-medium rounded-full px-2">
                {{ props.row.is_authorized ? 'YETKİLİ' : (props.row.vehicle_status === 'UNAUTHORIZED' ? 'YETKİSİZ' : 'BİLİNMEYEN') }}
            </q-chip>
        </q-td>
    ''')

    log_table.add_slot('body-cell-actions', '''
        <q-td :props="props" class="text-center">
            <q-btn outline color="zinc-400" label="Detay" dense size="xs" class="px-2.5 py-0.5 rounded border border-zinc-800 text-[11px] text-zinc-300 hover:bg-zinc-800 transition-colors" @click="$parent.$emit('view_details', props.row.plate_number)" />
        </q-td>
    ''')

    log_table.on('plate_clicked', lambda msg: VehicleDetailModal(msg.args).open())
    log_table.on('view_details', lambda msg: VehicleDetailModal(msg.args).open())

    # Shared UI stats updates
    async def update_statistics():
        data = await api_client.get_stats()
        if data:
            stats_data.update(data)

    async def load_initial_logs():
        logs = await api_client.get_logs(limit=15)
        formatted_rows = []
        for l in logs:
            formatted_rows.append({
                "id": l["id"],
                "timestamp": l["timestamp"][:16].replace("T", " "),
                "plate_number": l["plate_number"],
                "direction": l["direction"],
                "ocr_confidence": f"%{int(l['ocr_confidence'] * 100)}",
                "is_authorized": l["is_authorized"],
                "vehicle_status": "PENDING" if not l["vehicle_id"] else ("AUTHORIZED" if l["is_authorized"] else "UNAUTHORIZED"),
                "gate_opened": l["gate_opened"]
            })
        log_table.rows = formatted_rows

    def on_redis_event(data):
        ui.timer(0.1, update_statistics, once=True)
        is_auth = data.get("status") == "AUTHORIZED"
        ui.notify(
            f"Plaka Okundu: {data.get('plate_number')}",
            type="info" if is_auth else "warning",
            position="top-right"
        )
        if data.get("status") == "PENDING":
            UnknownVehiclePopup(data, on_action_done=load_initial_logs).open()
            
        new_row = {
            "id": data.get("log_id"),
            "timestamp": data.get("timestamp")[:16].replace("T", " "),
            "plate_number": data.get("plate_number"),
            "direction": data.get("direction"),
            "ocr_confidence": f"%{int(data.get('ocr_confidence', 0) * 100)}",
            "is_authorized": data.get("status") == "AUTHORIZED",
            "vehicle_status": data.get("status"),
            "gate_opened": data.get("gate_opened")
        }
        log_table.rows.insert(0, new_row)
        if len(log_table.rows) > 30:
            log_table.rows.pop()

    active_listeners.add(on_redis_event)
    ui.timer(0.2, update_statistics, once=True)
    ui.timer(0.5, load_initial_logs, once=True)
    ui.timer(5.0, update_statistics)
