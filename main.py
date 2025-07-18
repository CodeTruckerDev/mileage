from kivy.config import Config
Config.set('graphics', 'width', '360')
Config.set('graphics', 'height', '800')

import sqlite3
import os
from datetime import datetime
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
from kivy.core.window import Window
from kivy.clock import Clock
from collections import OrderedDict

# -----------------------------
# Klasa do obsługi bazy danych SQLite
# -----------------------------
class MileageDB:
    def __init__(self, db_path="mileage.db"):
        self.conn = sqlite3.connect(db_path)
        self.cursor = self.conn.cursor()
        self._create_table()

    def _create_table(self):
        # Tworzy tabelę, jeśli nie istnieje: kolumny to miesiąc (klucz), przebieg, delegacje
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS mileage (
                month TEXT PRIMARY KEY,
                mileage INTEGER,
                delegations INTEGER
            )
        """)
        self.conn.commit()

    def save_month_data(self, month: str, mileage: int, delegations: int):
        # Wstawia lub aktualizuje dane dla danego miesiąca      
        self.cursor.execute("""
            INSERT OR REPLACE INTO mileage (month, mileage, delegations)
            VALUES (?, ?, ?)
        """, (month, mileage, delegations))
        self.conn.commit()

    def get_month_data(self, month: str):
        # Zwraca dane (mileage, delegations) dla danego miesiąca jako krotkę
        self.cursor.execute("SELECT mileage, delegations FROM mileage WHERE month = ?", (month,))
        row = self.cursor.fetchone()
        return row if row else (0, 0)

    def get_all_months(self):
        # Zwraca listę wszystkich miesięcy zapisanych w bazie
        self.cursor.execute("SELECT month FROM mileage ORDER BY month DESC")
        return [row[0] for row in self.cursor.fetchall()]


# -----------------------------
# Główna klasa layoutu aplikacji
# -----------------------------    
class MileageLayout(BoxLayout):

    # Właściwości dynamiczne – automatycznie aktualizują UI
    current_month = StringProperty()
    start = StringProperty("")
    end = StringProperty("")
    deleg = NumericProperty(0)
    total = NumericProperty(0)
    total_daily = NumericProperty(0)
    d_counter = NumericProperty(0)
    start_locked = BooleanProperty(False)
    end_locked = BooleanProperty(False)
    deleg_locked = BooleanProperty(False)
    warning_text = StringProperty("")
    selected_month_key = StringProperty(datetime.now().strftime("%Y-%m"))
    selected_month_display = StringProperty(datetime.now().strftime("%B %Y"))

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.db = MileageDB()
        self.current_month = datetime.now().strftime("%B    %Y")
        self.start = ""
        self.end = ""
        mileage, delegations = self.db.get_month_data(self.selected_month_key)
        self.d_counter = delegations
        self.update_total()
        self.update_confirm_button_state()

    def set_selected_month(self, month_key):
        months_pl = {
            'January': 'Styczeń',
            'February': 'Luty',
            'March': 'Marzec',
            'April': 'Kwiecień',
            'May': 'Maj',
            'June': 'Czerwiec',
            'July': 'Lipiec',
            'August': 'Sierpień',
            'September': 'Wrzesień',
            'October': 'Październik',
            'November': 'Listopad',
            'December': 'Grudzień'
        }
        
        self.selected_month_key = month_key
        dt = datetime.strptime(month_key, "%Y-%m")
        month_en = dt.strftime("%B")
        month_pl = months_pl.get(month_en, month_en)
        self.selected_month_display = f"{month_pl} {dt.year}"

        data = self.db.get_month_data(month_key)
        if data:
            self.start = str(data[0])
            self.end = str(data[1])
            self.d_counter = data[2]
            self.update_total()

        self.start_locked = True
        self.update_confirm_button_state()
    
    def update_confirm_button_state(self):
        # 🔽 Tu dodajemy blok zarządzający przyciskiem zapisu
        is_current = (self.selected_month_key == datetime.now().strftime("%Y-%m"))
        self.set_editable_state(is_current)

        confirm_button = self.ids.confirm_button
        if is_current:
            self.set_buttons_enabled(True)
            confirm_button.text = "Zapisz i wyjdź"
        else:
            self.set_buttons_enabled(False)
            confirm_button.text = "Edycja zablokowana"

        
    def set_editable_state(self, editable):
        # Funkcja zmienia stan pól w zależności od miesiąca
        self.ids.start_input.disabled = not editable
        self.ids.end_input.disabled = not editable
        self.ids.deleg_input.disabled = not editable

    def set_buttons_enabled(self, enabled: bool):
        #  Blokuje lub odblokowuje wszystkie przyciski w zależności od wybranego miesiąca
        self.ids.start_button.disabled = not enabled
        self.ids.end_button.disabled = not enabled
        self.ids.deleg_button.disabled = not enabled
        self.ids.confirm_button.disabled = not enabled

    def show_month_selector(self):
        # Pokazuje popup z listą zapisanych miesięcy
        available_months = list(OrderedDict.fromkeys(self.db.get_all_months()))
        layout = GridLayout(cols=1, spacing=10, size_hint_y=None)
        layout.bind(minimum_height=layout.setter('height'))

        for month in available_months:
            btn = Button(text=month, size_hint_y=None, height=80)
            btn.bind(on_release=lambda btn: self.select_month(btn.text))
            layout.add_widget(btn)

        scroll = ScrollView(size_hint=(1, 1))
        scroll.add_widget(layout)

        self.popup = Popup(title="Wybierz miesiąc", content=scroll,
                           size_hint=(0.8, 0.8), auto_dismiss=True)
        self.popup.open()

    def select_month(self, month_key):
        # Wybiera miesiąc z popupu i aktualizuje dane
        self.selected_month_key = month_key
        data = self.db.get_month_data(month_key)
        self.total = data[0]
        self.d_counter = data[1]
        try:
            date_obj = datetime.strptime(month_key, "%Y-%m")
            self.selected_month_display = date_obj.strftime("%B %Y")
            self.popup.dismiss()
            self.update_confirm_button_state()
        except ValueError:
            self.selected_month_display = month_key

    def update_start(self, text):
        # Aktualizuje pole "start" przebiegu
        if text.isdigit() and text != self.start:
            if not self.start_locked:
                self.start = text[:7]

    def update_end(self, text):
        # Aktualizuje pole "end" przebiegu i oblicza przebieg
        if self.start_locked and text.isdigit():
            end_value = int(text[:7])
            try:
                start_value = int(self.start)
            except ValueError:
                return

            if end_value > start_value:
                self.end = str(end_value)
                self.warning_text = ""
                self.total_daily = end_value - start_value
                db_mileage, _ = self.db.get_month_data(self.selected_month_key)
                self.total = db_mileage + self.total_daily
            else:
                self.warning_text = "Wartość końcowa  >  wartość początkowa"

    def update_deleg(self, text):
        # Aktualizuje pole ilości delegacji
        if not self.deleg_locked and text.isdigit():
            self.deleg = int(text[:3])

    def update_total(self):
        # Aktualizuje przebieg całkowity
        try:
            db_mileage, _ = self.db.get_month_data(self.selected_month_key)
            self.total = db_mileage + self.total_daily
        except ValueError:
            pass

    def save(self):
        # Zapisuje dane do bazy i zamyka aplikację po 5 sekundach
        self.d_counter += self.deleg
        self.db.save_month_data(self.selected_month_key, self.total, self.d_counter)
        self.ids.confirm_button.disabled = True  # blokuje przycisk od razu
        Clock.schedule_once(self.closing, 5)

    def lock_start(self):
        # Blokuje pole początkowe
        if self.start:
            self.start_locked = True
            self.update_total()

    def lock_end(self):
        # Blokuje pole końcowe
        if self.end:
            self.end_locked = True
            self.update_total()

    def lock_deleg(self):
        # Blokuje pole delegacji
        self.deleg_locked = True

    def unlock_start(self):
        # Odblokowuje pole początkowe
        self.start_locked = False

    def unlock_end(self):
        # Odblokowuje pole końcowe
        self.end_locked = False

    def unlock_deleg(self):
        # Odblokowuje pole delegacji
        self.deleg_locked = False

    def closing(self, *args):
        # Zamyka okno aplikacji
        Window.close()

# -----------------------------
# Główna klasa aplikacji
# -----------------------------
class MileageApp(App):
    def build(self):
        root = FloatLayout()

        # ustal ścieżkę do tła w folderze assets/
        background_path = os.path.join(os.path.dirname(__file__), 'assets', 'dusk2_cropped.jpg')

        # ustawienie tła dla aplikacji. Obraz w tej samej lokacji co main.py
        background = Image(
            source=background_path,
            allow_stretch=True,
            keep_ratio=False,
            size_hint=(1, 1),
            pos_hint={'x': 0, 'y': 0}
        )
        root.add_widget(background)

        content = MileageLayout()
        root.add_widget(content)

        return root

if __name__ == "__main__":
    MileageApp().run()
