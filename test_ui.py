"""Testy wyłącznie interfejsu; oceny oblicza prawdziwy moduł ocena.py.

Uruchom: python -m pytest -q -p no:cacheprovider test_ui.py
Wymaga pytest i pytest-asyncio oprócz Textual.
"""

from unittest.mock import Mock

import pytest
from textual.widgets import Button, DataTable, Input, Static

import main


@pytest.fixture
def staly_kod(monkeypatch):
    """Stały kod umożliwia powtarzalne testy UI bez zastępowania algorytmu oceny."""
    easy = Mock(return_value=[1, 2, 1, 3])
    hard = Mock(return_value=[9, 8, 9, 0])
    monkeypatch.setattr(main.silnik, "generuj_kod_easy", easy)
    monkeypatch.setattr(main.silnik, "generuj_kod_hard", hard)
    return easy, hard


async def rozpocznij(app, pilot, trudny=False):
    if trudny:
        await pilot.click("#hard")
    app.screen.query_one("#start").scroll_visible(animate=False)
    await pilot.pause()
    await pilot.click("#start")
    await pilot.pause()
    assert isinstance(app.screen, main.EkranGry)
    return app.screen


async def wpisz(pilot, ekran, kod, przycisk=False):
    pole = ekran.query_one(Input)
    pole.value = kod
    pole.focus()
    await pilot.pause()
    if przycisk:
        ekran.query_one("#submit").scroll_visible(animate=False)
        await pilot.pause()
        await pilot.click("#submit")
    else:
        await pilot.press("enter")
    await pilot.pause()


@pytest.mark.parametrize("tekst,maks,blad", [
    ("", 3, "Wpisz kod"),
    ("    ", 3, "Wpisz kod"),
    ("123", 3, "dokładnie 4"),
    ("12345", 9, "dokładnie 4"),
    ("12a3", 3, "wyłącznie cyfr"),
    ("-123", 3, "wyłącznie cyfr"),
    ("1 23", 3, "wyłącznie cyfr"),
    ("１２３４", 9, "wyłącznie cyfr"),
    ("١٢٣٤", 9, "wyłącznie cyfr"),
    ("1234", 3, "od 0 do 3"),
])
def test_walidacja(tekst, maks, blad):
    with pytest.raises(ValueError, match=blad):
        main.odczytaj_probe(tekst, maks)


@pytest.mark.parametrize("tekst,maks,wynik", [
    ("0000", 3, [0, 0, 0, 0]),
    ("0123", 3, [0, 1, 2, 3]),
    ("9890", 9, [9, 8, 9, 0]),
])
def test_dozwolone_kody(tekst, maks, wynik):
    assert main.odczytaj_probe(tekst, maks) == wynik


@pytest.mark.asyncio
async def test_rzeczywiste_importy_i_silnik(monkeypatch):
    """Bez podmiany losowania: oba prawdziwe generatory są wywołane przez UI."""
    for trudny, nazwa in ((False, "generuj_kod_easy"), (True, "generuj_kod_hard")):
        generator = Mock(wraps=getattr(main.silnik, nazwa))
        with monkeypatch.context() as m:
            m.setattr(main.silnik, nazwa, generator)
            app = main.MastermindApp()
            async with app.run_test(size=(120, 45)) as pilot:
                ekran = await rozpocznij(app, pilot, trudny)
                generator.assert_called_once_with()
                assert len(ekran._kod) == 4
                assert all(0 <= cyfra <= ekran.maks_cyfra for cyfra in ekran._kod)
                assert ekran.query_one(DataTable).row_count == 0
                assert "?" in str(ekran.query_one("#secret", Static).content)
                assert not ekran.query_one("#result").display


@pytest.mark.asyncio
async def test_ocena_historia_i_ukrycie_kodu(staly_kod, monkeypatch):
    oceniaj = Mock(wraps=main.ocena.ocena)
    monkeypatch.setattr(main.ocena, "ocena", oceniaj)
    app = main.MastermindApp()
    async with app.run_test(size=(120, 45)) as pilot:
        ekran = await rozpocznij(app, pilot)
        await pilot.press("1", "1", "2", "1", "enter")
        await pilot.pause()
        oceniaj.assert_called_once_with([1, 2, 1, 3], [1, 1, 2, 1])
        tabela = ekran.query_one(DataTable)
        row = tabela.get_row_at(0)
        assert row[0] == "01"
        assert str(row[1]) == "1 1 2 1"
        assert str(row[2]) == "● 1"
        assert str(row[3]) == "○ 2"
        assert ekran.query_one(Input).value == ""
        assert ekran._kod == [1, 2, 1, 3]
        assert "?" in str(ekran.query_one("#secret", Static).content)
        await wpisz(pilot, ekran, "0000", przycisk=True)
        assert tabela.row_count == 2
        assert str(tabela.get_row_at(1)[2]) == "● 0"
        assert str(tabela.get_row_at(1)[3]) == "○ 0"


