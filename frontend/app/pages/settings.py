from nicegui import ui
from app.api_client import api_client

def show_settings():
    cameras_list = []

    columns = [
        {'name': 'name', 'label': 'Kamera Adı', 'field': 'name', 'align': 'left'},
        {'name': 'location', 'label': 'Lokasyon', 'field': 'location', 'align': 'left'},
        {'name': 'direction', 'label': 'Yön', 'field': 'direction', 'align': 'center'},
        {'name': 'rtsp_url', 'label': 'RTSP Bağlantısı', 'field': 'rtsp_url', 'align': 'left'},
        {'name': 'is_active', 'label': 'Durum', 'field': 'is_active', 'align': 'center'},
        {'name': 'actions', 'label': 'İşlemler', 'field': 'actions', 'align': 'center'}
    ]

    with ui.column().classes('w-full gap-6'):
        with ui.row().classes('w-full justify-between items-center'):
            ui.label("Sistem Ayarları & Kamera Yönetimi").classes('text-2xl font-bold text-primary')
            ui.button("➕ YENİ KAMERA EKLE", on_click=lambda: add_camera_dialog()).classes('bg-emerald-600 text-white font-bold px-4 py-2')

        # Camera management panel
        with ui.card().classes('w-full p-6 dark:bg-slate-900 border dark:border-slate-800'):
            ui.label("IP Kamera Listesi").classes('text-lg font-bold mb-4')
            cam_table = ui.table(columns=columns, rows=[], row_key='id').classes('w-full')

            cam_table.add_slot('body-cell-is_active', '''
                <q-td :props="props" class="text-center">
                    <q-chip :color="props.row.is_active ? 'green' : 'grey'" text-color="white" dense>
                        {{ props.row.is_active ? 'AKTİF' : 'PASİF' }}
                    </q-chip>
                </q-td>
            ''')

            cam_table.add_slot('body-cell-actions', '''
                <q-td :props="props" class="text-center">
                    <q-btn flat round color="red" icon="delete" @click="$parent.$emit('delete_camera', props.row.id)" />
                </q-td>
            ''')

            cam_table.on('delete_camera', lambda msg: delete_camera(msg.args))

        # System statistics / details card
        with ui.card().classes('w-full p-6 dark:bg-slate-900 border dark:border-slate-800 mt-4'):
            ui.label("Genel Sistem Yapılandırması").classes('text-lg font-bold mb-2')
            ui.label("Bu panelden IP kamera akışlarını, RTSP adreslerini, giriş/çıkış yönlerini ve genel sistem parametrelerini yönetebilirsiniz.").classes('text-sm text-gray-500 mb-4')

    async def load_cameras():
        try:
            data = await api_client.client.get("/api/cameras")
            if data.status_code == 200:
                cam_table.rows = data.json()
        except Exception as e:
            ui.notify(f"Kameralar yüklenirken hata oluştu: {str(e)}", type="negative")

    def add_camera_dialog():
        with ui.dialog() as dialog, ui.card().classes('w-[500px] p-6 dark:bg-slate-900'):
            ui.label("Yeni Kamera Tanımla").classes('text-xl font-bold mb-4')
            
            name_input = ui.input("Kamera Adı (Örn: Ana Kapı Giriş)").classes('w-full mb-2')
            loc_input = ui.input("Lokasyon (Örn: Kuzey Nizamiyesi)").classes('w-full mb-2')
            dir_select = ui.select(options=["IN", "OUT"], value="IN", label="Yön").classes('w-full mb-2')
            rtsp_input = ui.input("RTSP URL").classes('w-full mb-4')

            with ui.row().classes('w-full justify-end gap-3'):
                ui.button("İptal", on_click=dialog.close).classes('bg-slate-500 text-white')
                ui.button("Kaydet", on_click=lambda: save_camera(dialog, name_input.value, loc_input.value, dir_select.value, rtsp_input.value)).classes('bg-emerald-600 text-white')
        dialog.open()

    async def save_camera(dialog, name, location, direction, rtsp):
        payload = {
            "name": name,
            "location": location,
            "direction": direction,
            "rtsp_url": rtsp,
            "is_active": True
        }
        try:
            r = await api_client.client.post("/api/cameras", json=payload)
            if r.status_code in [200, 201]:
                ui.notify("Kamera başarıyla kaydedildi.", type="positive")
                dialog.close()
                await load_cameras()
            else:
                ui.notify(f"Kamera kaydedilemedi: {r.text}", type="negative")
        except Exception as e:
            ui.notify(f"Bağlantı hatası: {str(e)}", type="negative")

    async def delete_camera(camera_id: str):
        try:
            r = await api_client.client.delete(f"/api/cameras/{camera_id}")
            if r.status_code in [200, 204]:
                ui.notify("Kamera başarıyla silindi.", type="info")
                await load_cameras()
            else:
                ui.notify("Kamera silinemedi.", type="negative")
        except Exception as e:
            ui.notify(f"Hata: {str(e)}", type="negative")

    ui.timer(0.2, load_cameras, once=True)
