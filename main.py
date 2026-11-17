"""Interfejs Mastermind. Uruchom: python main.py (wymaga Textual 8.x)."""

import ocena
import silnik
from rich.text import Text
from textual import on
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, Vertical, VerticalScroll
from textual.events import Resize
from textual.screen import ModalScreen, Screen
from textual.widgets import Button, DataTable, Footer, Input, RadioButton, RadioSet, Static

DLUGOSC_KODU = 4
# Moduły kolegów nie narzucają limitu. Jest to konfiguracja rozgrywki w UI.
MAKS_PROB = 10
TRYBY = {"easy": ("Łatwy", 3), "hard": ("Trudny", 9)}


def odczytaj_probe(tekst: str, maks_cyfra: int) -> list[int]:
    """Walidacja wejścia; generowanie i ocenianie pozostają w osobnych modułach."""
    if not tekst.strip():
        raise ValueError("Wpisz kod, zanim go sprawdzisz.")
    if len(tekst) != DLUGOSC_KODU:
        raise ValueError(f"Kod musi mieć dokładnie {DLUGOSC_KODU} cyfry, bez spacji.")
    if any(znak not in "0123456789" for znak in tekst):
        raise ValueError("Użyj wyłącznie cyfr 0–9, bez spacji i innych znaków.")
    cyfry = [int(znak) for znak in tekst]
    if any(cyfra > maks_cyfra for cyfra in cyfry):
        raise ValueError(f"W tym trybie dozwolone są tylko cyfry od 0 do {maks_cyfra}.")
    return cyfry


class EkranStartowy(Screen):
    def compose(self) -> ComposeResult:
        with VerticalScroll(id="start-scroll"):
            with Vertical(id="start-card"):
                yield Static("GRA LOGICZNA / 01", classes="eyebrow")
                yield Static("MASTERMIND", id="start-title")
                yield Static("Cztery cyfry. Jeden ukryty kod.", id="start-subtitle")
                yield Static("?    ?    ?    ?", id="start-secret")
                yield Static(
                    f"Odkryj kod w {MAKS_PROB} próbach. Cyfry mogą się powtarzać, "
                    "a zero może być pierwszą cyfrą.", classes="description"
                )
                yield Static("● Miejsce — cyfra na właściwej pozycji.", classes="exact legend")
                yield Static("○ Cyfra — dobra cyfra, ale na innej pozycji.", classes="misplaced legend")
                yield Static(
                    "Wyniki to liczby trafień, nie wskazówki dla konkretnych pól.",
                    classes="muted description"
                )
                yield Static("WYBIERZ POZIOM", classes="eyebrow section-label")
                with RadioSet(id="difficulty"):
                    yield RadioButton("Łatwy · cyfry 0–3", value=True, id="easy")
                    yield RadioButton("Trudny · cyfry 0–9", id="hard")
                with Horizontal(classes="actions"):
                    yield Button("Rozpocznij grę", variant="primary", id="start")
                    yield Button("Wyjdź", id="exit")
        yield Footer()

    def on_mount(self) -> None:
        self.query_one("#start", Button).focus()

    @on(Button.Pressed, "#start")
    def rozpocznij(self) -> None:
        wybor = self.query_one(RadioSet).pressed_button
        self.app.switch_screen(EkranGry(wybor.id if wybor else "easy"))

    @on(Button.Pressed, "#exit")
    def wyjdz(self) -> None:
        self.app.exit()


class Potwierdzenie(ModalScreen[bool]):
    """Chroni rozpoczętą rozgrywkę przed przypadkowym wyczyszczeniem."""

    BINDINGS = [Binding("escape", "anuluj", "Anuluj")]

    def compose(self) -> ComposeResult:
        with VerticalScroll(id="confirm"):
            yield Static("Zakończyć tę rozgrywkę?", classes="panel-title")
            yield Static("Bieżący kod i historia prób zostaną utracone.", classes="description")
            with Horizontal(classes="actions"):
                yield Button("Wróć do gry", id="cancel", variant="primary")
                yield Button("Zakończ grę", id="confirm-end")

    def on_mount(self) -> None:
        self.query_one("#cancel", Button).focus()

    def action_anuluj(self) -> None:
        self.dismiss(False)

    @on(Button.Pressed)
    def odpowiedz(self, event: Button.Pressed) -> None:
        self.dismiss(event.button.id == "confirm-end")


