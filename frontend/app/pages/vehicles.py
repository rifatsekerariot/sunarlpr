from nicegui import ui
from app.api_client import api_client
from app.components.vehicle_modal import VehicleDetailModal
from app.components.operator_popups import RegistrationWizard
from app.theme import Theme

def show_vehicle_lists():
    columns = [
        {'name': 'plate_number', 'label': 'PLAKA', 'field': 'plate_number', 'align': 'left'},
        {'name': 'status', 'label': 'LİSTE DURUMU', 'field': 'status', 'align': 'center'},
        {'name': 'owner_name', 'label': 'ARAÇ SAHİBİ', 'field': 'owner_name', 'align': 'left'},
        {'name': 'company', 'label': 'FİRMA', 'field': 'company', 'align': 'left'},
        {'name': 'vehicle_type', 'label': 'TİP', 'field': 'vehicle_type', 'align': 'center'},
        {'name': 'actions', 'label': 'İŞLEMLER', 'field': 'actions', 'align': 'center'}
    ]

    with ui.column().classes('w-full gap-6'):
        with ui.row().classes('w-full justify-between items-center'):
            ui.label("Araç Yönetim Listesi").classes('text-lg font-bold text-slate-200')
            ui.button("➕ YENİ ARAÇ EKLE", on_click=lambda: RegistrationWizard("", "AUTHORIZED", None, on_success=load_vehicles).open()).classes('bg-indigo-600 text-white font-bold px-4 py-2 rounded-lg text-xs tracking-wider')

        # Filter bar
        with ui.row().style(f'background-color: {Theme.BG_SURFACE}; border: 1px solid {Theme.BORDER_COLOR};').classes('w-full gap-4 p-4 rounded-xl items-center'):
            search_input = ui.input(placeholder="Plaka, İsim, Firma veya Not ara...").classes('w-96 rounded px-2 dark:text-slate-100')
            
            status_select = ui.select(
                options=["Tümü", "AUTHORIZED", "UNAUTHORIZED", "PENDING"],
                value="Tümü",
                label="Liste Durumu"
            ).classes('w-48 dark:text-slate-100')
            
            ui.button("Filtrele", on_click=lambda: load_vehicles()).classes('bg-indigo-600 text-white rounded-lg px-4 py-2')
            ui.button("Temizle", on_click=lambda: clear_filters()).classes('bg-slate-700 text-white rounded-lg px-4 py-2')

        # Table
        v_table = ui.table(columns=columns, rows=[], row_key='id').style(f'background-color: {Theme.BG_SURFACE}; border: 1px solid {Theme.BORDER_COLOR};').classes('w-full rounded-xl shadow-sm dark:text-slate-100')

        # Custom buttons
        v_table.add_slot('body-cell-status', f'''
            <q-td :props="props" class="text-center">
                <q-chip :style="props.row.status === 'AUTHORIZED' 
                    ? 'background-color: {Theme.COLOR_SUCCESS_BG}; color: {Theme.COLOR_SUCCESS_FG};' 
                    : (props.row.status === 'UNAUTHORIZED' 
                        ? 'background-color: {Theme.COLOR_DANGER_BG}; color: {Theme.COLOR_DANGER_FG};' 
                        : 'background-color: {Theme.COLOR_WARNING_BG}; color: {Theme.COLOR_WARNING_FG};')" 
                    dense class="text-weight-bold">
                    {{{{ props.row.status === 'AUTHORIZED' ? 'YETKİLİ' : (props.row.status === 'UNAUTHORIZED' ? 'YETKİSİZ' : 'BEKLEYEN') }}}}
                </q-chip>
            </q-td>
        ''')

        v_table.add_slot('body-cell-actions', '''
            <q-td :props="props" class="text-center gap-2">
                <q-btn flat round color="indigo" icon="history" @click="$parent.$emit('show_history', props.row.plate_number)" />
                <q-btn flat round :color="props.row.status === 'AUTHORIZED' ? 'red' : 'green'" :icon="props.row.status === 'AUTHORIZED' ? 'block' : 'check_circle'" @click="$parent.$emit('toggle_status', props.row)" />
                <q-btn flat round color="orange" icon="edit" @click="$parent.$emit('edit_vehicle', props.row)" />
            </q-td>
        ''')

        # Register actions
        v_table.on('show_history', lambda msg: VehicleDetailModal(msg.args).open())
        v_table.on('toggle_status', lambda msg: toggle_status(msg.args))
        v_table.on('edit_vehicle', lambda msg: edit_vehicle(msg.args))

    async def load_vehicles():
        q = search_input.value if search_input.value else None
        st = status_select.value if status_select.value != "Tümü" else None
        data = await api_client.get_vehicles(query=q, status=st)
        v_table.rows = data

    async def clear_filters():
        search_input.value = ""
        status_select.value = "Tümü"
        await load_vehicles()

    async def toggle_status(row: dict):
        new_status = "UNAUTHORIZED" if row["status"] == "AUTHORIZED" else "AUTHORIZED"
        payload = {"status": new_status}
        if new_status == "UNAUTHORIZED":
            payload["reason"] = "Operatör tarafından hızlı geçiş."
        success = await api_client.update_vehicle(row["id"], payload)
        if success:
            ui.notify(f"Durum güncellendi: {new_status}", type="info")
            await load_vehicles()

    async def edit_vehicle(row: dict):
        RegistrationWizard(row["plate_number"], row["status"], row["snapshot_path"], on_success=load_vehicles).open()

    ui.timer(0.2, load_vehicles, once=True)
