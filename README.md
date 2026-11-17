# Mastermind

Gra logiczna w terminalu, napisana w Pythonie z interfejsem Textual.
Odgadnij czterocyfrowy kod w maksymalnie 10 próbach.

## Wymagania

- Python 3.10 lub nowszy, z modułami `pip` i `venv`.
- Git do pobrania projektu.
- Terminal na macOS, Linux lub Windows.

## Pobranie z GitHuba

Otwórz terminal w katalogu, w którym chcesz zapisać projekt:

```bash
git clone --branch js-ui https://github.com/stochajkubaa/mastermind_pp.git
cd mastermind_pp
```

Instrukcja zakłada, że branch `js-ui` został już opublikowany na GitHubie.
Jeśli Git zgłasza, że branch nie istnieje, autor musi najpierw go opublikować.

Możesz też otworzyć [repozytorium na GitHubie](https://github.com/stochajkubaa/mastermind_pp),
wybrać branch `js-ui`, kliknąć **Code → Download ZIP** i rozpakować archiwum.
Następnie otwórz terminal w rozpakowanym katalogu z plikiem `main.py`.

## Instalacja i pierwsze uruchomienie

### macOS i Linux

W katalogu projektu wykonaj:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install "textual>=8,<9"
python main.py
```

### Windows — PowerShell lub Wiersz polecenia

W katalogu projektu wykonaj:

```powershell
py -3 -m venv .venv
.venv\Scripts\python.exe -m pip install "textual>=8,<9"
.venv\Scripts\python.exe main.py
```

Nie trzeba aktywować środowiska ani zmieniać ustawień PowerShella.
Jeśli polecenie `py` nie jest dostępne, użyj `python` zamiast `py -3`.

## Kolejne uruchomienia

Otwórz terminal w katalogu projektu. Bibliotekę instalujesz tylko raz.

macOS i Linux:

```bash
.venv/bin/python main.py
```

Windows:

```powershell
.venv\Scripts\python.exe main.py
```

## Jak grać

1. Wybierz poziom i naciśnij **Rozpocznij grę**.
2. Wpisz dokładnie 4 cyfry bez spacji i zatwierdź Enterem lub przyciskiem **Sprawdź kod**.
3. Korzystaj z historii prób i ocen, aby odgadnąć kod.

- **Łatwy:** cyfry od 0 do 3.
- **Trudny:** cyfry od 0 do 9.
- Cyfry mogą się powtarzać; kod może zaczynać się od zera.
- **● Miejsce:** ilość cyfr na właściwej pozycji.
- **○ Cyfra:** ilość poprawnych cyfr na złej pozycji.

Masz 10 prób. Po zakończeniu rozgrywki zobaczysz tajny kod i możesz rozpocząć nową grę.

## Sterowanie

| Klawisz | Działanie |
| --- | --- |
| Enter | Zatwierdzenie kodu lub aktywacja wybranego przycisku |
| Tab / Shift+Tab | Przejście między elementami interfejsu |
| Strzałki / Spacja | Wybór poziomu trudności w polu wyboru |
| Ctrl+N | Nowa gra |
| Esc | Powrót do wyboru trybu; anulowanie okna potwierdzenia |
| Ctrl+Q | Zakończenie programu |

Możesz również używać myszy. W małym terminalu przewijaj widok, aby zobaczyć całą historię i opisy.

## Pliki projektu

- `main.py` — interfejs i obsługa rozgrywki.
- `main.tcss` — wygląd interfejsu; musi znajdować się obok `main.py`.
- `silnik.py` — generowanie tajnego kodu.
- `ocena.py` — ocenianie prób.
