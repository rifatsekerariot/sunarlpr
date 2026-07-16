from nicegui import ui
from app.api_client import api_client

class UnknownVehiclePopup(ui.dialog):
    def __init__(self, data: dict, on_action_done=None):
        super().__init__()
        self.data = data
        self.on_action_done = on_action_done
        self.plate_number = data.get("plate_number", "")
        self.log_id = data.get("log_id", "")
        
        # Resolve full URL path for Nginx images
        img_url = f"{api_client.base_url}{data.get('snapshot_path', '')}"

        with self, ui.card().classes('w-[500px] p-6 dark:bg-slate-900 border-2 border-amber-500 rounded-xl shadow-2xl'):
            # Red/Amber blinking header effect
            with ui.row().classes('w-full items-center justify-between bg-amber-500 text-slate-950 p-3 rounded-lg mb-4'):
                ui.label("⚠️ Yeni Araç Tespit Edildi (Bilinmeyen)").classes('text-lg font-bold')
                ui.button(icon='close', on_click=self.close).flat().props('dense text-slate-950')

            with ui.column().classes('w-full gap-3 mb-4'):
                with ui.row().classes('w-full justify-between border-b pb-2 dark:border-slate-800'):
                    ui.label("Plaka").classes('font-bold text-gray-500')
                    ui.label(self.plate_number).classes('text-2xl font-black text-amber-500 tracking-wider')
                
                with ui.row().classes('w-full justify-between border-b pb-2 dark:border-slate-800'):
                    ui.label("İlk Görülme").classes('font-bold text-gray-500')
                    ui.label(data.get("timestamp", "")[:16].replace("T", " ")).classes('font-semibold')
                
                with ui.row().classes('w-full justify-between border-b pb-2 dark:border-slate-800'):
                    ui.label("Kamera / Lokasyon").classes('font-bold text-gray-500')
                    ui.label(f"{data.get('camera_name', 'Ana Giriş')} ({data.get('direction', 'IN')})").classes('font-semibold')

            ui.label("Araç Görseli").classes('font-bold text-gray-500 mb-1')
            ui.image(img_url).classes('w-full h-64 object-cover rounded-lg border dark:border-slate-700 shadow mb-6')

            with ui.column().classes('w-full gap-2'):
                ui.button("✅ YETKİLİ ARAÇ OLARAK KAYDET", on_click=self.save_authorized).classes('w-full bg-emerald-600 hover:bg-emerald-700 text-white font-bold py-3 rounded-lg text-md shadow-md')
                ui.button("❌ YETKİSİZ ARAÇ OLARAK KAYDET", on_click=self.save_unauthorized).classes('w-full bg-rose-600 hover:bg-rose-700 text-white font-bold py-3 rounded-lg text-md shadow-md')
                ui.button("⏳ DAHA SONRA İNCELE", on_click=self.close).classes('w-full bg-slate-600 hover:bg-slate-700 text-white py-2 rounded-lg text-sm')

    async def save_authorized(self):
        self.close()
        # Open detailed registration wizard
        RegistrationWizard(self.plate_number, "AUTHORIZED", self.data.get("snapshot_path"), self.on_action_done).open()

    async def save_unauthorized(self):
        self.close()
        RegistrationWizard(self.plate_number, "UNAUTHORIZED", self.data.get("snapshot_path"), self.on_action_done).open()


class RegistrationWizard(ui.dialog):
    def __init__(self, plate: str, target_status: str, snapshot_path: str | None, on_success=None):
        super().__init__()
        self.plate = plate
        self.target_status = target_status
        self.snapshot_path = snapshot_path
        self.on_success = on_success

        with self, ui.card().classes('w-[600px] p-6 dark:bg-slate-900'):
            ui.label(f"{'Yetkili' if target_status == 'AUTHORIZED' else 'Yetkisiz'} Araç Kayıt Formu").classes('text-xl font-bold mb-4 text-primary')
            
            with ui.grid(columns=2).classes('w-full gap-4'):
                self.plate_input = ui.input("Plaka", value=self.plate).classes('w-full').props('readonly')
                self.owner_input = ui.input("Araç Sahibi").classes('w-full')
                self.company_input = ui.input("Firma").classes('w-full')
                self.dept_input = ui.input("Departman").classes('w-full')
                self.phone_input = ui.input("Telefon").classes('w-full')
                self.brand_input = ui.input("Marka").classes('w-full')
                self.model_input = ui.input("Model").classes('w-full')
                self.color_input = ui.input("Renk").classes('w-full')
                
                self.type_select = ui.select(
                    label="Araç Tipi",
                    options=["PERSONEL", "MİSAFİR", "TEDARİKÇİ", "LOJİSTİK", "VIP", "ACİL_DURUM"],
                    value="PERSONEL"
                ).classes('w-full')
                
                self.card_input = ui.input("Kart Numarası (Opsiyonel)").classes('w-full')
                self.rfid_input = ui.input("RFID Etiketi (Opsiyonel)").classes('w-full')

            if target_status == "UNAUTHORIZED":
                self.reason_input = ui.textarea("Engelleme / Yetkisizleştirme Sebebi").classes('w-full col-span-2 mt-2')
            else:
                self.reason_input = None

            self.notes_input = ui.textarea("Notlar").classes('w-full col-span-2 mt-2')

            with ui.row().classes('w-full justify-end gap-3 mt-6'):
                ui.button("İptal", on_click=self.close).classes('bg-slate-500 text-white')
                ui.button("Kaydet", on_click=self.submit_form).classes('bg-emerald-600 text-white')

    async def submit_form(self):
        # Fetch matching record first to check if we are updating a pending record
        vehicles = await api_client.get_vehicles(query=self.plate)
        matching_vehicle = None
        for v in vehicles:
            if v["plate_number"] == self.plate:
                matching_vehicle = v
                break

        payload = {
            "plate_number": self.plate,
            "status": self.target_status,
            "owner_name": self.owner_input.value,
            "company": self.company_input.value,
            "department": self.dept_input.value,
            "phone": self.phone_input.value,
            "brand": self.brand_input.value,
            "model": self.model_input.value,
            "color": self.color_input.value,
            "vehicle_type": self.type_select.value,
            "card_number": self.card_input.value or None,
            "rfid_tag": self.rfid_input.value or None,
            "notes": self.notes_input.value or None,
            "snapshot_path": self.snapshot_path,
            "is_active": True
        }

        if self.reason_input:
            payload["reason"] = self.reason_input.value

        success = False
        if matching_vehicle:
            # Update record
            success = await api_client.update_vehicle(matching_vehicle["id"], payload)
        
        if success:
            ui.notify("Araç listesi başarıyla güncellendi!", type="positive", position="top-right")
            self.close()
            if self.on_success:
                self.on_success()
        else:
            ui.notify("Kayıt güncellenirken hata oluştu.", type="negative", position="top-right")
