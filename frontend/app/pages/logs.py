from nicegui import ui
from app.api_client import api_client
from app.components.vehicle_modal import VehicleDetailModal

def show_logs():
    columns = [
        {'name': 'timestamp', 'label': 'Tarih / Saat', 'field': 'timestamp', 'align': 'left'},
        {'name': 'plate_number', 'label': 'Plaka', 'field': 'plate_number', 'align': 'left'},
        {'name': 'direction', 'label': 'Yön', 'field': 'direction', 'align': 'center'},
        {'name': 'ocr_confidence', 'label': 'OCR Güven', 'field': 'ocr_confidence', 'align': 'center'},
        {'name': 'is_authorized', 'label': 'Giriş İzni', 'field': 'is_authorized', 'align': 'center'},
        {'name': 'gate_opened', 'label': 'Kapı Tetiklendi', 'field': 'gate_opened', 'align': 'center'},
        {'name': 'actions', 'label': 'İşlemler', 'field': 'actions', 'align': 'center'}
    ]

    with ui.column().classes('w-full gap-4'):
        ui.label("Geçiş Kayıtları Geçmişi").classes('text-2xl font-bold text-primary')

        # Filter bar
        with ui.row().classes('w-full gap-4 bg-slate-100 dark:bg-slate-800 p-4 rounded-lg items-center'):
            plate_filter = ui.input(placeholder="Plaka girin...").classes('w-48 bg-white dark:bg-slate-900 rounded px-2')
            
            direction_select = ui.select(
                options=["Tümü", "IN", "OUT"],
                value="Tümü",
                label="Yön"
            ).classes('w-32')
            
            auth_select = ui.select(
                options=["Tümü", "YETKİLİ", "YETKİSİZ"],
                value="Tümü",
                label="Yetki"
            ).classes('w-40')
            
            ui.button("Filtrele", on_click=lambda: load_logs()).classes('bg-primary text-white')
            ui.button("Temizle", on_click=lambda: clear_filters()).classes('bg-slate-500 text-white')

        # Logs Table
        logs_table = ui.table(columns=columns, rows=[], row_key='id').classes('w-full border rounded-lg shadow dark:border-slate-800')

        # Custom cell chips
        logs_table.add_slot('body-cell-is_authorized', '''
            <q-td :props="props" class="text-center">
                <q-chip :color="props.row.is_authorized ? 'green' : 'red'" text-color="white" dense>
                    {{ props.row.is_authorized ? 'İZİN VERİLDİ' : 'REDDEDİLDİ' }}
                </q-chip>
            </q-td>
        ''')

        logs_table.add_slot('body-cell-gate_opened', '''
            <q-td :props="props" class="text-center">
                <q-chip :color="props.row.gate_opened ? 'green' : 'red'" text-color="white" dense>
                    {{ props.row.gate_opened ? 'AÇILDI' : 'KAPALI' }}
                </q-chip>
            </q-td>
        ''')

        logs_table.add_slot('body-cell-actions', '''
            <q-td :props="props" class="text-center">
                <q-btn color="secondary" icon="history" label="Araç Geçmişi" dense size="sm" @click="$parent.$emit('view_details', props.row.plate_number)" />
            </q-td>
        ''')

        logs_table.on('view_details', lambda msg: VehicleDetailModal(msg.args).open())

    async def load_logs():
        plate = plate_filter.value if plate_filter.value else None
        dir_val = direction_select.value if direction_select.value != "Tümü" else None
        
        is_auth = None
        if auth_select.value == "YETKİLİ":
            is_auth = True
        elif auth_select.value == "YETKİSİZ":
            is_auth = False
            
        data = await api_client.get_logs(plate=plate)
        # Apply local formatting and client-side filtering if needed
        rows = []
        for l in data:
            # Simple manual filter for direction and authorization status match
            if dir_val and l["direction"] != dir_val:
                continue
            if is_auth is not None and l["is_authorized"] != is_auth:
                continue
                
            rows.append({
                "id": l["id"],
                "timestamp": l["timestamp"][:16].replace("T", " "),
                "plate_number": l["plate_number"],
                "direction": l["direction"],
                "ocr_confidence": f"%{int(l['ocr_confidence'] * 100)}",
                "is_authorized": l["is_authorized"],
                "gate_opened": l["gate_opened"]
            })
        logs_table.rows = rows

    async def clear_filters():
        plate_filter.value = ""
        direction_select.value = "Tümü"
        auth_select.value = "Tümü"
        await load_logs()

    ui.timer(0.2, load_logs, once=True)
