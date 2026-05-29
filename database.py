"""
Moduł warstwy danych (Data Access Layer) dla aplikacji Mileage.
Odpowiada za całą komunikację z bazą SQLite.
Oddzielenie tego od głównego kodu Kivy ułatwia testowanie i ewentualne
przyszłe integracje (np. eksportowanie logów do CSV przez osobny skrypt).
"""
import sqlite3


class MileageDB:
    """
    Klasa zarzadzająca połączeniem i operacjami na lokalnej bazie SQLite.

    Dwie tabele:
      - mileage: agregaty miesięczne (klucz glowny to YYYY-MM)
      - entries: pojedyncze wpisy tras z datą, do pamiętania ostatniego wpisu
    """

    def __init__(self, db_path="mileage.db"):
        self.conn = sqlite3.connect(db_path)
        self.cursor = self.conn.cursor()
        self._create_tables()

    def _create_tables(self):
        """Inicjalizuje strukturę bazy: agregaty miesięczne oraz dziennik wpisów."""
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS mileage (
                month TEXT PRIMARY KEY,
                mileage INTEGER,
                delegations INTEGER
            )
        """)
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS entries (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                month TEXT,
                date TEXT,
                km INTEGER,
                delegations INTEGER
            )
        """)
        self.conn.commit()

    def save_month_data(self, month: str, mileage: int, delegations: int):
        """Nadpisuje lub tworzy wpis z sumarycznym przebiegiem i delegacjami dla podanego miesiąca."""
        self.cursor.execute("""
            INSERT OR REPLACE INTO mileage (month, mileage, delegations)
            VALUES (?, ?, ?)
        """, (month, mileage, delegations))
        self.conn.commit()

    def get_month_data(self, month: str):
        """Zwraca krotkę (mileage, delegations) dla danego miesiąca lub (0, 0) jeśli brak wpisu."""
        self.cursor.execute("SELECT mileage, delegations FROM mileage WHERE month = ?", (month,))
        row = self.cursor.fetchone()
        return row if row else (0, 0)

    def get_all_months(self):
        """Pobiera listę wszystkich zapisanych miesięcy (np. do zasilenia listy wyboru w interfejsie)."""
        self.cursor.execute("SELECT month FROM mileage ORDER BY month DESC")
        return [row[0] for row in self.cursor.fetchall()]

    def add_entry(self, month: str, date: str, km: int, delegations: int):
        """Dopisuje pojedynczy wpis dziennej trasy do dziennika wpisów."""
        self.cursor.execute("""
            INSERT INTO entries (month, date, km, delegations)
            VALUES (?, ?, ?, ?)
        """, (month, date, km, delegations))
        self.conn.commit()

    def get_last_entry(self, month: str):
        """Zwraca ostatni wpis (date, km, delegations) dla danego miesiąca lub None."""
        self.cursor.execute("""
            SELECT date, km, delegations FROM entries
            WHERE month = ? ORDER BY id DESC LIMIT 1
        """, (month,))
        return self.cursor.fetchone()

    def close(self):
        """Zamyka połączenie z bazą."""
        self.conn.close()

    # -----------------------------------------------------------------
    # SEED HISTORYCZNY
    # -----------------------------------------------------------------
    # Wpisz tutaj dane historyczne RĘCZNIE przed zbudowaniem APK.
    # Format krotki: (rok, miesiąc, km, delegacje)
    # Klucz miesiąca składany jest automatycznie do formatu "RRRR-MM".
    # Seed zasila TYLKO tabele sum miesięcznych (mileage) - dla starych
    # miesiecy nie znamy pojedynczych tras, wiec dziennik wpisów (entries)
    # zostaje pusty i zapełnia się dopiero przy bieżącym użytkowaniu apki.
    #
    # Aby zasiać bazę: odpal ten plik bezpośrednio (python3 database.py).
    # -----------------------------------------------------------------
    # def seed_historical_data(self):
    #    historical = [
    #        # (rok, miesiąc, km, delegacje)
    #        (2025, 1, 0, 0),
    #        (2025, 2, 0, 0),
    #        (2025, 3, 0, 0),
    #        # ... dopisuj kolejne wpisy według wzoru powyżej
    #    ]
    #    for year, month, km, deleg in historical:
    #        month_key = f"{year:04d}-{month:02d}"
    #        self.save_month_data(month_key, km, deleg)


if __name__ == "__main__":
    # Ręczne zasianie bazy danymi historycznymi
    db = MileageDB()
    # db.seed_historical_data()   # w przypadku ręcznego uzupełnienia bazy danych
    db.close()
    # print("Baza zasiana danymi historycznymi.")
