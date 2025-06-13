import sqlite3
from datetime import datetime
from kivy.config import Config
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.popup import Popup
from kivy.uix.scrollview import ScrollView
from kivy.uix.gridlayout import GridLayout
from kivy.uix.image import Image
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.properties import StringProperty, NumericProperty, BooleanProperty


class MileageDB:
    def __init__(self, db_path="mileage.db"):
        self.conn = sqlite3.connect(db_path)
        self.cursor = self.conn.cursor()
        self._create_table()

    def _create_table(self):
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS mileage (
                month TEXT PRIMARY KEY,
                mileage INTEGER,
                delegations INTEGER
            )
        """)
        self.conn.commit()

    def save_month_data(self, month: str, mileage: int, delegations: int):
        """Insert or update data for a given month (YYYY-MM format)."""
        self.cursor.execute("""
            INSERT OR REPLACE INTO mileage (month, mileage, delegations)
            VALUES (?, ?, ?)
        """, (month, mileage, delegations))
        self.conn.commit()

    def get_month_data(self, month: str):
        """Returns (mileage, delegations) tuple or (0, 0) if no data."""
        self.cursor.execute("SELECT mileage, delegations FROM mileage WHERE month = ?", (month,))
        row = self.cursor.fetchone()
        return row if row else (0, 0)

    def get_all_months(self):
        """Return all months with saved data (for calendar list)."""
        self.cursor.execute("SELECT month FROM mileage ORDER BY month DESC")
        return [row[0] for row in self.cursor.fetchall()]
    
class MileageLayout(BoxLayout):
    Config.set('graphics', 'width', '360')
    Config.set('graphics', 'height', '800')
    current_month = StringProperty()
    start = StringProperty("")
    end = StringProperty("")
    total = NumericProperty(0)
    total_daily = NumericProperty(0)
    d_counter = NumericProperty(0)
    d_counter_daily = NumericProperty(0)
    start_locked = BooleanProperty(False)
    end_locked = BooleanProperty(False)
    save_button = BooleanProperty(False)
    warning_text = StringProperty("")
    was_delegation_text = StringProperty("Brak delegacji")
    selected_month_key = StringProperty()
    selected_month_display = StringProperty()
    selected_month_key = StringProperty(datetime.now().strftime("%Y-%m"))
    selected_month_display = StringProperty(datetime.now().strftime("%B %Y"))

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.db = MileageDB()
        self.selected_month_key = self.selected_month_key
        self.selected_month_display = datetime.now().strftime("%B %Y")
        self.selected_month_key = datetime.now().strftime("%Y-%m")
        self.current_month = datetime.now().strftime("%B    %Y")
        data = self.db.get_month_data(self.selected_month_key)

        mileage, delegations = self.db.get_month_data(self.selected_month_key)
        total_daily = 0
        d_counter_daily = 0
        self.start = ""
        self.end = ""
        self.d_counter = delegations
        self.update_total()
        
    def open_month_selector(self):
        self.set_selected_month(selected_key)

    def set_selected_month(self, month_key):
        self.selected_month_key = month_key
        dt = datetime.strptime(month_key, "%Y-%m")
        self.selected_month_display = dt.strftime("%B %Y")

        data = self.db.get_month_data(month_key)
        if data:
            self.start = str(data[0])
            self.end = str(data[1])
            self.d_counter = data[2]
            self.update_total()

        self.start_locked = True
        is_current = (month_key == self.selected_month_key)
        self.set_editable_state(is_current)

    def set_editable_state(self, editable):
        self.ids.start_input.disabled = not editable
        self.ids.end_input.disabled = not editable
        self.ids.d_button.disabled = not editable
        self.ids.lock_button.disabled = not editable

    def show_month_selector(self):
        available_months = self.db.get_all_months()
        
        layout = GridLayout(cols=1, spacing=10, size_hint_y=None)
        layout.bind(minimum_height=layout.setter('height'))

        for month in available_months:
            btn = Button(text=month, size_hint_y=None, height=40)
            btn.bind(on_release=lambda btn: self.select_month(btn.text))
            layout.add_widget(btn)

        scroll = ScrollView(size_hint=(1, 1))
        scroll.add_widget(layout)

        self.popup = Popup(title="Wybierz miesiąc", content=scroll,
                           size_hint=(0.8, 0.8), auto_dismiss=True)
        self.popup.open()

    def select_month(self, month_key):
        self.selected_month_key = month_key
        data = self.db.get_month_data(month_key)
        self.total = data[0]
        self.d_counter = data[1]
        self.was_delegation_text = "Brak delegacji"
        try:
            date_obj = datetime.strptime(month_key, "%Y-%m")
            self.selected_month_display = date_obj.strftime("%B %Y")
            self.popup.dismiss()
        except ValueError:
            self.selected_month_display = month_key

    def update_start(self, text):
        if text.isdigit() and text != self.start:
            if not self.start_locked:
                self.start = text[:7]

    def update_end(self, text):
        if self.start_locked and text.isdigit():
            end_value = int(text[:7])  # Limit to 7 digits
            try:
                start_value = int(self.start)
            except ValueError:
                return

            if end_value > start_value:
                self.end = str(end_value)
                self.warning_text = ""  # clear warning

                self.total_daily = end_value - start_value
                db_mileage, _ = self.db.get_month_data(self.selected_month_key)
                self.total = db_mileage + self.total_daily
            else:
                self.warning_text = "Wartość końcowa  >  wartość początkowa"

##    def increment_d(self, text=None):
##        self.d_counter_daily += 1
##        self.was_delegation_text = f"Delegacji: + (self.d_counter_daily)"

    def toggle_delegation(self):
        if self.was_delegation_text == "Brak delegacji":
            self.was_delegation_text = "Była delegacja"
            self.d_counter_daily = 1
        else:
            self.was_delegation_text = "Brak delegacji"
            self.d_counter_daily = 0

    def update_total(self):
        try:
            db_mileage, _ = self.db.get_month_data(self.selected_month_key)
            self.total = db_mileage + self.total_daily
        except ValueError:
            pass

    def save(self):
        if self.d_counter_daily == 1:
            self.d_counter += 1
        
        mileage = self.total
        self.save_button = True
        self.db.save_month_data(self.selected_month_key, self.total, self.d_counter)

    def lock_start(self):
        if self.start:
            self.start_locked = True
            self.update_total()

    def lock_end(self):
        if self.end:
            self.end_locked = True
            self.update_total()

    def unlock_start(self):
        self.start_locked = False

    def unlock_end(self):
        self.end_locked = False

class MileageApp(App):
    def build(self):
        return MileageLayout()

if __name__ == "__main__":
    MileageApp().run()
    
