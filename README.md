# Mileage – Rejestr przebiegu i delegacji

**Mileage** to minimalistyczna aplikacja do zapisywania pokonanych kilometrów tras oraz delegacji służbowych w ujęciu miesięcznym. Idealna do użytku prywatnego, bez potrzeby logowania ani połączenia z internetem.

## Funkcje

* Ręczne wprowadzanie początku i końca trasy
* Blokowanie pól po wpisaniu danych, wymuszające świadome potwierdzenie wpisu
* Zliczanie przebiegu miesięcznego oraz delegacji
* Pamięć ostatniego wpisu – po uruchomieniu aplikacja pokazuje datę wpisu, kilometry i delegacje z ostatnio zapisanej trasy
* Przegląd zapisanych miesięcy z trybem podglądu – dane historyczne są tylko do odczytu, edycja możliwa wyłącznie w miesiącu bieżącym
* Przycisk dolny zmienia tryb zależnie od kontekstu: zwykłe wyjście, dopóki wpis nie zostanie potwierdzony, oraz zapis i wyjście po zablokowaniu wszystkich pól
* Zapis danych do lokalnej bazy SQLite
* Tło aplikacji z grafiką drogi
* Interfejs zoptymalizowany pod ekran dotykowy (Samsung A56)

## Zrzut ekranu aplikacji

*Widok główny aplikacji – z wprowadzonymi danymi przykładowymi. Wersja uruchomiona na komputerze*

[![Image](https://github.com/CodeTruckerDev/mileage/raw/main/mileage_1.0.png)](/CodeTruckerDev/mileage/blob/main/mileage_1.0.png)

Zrzut wykonany na moim telefonie — żeby było widać, że to nie tylko kod, ale realna aplikacja, którą da się uruchomić

[![Image](https://github.com/CodeTruckerDev/mileage/raw/main/mileage_mobile.png)](/CodeTruckerDev/mileage/blob/main/mileage_mobile.png)

## Architektura

Warstwa danych jest oddzielona od interfejsu. Cała obsługa bazy SQLite mieszka w `database.py`, logika i interfejs Kivy w `main.py`, a układ ekranu w `mileage.kv`. Takie rozdzielenie ułatwia testowanie i ewentualne przyszłe integracje, na przykład eksport logów osobnym skryptem.

## Struktura danych

Baza składa się z dwóch tabel. Tabela `mileage` przechowuje narastające sumy miesięczne, a tabela `entries` zapisuje pojedyncze wpisy tras z datą, co pozwala odtworzyć ostatni wpis po ponownym uruchomieniu aplikacji.

### Tabela `mileage`

| Kolumna | Typ danych | Opis |
| --- | --- | --- |
| `month` | TEXT | Miesiąc w formacie `YYYY-MM` (klucz główny) |
| `mileage` | INTEGER | Sumaryczny przebieg miesięczny |
| `delegations` | INTEGER | Liczba delegacji w danym miesiącu |

### Tabela `entries`

| Kolumna | Typ danych | Opis |
| --- | --- | --- |
| `id` | INTEGER | Klucz główny, autoinkrementacja |
| `month` | TEXT | Miesiąc w formacie `YYYY-MM` |
| `date` | TEXT | Data wpisu w formacie `dd.mm` |
| `km` | INTEGER | Kilometry pojedynczej trasy |
| `delegations` | INTEGER | Liczba delegacji w danym wpisie |

## Instalacja

Skopiuj pliki `main.py`, `database.py`, `mileage.kv` oraz grafikę tła `dusk2_cropped.jpg` (w katalogu `assets/`).

Uruchom przez:

```
python main.py
```

## Zasilenie bazy danymi historycznymi

Plik `database.py` zawiera zakomentowaną metodę `seed_historical_data`, służącą do ręcznego wpisania danych historycznych przed zbudowaniem APK. Format krotki to `(rok, miesiąc, km, delegacje)`, a klucz miesiąca składany jest automatycznie do formatu `RRRR-MM`. Seed zasila wyłącznie tabelę sum miesięcznych – dla starych miesięcy nie znamy pojedynczych tras, więc dziennik wpisów pozostaje pusty i zapełnia się dopiero przy bieżącym użytkowaniu.

## Historia zmian

### Wersja 1.2

* Trzy stany przycisku dolnego: zwykłe wyjście w trybie podglądu miesięcy historycznych, wyjście bez zapisu gdy pola nie są jeszcze potwierdzone, zapis i wyjście po zablokowaniu wszystkich trzech pól
* Strażnik w metodzie zapisu – decyduje stan aplikacji, nie etykieta przycisku, co chroni przed przypadkowym zapisem
* Naprawa błędu: pole "Razem" aktualizowało się już przy blokowaniu drugiego pola, zanim wpis został zapisany. Teraz "Razem" odzwierciedla wyłącznie stan zapisany w bazie i zmienia się dopiero po kliknięciu "Zapisz i wyjdz"
* Reset blokad przy zmianie miesiąca – świeży stan dla każdego widoku
* Stonowane kolory tła pól (mniej jaskrawe odcienie) oraz biały tekst dla lepszej czytelności
* Skrócenie czasu zamknięcia aplikacji z 5 do 2 sekund
* Czyste zamykanie przez `App.stop()` zamiast `Window.close()`

### Wersja 1.1

* Pamięć ostatniego wpisu – nowa tabela `entries` w bazie SQLite, przechowująca pojedyncze wpisy tras z datą
* Po uruchomieniu aplikacja pokazuje informację o ostatnim zapisanym wpisie dla bieżącego miesiąca
* Wydzielenie warstwy danych do osobnego modułu `database.py`
* Naprawa logiki czyszczenia pól – wartości zmiennych poprawnie reagują na opróżnienie pól tekstowych

### Wersja 1.0

* Pierwsza wersja aplikacji – wprowadzanie przebiegu początkowego, końcowego oraz delegacji
* Zliczanie sum miesięcznych w tabeli `mileage`
* Przegląd zapisanych miesięcy
* Build APK dla Androida (arm64-v8a)

## Pobierz aplikację

[mileage-v1.2.apk](https://github.com/CodeTruckerDev/mileage/releases/download/ver1_2/mileage-1.2-arm64-v8a-debug.apk)

> Plik APK możesz zainstalować bezpośrednio na telefonie (pamiętaj o włączeniu instalacji z nieznanych źródeł).

## Źródła grafiki

* Obraz tła: `dusk2_cropped.jpg` ([źródło](https://www.freepik.com/free-ai-image/truck-logistics-operation-dusk_186747654.htm))
* Ikona aplikacji: `icon.png` ([źródło](https://icons8.com/icon/BCKJ34JwI3Bs/truck) – Truck icon by Icons8.com)

---

## License

This project is licensed under the MIT License - see the [LICENSE](https://github.com/CodeTruckerDev/mileage/blob/main/LICENSE) file.

**Attribution appreciated:** If you use this code, a link back to this repo
would be awesome (but not required). It helps other developers find the original
work and supports independent creators like me.

---

## Pomysły na przyszłość

* Sekwencyjne wprowadzanie danych z automatycznym przenoszeniem fokusu między polami
* Tryb „aplikacja główna” dla floty lub zespołu
* Eksport danych do pliku lub serwera
* Powiadomienia o braku wpisów pod koniec miesiąca

