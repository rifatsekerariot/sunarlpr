from nicegui import ui
import datetime
from app.api_client import api_client

class VehicleDetailModal(ui.dialog):
    def __init__(self, plate: str, on_close_callback=None):
        super().__init__()
        self.plate = plate
        self.on_close_callback = on_close_callback
        self.history_data = []
        
        with self, ui.card().classes('w-[800px] max-w-full p-6 dark:bg-slate-900'):
            ui.label(f"Araç Geçmişi: {plate}").classes('text-2xl font-bold text-primary mb-4')
            
            with ui.row().classes('w-full justify-between items-center bg-slate-100 dark:bg-slate-800 p-4 rounded-lg mb-4'):
                self.first_seen = ui.label("İlk Görülme: Yükleniyor...")
                self.last_seen = ui.label("Son Görülme: Yükleniyor...")
                self.total_seen = ui.label("Toplam Geçiş: Yükleniyor...")

            ui.label("Son Geçişler ve Snapshot Geçmişi").classes('text-lg font-bold mb-2')
            
            # Grid container for historic snapshots
            self.history_grid = ui.grid(columns=3).classes('w-full gap-4 mb-4')
            
            ui.button("Kapat", on_click=self.close).classes('w-full bg-slate-500 text-white mt-4 py-2')
            
        self.load_history()

    async def load_history(self):
        history = await api_client.get_vehicle_history(self.plate)
        self.history_data = history
        
        if not history:
            self.first_seen.text = "İlk Görülme: Kayıt Yok"
            self.last_seen.text = "Son Görülme: Kayıt Yok"
            self.total_seen.text = "Toplam Geçiş: 0"
            return
            
        timestamps = [datetime.datetime.fromisoformat(item["timestamp"].replace("Z", "+00:00")) for item in history]
        timestamps.sort()
        
        self.first_seen.text = f"İlk Görülme: {timestamps[0].strftime('%d.%m.%Y %H:%M')}"
        self.last_seen.text = f"Son Görülme: {timestamps[-1].strftime('%d.%m.%Y %H:%M')}"
        self.total_seen.text = f"Toplam Geçiş: {len(history)}"
        
        # Populate snapshots in the dialog
        self.history_grid.clear()
        with self.history_grid:
            for item in history[:6]:  # Limit to last 6 entries
                # Build image path correctly referencing Nginx local media structure
                img_url = f"{api_client.base_url}{item['snapshot_path']}"
                with ui.card().classes('items-center p-2 border dark:border-slate-700'):
                    ui.image(img_url).classes('w-full h-32 object-cover rounded')
                    ui.label(item["timestamp"][:16].replace("T", " ")).classes('text-xs text-gray-500 mt-1')
                    ui.label(f"Yön: {item['direction']}").classes('text-xs font-semibold')