class EkranGry(Screen):
    BINDINGS = [
        Binding("ctrl+n", "nowa_gra", "Nowa gra"),
        Binding("escape", "menu", "Tryby"),
    ]

    def __init__(self, tryb: str = "easy") -> None:
        super().__init__()
        self.tryb = tryb
        self.nazwa_trybu, self.maks_cyfra = TRYBY[tryb]
        self._kod = (silnik.generuj_kod_easy() if tryb == "easy"
                     else silnik.generuj_kod_hard())
        self.liczba_prob = 0
        self.aktywna = True
        self._sprawdzanie = False

    def compose(self) -> ComposeResult:
        with Horizontal(id="game-header"):
            yield Static("MASTERMIND", id="brand")
            yield Static(f"{self.nazwa_trybu} / 0–{self.maks_cyfra}", id="mode-badge")
        with VerticalScroll(id="game-scroll"):
            with Vertical(id="game-content"):
                with Horizontal(id="round-header"):
                    yield Static(f"PRÓBA 01 / {MAKS_PROB:02}", id="round", classes="eyebrow")
                    yield Static("?   ?   ?   ?", id="secret")
                with Horizontal(id="board"):
                    with Vertical(id="history-panel", classes="panel"):
                        yield Static("Historia prób", classes="panel-title")
                        yield Static("Zacznij od dowolnego kodu.", id="history-hint", classes="muted")
                        yield DataTable(id="history", zebra_stripes=True, cursor_type="row")
                        yield Static("● Właściwa pozycja   ○ Inna pozycja", id="table-legend", classes="muted")
                    with Vertical(id="control-panel", classes="panel"):
                        yield Static("Twój następny ruch", classes="panel-title")
                        yield Static(
                            f"Wpisz 4 cyfry od 0 do {self.maks_cyfra}.\nPowtórzenia są dozwolone.",
                            id="input-help", classes="muted"
                        )
                        yield Input(placeholder="np. 0123", id="guess")
                        yield Button("Sprawdź kod  ↵", id="submit", variant="primary", disabled=True)
                        yield Static("Gotowy na pierwszą próbę.", id="message", markup=False)
                        yield Static("JAK CZYTAĆ WYNIK", classes="eyebrow section-label")
                        yield Static("● Cyfra na właściwej pozycji.", classes="exact legend")
                        yield Static("○ Cyfra na innej pozycji.", classes="misplaced legend")
                        yield Static(
                            "Znaczniki podają tylko liczbę trafień. Każda cyfra jest liczona raz.",
                            classes="muted description"
                        )
                with Vertical(id="result", classes="panel"):
                    yield Static("", id="result-title", classes="panel-title")
                    yield Static("", id="result-detail", markup=False)
        with Horizontal(id="game-actions", classes="actions"):
            yield Button("Nowa gra", id="new-game")
            yield Button("Tryby", id="menu")
            yield Button("Wyjdź", id="exit")
        yield Footer()

    def on_mount(self) -> None:
        tabela = self.query_one(DataTable)
        tabela.add_column("#", width=2)
        tabela.add_column("Twój kod", width=9)
        tabela.add_column("● Miejsce", width=9)
        tabela.add_column("○ Cyfra", width=8)
        tabela.show_row_labels = False
        self.query_one("#result").display = False
        self.dostosuj_uklad(self.size.width)
        self.query_one(Input).focus()

    def on_resize(self, event: Resize) -> None:
        self.dostosuj_uklad(event.size.width)

    def dostosuj_uklad(self, szerokosc: int) -> None:
        self.set_class(szerokosc < 88, "narrow")
        self.set_class(szerokosc < 55, "small")
        if self.query("#board"):
            plansza = self.query_one("#board")
            panel = self.query_one("#control-panel" if szerokosc < 88 else "#history-panel")
            if plansza.children[0] is not panel:
                plansza.move_child(panel, before=0)

    @on(Input.Changed, "#guess")
    def zmiana_kodu(self, event: Input.Changed) -> None:
        self.query_one("#submit", Button).disabled = not self.aktywna or not bool(event.value)

    @on(Input.Submitted, "#guess")
    def zatwierdz_enterem(self, event: Input.Submitted) -> None:
        # Zignoruj zdarzenie czekające w kolejce po wyczyszczeniu pola.
        if event.value == self.query_one(Input).value:
            self.sprawdz_probe()

    @on(Button.Pressed, "#submit")
    def zatwierdz_przyciskiem(self, event: Button.Pressed) -> None:
        if not event.button.disabled:
            self.sprawdz_probe()

    def sprawdz_probe(self) -> None:
        if not self.aktywna or self._sprawdzanie:
            return
        pole = self.query_one(Input)
        komunikat = self.query_one("#message", Static)
        try:
            proba = odczytaj_probe(pole.value, self.maks_cyfra)
        except ValueError as blad:
            komunikat.update(str(blad))
            komunikat.add_class("error")
            pole.focus()
            komunikat.scroll_visible(animate=False)
            return

        self._sprawdzanie = True
        try:
            # Jedyne źródło oceny to funkcja kolegi; UI tylko prezentuje wynik.
            miejsca, cyfry = ocena.ocena(self._kod, proba)
            self.liczba_prob += 1
            tabela = self.query_one(DataTable)
            tabela.add_row(
                f"{self.liczba_prob:02}",
                Text(" ".join(map(str, proba)), style="bold #e4ecf5"),
                Text(f"● {miejsca}", style="#63dbc1"),
                Text(f"○ {cyfry}", style="#efc47a"),
            )
            tabela.move_cursor(row=self.liczba_prob - 1)
            self.query_one("#history-hint", Static).update(
                f"Zapisano prób: {self.liczba_prob} / {MAKS_PROB}."
            )
            komunikat.remove_class("error")
            komunikat.update(f"Na miejscu: {miejsca}. Na innej pozycji: {cyfry}.")
            pole.value = ""
            self.query_one("#submit", Button).disabled = True
            if miejsca == DLUGOSC_KODU:
                self.zakoncz_gre(wygrana=True)
            elif self.liczba_prob >= MAKS_PROB:
                self.zakoncz_gre(wygrana=False)
            else:
                self.query_one("#round", Static).update(
                    f"PRÓBA {self.liczba_prob + 1:02} / {MAKS_PROB:02}"
                )
                pole.focus()
        finally:
            self._sprawdzanie = False

    def zakoncz_gre(self, wygrana: bool) -> None:
        self.aktywna = False
        self.query_one(Input).disabled = True
        self.query_one("#submit", Button).disabled = True
        self.query_one("#round", Static).update(f"KONIEC / {self.liczba_prob:02} PRÓB")
        self.query_one("#secret", Static).update("   ".join(map(str, self._kod)))
        wynik = self.query_one("#result")
        wynik.display = True
        wynik.set_class(wygrana, "win")
        wynik.set_class(not wygrana, "loss")
        self.query_one("#result-title", Static).update(
            "Kod złamany. Gratulacje!" if wygrana else "Koniec rozgrywki. Spróbuj ponownie!"
        )
        self.query_one("#result-detail", Static).update(
            f"Wykorzystane próby: {self.liczba_prob} / {MAKS_PROB}. "
            f"Tajny kod: {''.join(map(str, self._kod))}."
        )
        self.query_one("#message", Static).update("Rozgrywka zakończona. Możesz rozpocząć nową grę.")
        przycisk = self.query_one("#new-game", Button)
        przycisk.variant = "primary"
        # Kolejny Enter po zwycięskiej próbie nie może przypadkiem włączyć nowej gry.
        self.query_one(DataTable).focus()
        self.call_after_refresh(wynik.scroll_visible, animate=False)

    def zmien_ekran(self, menu: bool) -> None:
        def przejdz(potwierdzono: bool) -> None:
            if potwierdzono:
                self.app.switch_screen(EkranStartowy() if menu else EkranGry(self.tryb))

        if self.aktywna and self.liczba_prob:
            self.app.push_screen(Potwierdzenie(), przejdz)
        else:
            przejdz(True)

    def action_nowa_gra(self) -> None:
        self.zmien_ekran(menu=False)

    def action_menu(self) -> None:
        self.zmien_ekran(menu=True)

    @on(Button.Pressed, "#new-game")
    def nowa_gra(self) -> None:
        self.action_nowa_gra()

    @on(Button.Pressed, "#menu")
    def menu(self) -> None:
        self.action_menu()

    @on(Button.Pressed, "#exit")
    def wyjdz(self) -> None:
        self.app.exit()


class MastermindApp(App):
    TITLE = "Mastermind"
    CSS_PATH = "main.tcss"
    ENABLE_COMMAND_PALETTE = False
    BINDINGS = [Binding("ctrl+q", "quit", "Wyjdź", priority=True)]

    def on_mount(self) -> None:
        self.theme = "textual-dark"
        self.push_screen(EkranStartowy())


if __name__ == "__main__":
    MastermindApp().run()