@pytest.mark.asyncio
async def test_bledy_nie_zuzywaja_prob_i_znikaja_po_ruchu(staly_kod):
    app = main.MastermindApp()
    async with app.run_test(size=(120, 45)) as pilot:
        ekran = await rozpocznij(app, pilot)
        for kod in ("", "12", "12345", "12x3", "１２３４", "9999", "1 23"):
            await wpisz(pilot, ekran, kod)
            assert ekran.liczba_prob == 0
            assert ekran.query_one(DataTable).row_count == 0
            assert ekran.query_one("#message").has_class("error")
        await wpisz(pilot, ekran, "0000")
        assert ekran.liczba_prob == 1
        assert not ekran.query_one("#message").has_class("error")


@pytest.mark.asyncio
async def test_zwyciestwo_blokada_ruchow_i_restart(staly_kod):
    app = main.MastermindApp()
    async with app.run_test(size=(120, 45)) as pilot:
        ekran = await rozpocznij(app, pilot, trudny=True)
        await wpisz(pilot, ekran, "9890")
        assert not ekran.aktywna
        assert ekran.query_one("#result").has_class("win")
        assert "1 / 10" in str(ekran.query_one("#result-detail", Static).content)
        assert "9890" in str(ekran.query_one("#result-detail", Static).content)
        assert ekran.query_one(Input).disabled
        assert ekran.query_one("#submit", Button).disabled
        ekran.sprawdz_probe()
        await pilot.press("enter", "enter")
        assert ekran.query_one(DataTable).row_count == 1
        await pilot.click("#new-game")
        await pilot.pause()
        nowy = app.screen
        assert isinstance(nowy, main.EkranGry) and nowy is not ekran
        assert nowy.tryb == "hard" and nowy.aktywna
        assert nowy.liczba_prob == 0
        assert nowy.query_one(DataTable).row_count == 0
        assert not nowy.query_one(Input).disabled
        assert not nowy.query_one("#result").display
        staly_kod[1].assert_called_with()
        assert staly_kod[1].call_count == 2


@pytest.mark.asyncio
async def test_przegrana_i_zwyciestwo_w_ostatniej_probie(staly_kod):
    for ostatni_kod, oczekiwana_klasa in (("0000", "loss"), ("1213", "win")):
        app = main.MastermindApp()
        async with app.run_test(size=(120, 45)) as pilot:
            ekran = await rozpocznij(app, pilot)
            for _ in range(main.MAKS_PROB - 1):
                await wpisz(pilot, ekran, "0000")
            assert ekran.aktywna
            await wpisz(pilot, ekran, ostatni_kod)
            assert not ekran.aktywna
            assert ekran.liczba_prob == main.MAKS_PROB
            assert ekran.query_one(DataTable).row_count == main.MAKS_PROB
            assert ekran.query_one("#result").has_class(oczekiwana_klasa)
            assert "1213" in str(ekran.query_one("#result-detail", Static).content)
            assert "1   2   1   3" in str(ekran.query_one("#secret", Static).content)
            ekran.sprawdz_probe()
            assert ekran.liczba_prob == main.MAKS_PROB
            await pilot.press("ctrl+n")
            await pilot.pause()
            assert app.screen.liczba_prob == 0


@pytest.mark.asyncio
async def test_podwojne_zatwierdzenie(staly_kod):
    app = main.MastermindApp()
    async with app.run_test(size=(120, 45)) as pilot:
        ekran = await rozpocznij(app, pilot)
        pole = ekran.query_one(Input)
        pole.value = "0000"
        await pilot.pause()
        # Dwa oczekujące zdarzenia Enter i kliknięcia tego samego ruchu.
        pole.post_message(Input.Submitted(pole, "0000"))
        pole.post_message(Input.Submitted(pole, "0000"))
        przycisk = ekran.query_one("#submit", Button)
        przycisk.post_message(Button.Pressed(przycisk))
        przycisk.post_message(Button.Pressed(przycisk))
        await pilot.pause()
        assert ekran.liczba_prob == 1
        assert ekran.query_one(DataTable).row_count == 1
        assert not ekran.query_one("#message").has_class("error")


