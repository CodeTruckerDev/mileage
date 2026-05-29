from kivy.config import Config
Config.set('graphics', 'width', '360')
Config.set('graphics', 'height', '800')

import os
from datetime import datetime
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.popup import Popup
from kivy.uix.scrollview import ScrollView
from kivy.uix.gridlayout import GridLayout
from kivy.uix.image import Image
from kivy.uix.button import Button
from kivy.properties import StringProperty, NumericProperty, BooleanProperty
from kivy.clock import Clock
from collections import OrderedDict

from database import MileageDB


# -----------------------------
# Główna klasa layoutu aplikacji
# -----------------------------
class MileageLayout(BoxLayout):

    # Właściwosci dynamiczne - automatycznie aktualizuja UI
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
    last_entry_text = StringProperty("")
    selected_month_key = StringProperty(datetime.now().strftime("%Y-%m"))
    selected_month_display = StringProperty(datetime.now().strftime("%B %Y"))

    MONTHS_PL = {
        'January': 'Styczeń', 'February': 'Luty', 'March': 'Marzec',
        'April': 'Kwiecień', 'May': 'Maj', 'June': 'Czerwiec',
        'July': 'Lipiec', 'August': 'Sierpień', 'September': 'Wrzesień',
        'October': 'Październik', 'November': 'Listopad', 'December': 'Grudzień'
    }

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.db = MileageDB()
        self.start = ""
        self.end = ""
        # Jawne ustawienie sumy z bazy dla bieżącego miesiąca
        mileage, delegations = self.db.get_month_data(self.selected_month_key)
        self.total = mileage
        self.d_counter = delegations
        self.total_daily = 0
        self.selected_month_display = self._format_month(self.selected_month_key)
        self.refresh_last_entry()
        Clock.schedule_once(lambda dt: self.apply_month_view_mode(), 0)

    def _format_month(self, month_key):
        # Składa czytelny opis miesiąca w języku polskim, np. "Maj 2025"
        dt = datetime.strptime(month_key, "%Y-%m")
        month_en = dt.strftime("%B")
        month_pl = self.MONTHS_PL.get(month_en, month_en)
        return f"{month_pl} {dt.year}"

    def refresh_last_entry(self):
        # Czyta ostatni wpis trasy z dziennika dla bieżącego miesiąca
        last = self.db.get_last_entry(self.selected_month_key)
        if last:
            date, km, deleg = last
            self.last_entry_text = f"Ostatnio: {date} - {km} km, {deleg} deleg."
        else:
            self.last_entry_text = "Ostatnio: brak wpisow"

    def refresh_button_state(self):
        # Ustala etykietę przycisku na podstawie dwóch warunków:
        # 1) czy wybrany miesiąc jest bieżący
        # 2) czy wszystkie trzy pola są zablokowane (potwierdzone)
        # Przycisk jest zawsze aktywny - tryb wyjścia jest domyślny, zapis tylko gdy oba warunki spełnione.
        is_current = (self.selected_month_key == datetime.now().strftime("%Y-%m"))
        all_locked = self.start_locked and self.end_locked and self.deleg_locked

        confirm_button = self.ids.confirm_button
        if is_current and all_locked:
            confirm_button.text = "Zapisz i wyjdź"
        else:
            confirm_button.text = "Wyjdź"

    def apply_month_view_mode(self):
        # Pola i przyciski lock/unlock aktywne tylko w bieżącym miesiącu.
        # Przycisk dolny zostaje zawsze aktywny - jego tryb steruje refresh_button_state.
        is_current = (self.selected_month_key == datetime.now().strftime("%Y-%m"))
        self.ids.start_input.disabled = not is_current
        self.ids.end_input.disabled = not is_current
        self.ids.deleg_input.disabled = not is_current
        self.ids.start_button.disabled = not is_current
        self.ids.end_button.disabled = not is_current
        self.ids.deleg_button.disabled = not is_current
        self.refresh_button_state()

    def show_month_selector(self):
        # Pokazuje popup z listą zapisanych miesięcy
        available_months = list(OrderedDict.fromkeys(self.db.get_all_months()))
        layout = GridLayout(cols=1, spacing=10, size_hint_y=None)
        layout.bind(minimum_height=layout.setter('height'))

        for month in available_months:
            btn = Button(text=month, size_hint_y=None, height=80)
            btn.bind(on_release=lambda b: self.select_month(b.text))
            layout.add_widget(btn)

        scroll = ScrollView(size_hint=(1, 1))
        scroll.add_widget(layout)

        self.popup = Popup(title="Wybierz miesiąc", content=scroll,
                           size_hint=(0.8, 0.8), auto_dismiss=True)
        self.popup.open()

    def select_month(self, month_key):
        # Wybiera miesiąc z popupu i aktualizuje dane
        self.selected_month_key = month_key
        mileage, delegations = self.db.get_month_data(month_key)
        self.total = mileage
        self.d_counter = delegations
        self.total_daily = 0
        self.start = ""
        self.end = ""
        self.deleg = 0
        self.warning_text = ""
        # Reset blokad przy zmianie miesiąca - świeży stan dla nowego widoku
        self.start_locked = False
        self.end_locked = False
        self.deleg_locked = False
        try:
            self.selected_month_display = self._format_month(month_key)
        except ValueError:
            self.selected_month_display = month_key
        self.refresh_last_entry()
        if hasattr(self, 'popup'):
            self.popup.dismiss()
        self.apply_month_view_mode()

    def update_start(self, text):
        # Aktualizuje pole "start" przebiegu; czyści zmienna gdy pole puste
        if self.start_locked:
            return
        if text == "":
            self.start = ""
        elif text.isdigit():
            self.start = text[:7]

    def update_end(self, text):
        # Aktualizuje pole "end" przebiegu i przelicza trasę dzienną.
        # UWAGA: self.total (Razem) NIE jest tu ruszane - aktualizuje się tylko po realnym zapisie.
        if text == "":
            self.end = ""
            self.total_daily = 0
            self.warning_text = ""
            return

        if not text.isdigit():
            return

        try:
            start_value = int(self.start)
        except ValueError:
            # brak poprawnej wartości początkowej - nie liczymy jeszcze trasy
            self.end = text[:7]
            return

        end_value = int(text[:7])
        if end_value > start_value:
            self.end = str(end_value)
            self.warning_text = ""
            self.total_daily = end_value - start_value
        else:
            self.end = str(end_value)
            self.total_daily = 0
            self.warning_text = "Wartość końcowa  >  wartość początkowa"

    def update_deleg(self, text):
        # Aktualizuje pole ilości delegacji; czyści gdy puste
        if self.deleg_locked:
            return
        if text == "":
            self.deleg = 0
        elif text.isdigit():
            self.deleg = int(text[:3])

    def save(self):
        # Tryb wyjścia: brak zapisu jeśli miesiąc historyczny lub pola niezablokowane.
        # Decyduje stan, nie etykieta - to chroni przed zapisem śmiecia nawet gdyby
        # przycisk pokazywał "Zapisz i wyjdź" przez przypadek.
        is_current = (self.selected_month_key == datetime.now().strftime("%Y-%m"))
        all_locked = self.start_locked and self.end_locked and self.deleg_locked
        if not (is_current and all_locked):
            self.closing()
            return

        # Zapisuje do obu tabel: dzienny wpis do entries + narastająca suma do mileage.
        # Dopiero tutaj liczymy nowe "Razem" - wcześniej self.total trzymało stan z bazy.
        today = datetime.now().strftime("%d.%m")
        new_total = self.total + self.total_daily
        self.d_counter += self.deleg

        # 1) Wpis dzienny do dziennika (km = trasa dzienna, nie suma)
        self.db.add_entry(self.selected_month_key, today, self.total_daily, self.deleg)
        # 2) Aktualizacja narastającej sumy miesięcznej
        self.db.save_month_data(self.selected_month_key, new_total, self.d_counter)
        # 3) Odświeżenie UI - przez 2s podglądu zobaczymy nowe "Razem" przed zamknięciem
        self.total = new_total

        self.ids.confirm_button.disabled = True  # blokuje przycisk od razu
        Clock.schedule_once(self.closing, 2)

    def lock_start(self):
        # Blokuje pole początkowe
        if self.start:
            self.start_locked = True
            self.refresh_button_state()

    def lock_end(self):
        # Blokuje pole końcowe
        if self.end:
            self.end_locked = True
            self.refresh_button_state()

    def lock_deleg(self):
        # Blokuje pole delegacji
        self.deleg_locked = True
        self.refresh_button_state()

    def unlock_start(self):
        # Odblokowuje pole początkowe
        self.start_locked = False
        self.refresh_button_state()

    def unlock_end(self):
        # Odblokowuje pole końcowe
        self.end_locked = False
        self.refresh_button_state()

    def unlock_deleg(self):
        # Odblokowuje pole delegacji
        self.deleg_locked = False
        self.refresh_button_state()

    def closing(self, *args):
        # Zamyka aplikację poprawnie i domyka połączenie z bazą
        self.db.close()
        App.get_running_app().stop()


# -----------------------------
# Główna klasa aplikacji
# -----------------------------
class MileageApp(App):
    def build(self):
        root = FloatLayout()

        # ustal ścieżkę do tła w folderze assets/
        background_path = os.path.join(os.path.dirname(__file__), 'assets', 'dusk2_cropped.jpg')

        # ustawienie tła dla aplikacji
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


