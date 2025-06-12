import pytest
from PIL import Image, ImageDraw
import os
import sys

# Ensure the repository root is on the import path when tests are executed via
# `pytest`.
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from main import PosterTilerApp


def test_draw_corner_xs_black_pixels():
    img = Image.new("RGB", (50, 50), "white")
    draw = ImageDraw.Draw(img)
    app = PosterTilerApp.__new__(PosterTilerApp)
    app.draw_corner_xs(draw, 0, 0, 50, 50, 0, 0)
    assert img.getpixel((5, 5)) == (0, 0, 0)
    assert img.getpixel((0, 0)) == (0, 0, 0)


def test_draw_overlap_xs_red_pixel():
    img = Image.new("RGB", (120, 120), "white")
    draw = ImageDraw.Draw(img)
    app = PosterTilerApp.__new__(PosterTilerApp)
    app.draw_overlap_xs(draw, border_px=10, width=80, height=80, overlap_px=20, row=0, col=0, rows=2, cols=2)
    assert img.getpixel((80, 50)) == (255, 0, 0)


def test_draw_overlap_xs_bottom_pixel():
    img = Image.new("RGB", (120, 120), "white")
    draw = ImageDraw.Draw(img)
    app = PosterTilerApp.__new__(PosterTilerApp)
    app.draw_overlap_xs(draw, border_px=10, width=80, height=80, overlap_px=20, row=0, col=0, rows=2, cols=2)
    assert img.getpixel((50, 80)) == (255, 0, 0)


def test_draw_ruler_marks_top_tick():
    img = Image.new("RGB", (150, 150), "white")
    draw = ImageDraw.Draw(img)
    app = PosterTilerApp.__new__(PosterTilerApp)
    app.draw_ruler_marks(draw, border_px=25, width=100, height=100, dpi=100)
    assert img.getpixel((25, 0)) == (0, 0, 0)

class DummyVar:
    def __init__(self, value):
        self._value = value
    def get(self):
        return self._value
    def set(self, v):
        self._value = v

def test_generate_tiles_creates_file(tmp_path, monkeypatch):
    from main import OUTPUT_FOLDER
    img = Image.new("RGB", (100, 100), "white")
    input_path = tmp_path / "img.jpg"
    img.save(input_path)

    import main
    app = main.PosterTilerApp.__new__(main.PosterTilerApp)
    app.image_path_var = DummyVar(str(input_path))
    app.dpi_var = DummyVar(100)
    app.custom_width_var = DummyVar(1)
    app.custom_height_var = DummyVar(1)
    app.rows_var = DummyVar(1)
    app.cols_var = DummyVar(1)
    app.border_in_var = DummyVar(0)
    app.overlap_in_var = DummyVar(0)
    app.corner_marks_var = DummyVar(False)
    app.edge_xs_var = DummyVar(False)
    app.ruler_marks_var = DummyVar(False)
    app.output_pdf_var = DummyVar(False)
    app.preview_label = type('Lbl', (), {'configure': lambda *a, **k: None})()

    monkeypatch.setattr(main, 'OUTPUT_FOLDER', str(tmp_path / 'out'))
    monkeypatch.setattr(main.messagebox, 'showinfo', lambda *a, **k: None)
    monkeypatch.setattr(main.messagebox, 'showwarning', lambda *a, **k: None)
    monkeypatch.setattr(main, 'subprocess', type('P', (), {'Popen': lambda *a, **k: None})())
    monkeypatch.setattr(main.ImageTk, 'PhotoImage', lambda *a, **k: object())

    app.generate_tiles()
    files = list((tmp_path / 'out').iterdir())
    assert len(files) == 1