@pytest.mark.asyncio
async def test_potwierdzenie_restartu_i_powrot_do_menu(staly_kod):
    app = main.MastermindApp()
    async with app.run_test(size=(120, 45)) as pilot:
        ekran = await rozpocznij(app, pilot)
        await wpisz(pilot, ekran, "0000")
        await pilot.press("ctrl+n")
        assert isinstance(app.screen, main.Potwierdzenie)
        await pilot.press("escape")
        assert app.screen is ekran and ekran.liczba_prob == 1
        await pilot.press("ctrl+n")
        await pilot.click("#confirm-end")
        await pilot.pause()
        assert app.screen is not ekran and app.screen.liczba_prob == 0
        await pilot.press("escape")
        await pilot.pause()
        assert isinstance(app.screen, main.EkranStartowy)
        await rozpocznij(app, pilot, trudny=True)
        assert app.screen.tryb == "hard"


@pytest.mark.asyncio
@pytest.mark.parametrize("rozmiar", [(120, 42), (80, 24), (60, 20), (40, 16)])
async def test_maly_terminal_i_zmiana_rozmiaru(staly_kod, rozmiar):
    app = main.MastermindApp()
    async with app.run_test(size=rozmiar) as pilot:
        ekran = await rozpocznij(app, pilot)
        if rozmiar[0] < 88:
            assert ekran.query_one("#board").children[0].id == "control-panel"
        for id in ("#guess", "#submit", "#new-game", "#menu", "#exit"):
            widget = ekran.query_one(id)
            widget.scroll_visible(animate=False)
            await pilot.pause()
            assert 0 <= widget.region.x < rozmiar[0]
            assert widget.region.right <= rozmiar[0]
            assert 0 <= widget.region.y < rozmiar[1] - 1
        await wpisz(pilot, ekran, "1213")
        assert ekran.query_one("#result").has_class("win")
        await pilot.press("ctrl+n")
        await pilot.pause()
        assert app.screen.liczba_prob == 0
        await pilot.resize_terminal(110, 40)
        await pilot.pause()
        assert app.screen.query_one("#board").children[0].id == "history-panel"
        await pilot.resize_terminal(40, 16)
        await pilot.pause()
        assert app.screen.query_one("#board").children[0].id == "control-panel"


@pytest.mark.asyncio
@pytest.mark.parametrize("sposob", ["start", "game", "shortcut"])
async def test_wyjscie(staly_kod, sposob):
    app = main.MastermindApp()
    async with app.run_test(size=(120, 45)) as pilot:
        if sposob == "game":
            await rozpocznij(app, pilot)
        if sposob == "shortcut":
            await pilot.press("ctrl+q")
        else:
            await pilot.click("#exit")
        await pilot.pause()
        assert not app.is_running


@pytest.mark.asyncio
async def test_start_klawiatura_i_blad_po_kliknieciu(staly_kod):
    app = main.MastermindApp()
    async with app.run_test(size=(80, 24)) as pilot:
        await pilot.press("enter")
        await pilot.pause()
        ekran = app.screen
        assert isinstance(ekran, main.EkranGry)
        await wpisz(pilot, ekran, "12x3", przycisk=True)
        assert ekran.liczba_prob == 0
        assert "wyłącznie cyfr" in str(ekran.query_one("#message", Static).content)
        await pilot.press("ctrl+q")
        assert not app.is_running


@pytest.mark.asyncio
async def test_menu_w_trakcie_gry_wymaga_potwierdzenia(staly_kod):
    app = main.MastermindApp()
    async with app.run_test(size=(40, 16)) as pilot:
        ekran = await rozpocznij(app, pilot)
        await wpisz(pilot, ekran, "0000")
        await pilot.click("#menu")
        assert isinstance(app.screen, main.Potwierdzenie)
        await pilot.press("escape")
        assert app.screen is ekran
        assert ekran.query_one(DataTable).row_count == 1
        await pilot.click("#menu")
        app.screen.query_one("#confirm-end").scroll_visible(animate=False)
        await pilot.pause()
        await pilot.click("#confirm-end")
        await pilot.pause()
        assert isinstance(app.screen, main.EkranStartowy)
