import os
import sys
import subprocess
from PIL import Image, ImageDraw, ImageFont, ImageTk
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

# --- Constants ---
DEFAULT_DPI = 300
DEFAULT_ROWS = 2
DEFAULT_COLS = 4
DEFAULT_BORDER_IN = 0.25
DEFAULT_OVERLAP_IN = 0.0
OUTPUT_FOLDER = "slices"
PAPER_SIZES = {
    "Letter (8.5 x 11)": (8.5, 11),
    "Legal (8.5 x 14)": (8.5, 14),
    "Tabloid (11 x 17)": (11, 17),
    "A4 (8.27 x 11.69)": (8.27, 11.69),
    "Custom": (0, 0)
}

# --- Main App Class ---
class PosterTilerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Poster Tiler with Alignment Marks")

        self.preview_label = None
        self.output_pdf_var = tk.BooleanVar(value=False)
        self.create_widgets()

    def create_widgets(self):
        frm = ttk.Frame(self.root, padding=10)
        frm.grid()

        # File selector
        ttk.Label(frm, text="Select Image:").grid(column=0, row=0, sticky="w")
        self.image_path_var = tk.StringVar()
        ttk.Entry(frm, textvariable=self.image_path_var, width=50).grid(column=1, row=0)
        ttk.Button(frm, text="Browse", command=self.browse_image).grid(column=2, row=0)

        # DPI
        ttk.Label(frm, text="DPI:").grid(column=0, row=1, sticky="w")
        self.dpi_var = tk.IntVar(value=DEFAULT_DPI)
        ttk.Entry(frm, textvariable=self.dpi_var).grid(column=1, row=1, sticky="w")

        # Paper size dropdown
        ttk.Label(frm, text="Paper Size:").grid(column=0, row=2, sticky="w")
        self.paper_size_var = tk.StringVar(value="Letter (8.5 x 11)")
        paper_menu = ttk.OptionMenu(frm, self.paper_size_var, "Letter (8.5 x 11)", *PAPER_SIZES.keys(), command=self.paper_size_changed)
        paper_menu.grid(column=1, row=2, sticky="w")

        # Custom size inputs
        self.custom_width_var = tk.DoubleVar(value=8.5)
        self.custom_height_var = tk.DoubleVar(value=11)

        self.custom_width_entry = ttk.Entry(frm, textvariable=self.custom_width_var, width=10)
        self.custom_height_entry = ttk.Entry(frm, textvariable=self.custom_height_var, width=10)
        self.custom_width_entry.grid(column=1, row=3, sticky="w")
        self.custom_height_entry.grid(column=2, row=3, sticky="w")

        ttk.Label(frm, text="Custom Width (in)").grid(column=0, row=3, sticky="w")
        ttk.Label(frm, text="Custom Height (in)").grid(column=1, row=3, sticky="e")

        # Rows and Columns
        ttk.Label(frm, text="Rows:").grid(column=0, row=4, sticky="w")
        self.rows_var = tk.IntVar(value=DEFAULT_ROWS)
        ttk.Entry(frm, textvariable=self.rows_var).grid(column=1, row=4, sticky="w")

        ttk.Label(frm, text="Columns:").grid(column=0, row=5, sticky="w")
        self.cols_var = tk.IntVar(value=DEFAULT_COLS)
        ttk.Entry(frm, textvariable=self.cols_var).grid(column=1, row=5, sticky="w")

        # Border and Overlap
        ttk.Label(frm, text="Border (in):").grid(column=0, row=6, sticky="w")
        self.border_in_var = tk.DoubleVar(value=DEFAULT_BORDER_IN)
        ttk.Entry(frm, textvariable=self.border_in_var).grid(column=1, row=6, sticky="w")

        ttk.Label(frm, text="Overlap (in):").grid(column=0, row=7, sticky="w")
        self.overlap_in_var = tk.DoubleVar(value=DEFAULT_OVERLAP_IN)
        ttk.Entry(frm, textvariable=self.overlap_in_var).grid(column=1, row=7, sticky="w")

        # Checkboxes
        self.corner_marks_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(frm, text="Add Corner Xs", variable=self.corner_marks_var).grid(column=0, row=8, sticky="w")

        self.edge_xs_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(frm, text="Add Edge Xs", variable=self.edge_xs_var).grid(column=1, row=8, sticky="w")

        self.output_pdf_checkbox = ttk.Checkbutton(frm, text="Output as PDF", variable=self.output_pdf_var)
        self.output_pdf_checkbox.grid(column=0, row=9, sticky="w")

        # Run button
        ttk.Button(frm, text="Generate Tiles", command=self.generate_tiles).grid(column=0, row=10, columnspan=3, pady=10)

        # Preview area
        self.preview_label = ttk.Label(frm)
        self.preview_label.grid(column=0, row=11, columnspan=3)

        self.paper_size_changed(self.paper_size_var.get())

    def paper_size_changed(self, value):
        if value == "Custom":
            self.custom_width_entry.configure(state="normal")
            self.custom_height_entry.configure(state="normal")
        else:
            w, h = PAPER_SIZES[value]
            self.custom_width_var.set(w)
            self.custom_height_var.set(h)
            self.custom_width_entry.configure(state="disabled")
            self.custom_height_entry.configure(state="disabled")

    def browse_image(self):
        path = filedialog.askopenfilename(filetypes=[("Image files", "*.jpg *.jpeg *.png *.bmp")])
        if path:
            self.image_path_var.set(path)
            self.update_preview()

    def update_preview(self):
        try:
            path = self.image_path_var.get()
            dpi = self.dpi_var.get()
            width_in = self.custom_width_var.get()
            height_in = self.custom_height_var.get()
            rows = self.rows_var.get()
            cols = self.cols_var.get()

            tile_width_px = int(width_in * dpi)
            tile_height_px = int(height_in * dpi)
            total_width_px = tile_width_px * cols
            total_height_px = tile_height_px * rows

            img = Image.open(path).convert("RGB")
            img_width, img_height = img.size
            img_ratio = img_width / img_height
            target_ratio = total_width_px / total_height_px

            if abs(img_ratio - target_ratio) > 0.05:
                messagebox.showwarning("Aspect Ratio Warning", "The input image ratio doesn't match the output tiling layout. The image will be stretched to fit.")

            preview_img = img.resize((300, int(300 * img_height / img_width)))
            preview_img = ImageTk.PhotoImage(preview_img)
            self.preview_label.configure(image=preview_img)
            self.preview_label.image = preview_img

        except Exception as e:
            print(f"Preview error: {e}")

    def generate_tiles(self):
        try:
            path = self.image_path_var.get()
            dpi = self.dpi_var.get()
            tile_width_in = self.custom_width_var.get()
            tile_height_in = self.custom_height_var.get()
            rows = self.rows_var.get()
            cols = self.cols_var.get()
            border_in = self.border_in_var.get()
            overlap_in = self.overlap_in_var.get()
        except Exception as e:
            messagebox.showerror("Invalid Input", str(e))
            return

        border_px = int(border_in * dpi)
        overlap_px = int(overlap_in * dpi)
        tile_width_px = int(tile_width_in * dpi)
        tile_height_px = int(tile_height_in * dpi)
        total_width_px = tile_width_px * cols - (cols - 1) * overlap_px
        total_height_px = tile_height_px * rows - (rows - 1) * overlap_px

        img = Image.open(path).convert("RGB")
        img = img.resize((total_width_px, total_height_px))

        os.makedirs(OUTPUT_FOLDER, exist_ok=True)

        pdf_images = []
        count = 1
        for row in range(rows):
            for col in range(cols):
                left = col * (tile_width_px - overlap_px)
                upper = row * (tile_height_px - overlap_px)
                right = left + tile_width_px
                lower = upper + tile_height_px
                tile = img.crop((left, upper, right, lower))

                canvas_width = tile_width_px + 2 * border_px
                canvas_height = tile_height_px + 2 * border_px
                canvas = Image.new("RGB", (canvas_width, canvas_height), "white")
                canvas.paste(tile, (border_px, border_px))

                draw = ImageDraw.Draw(canvas)
                if self.corner_marks_var.get():
                    self.draw_corner_xs(draw, 0, 0, canvas_width, canvas_height, row, col)
                if self.edge_xs_var.get():
                    self.draw_overlap_xs(draw, border_px, tile_width_px, tile_height_px, overlap_px, row, col, rows, cols)

                filename = f"tile_{count:02}.jpg"
                filepath = os.path.join(OUTPUT_FOLDER, filename)
                canvas.save(filepath, dpi=(dpi, dpi))

                if self.output_pdf_var.get():
                    pdf_images.append(canvas.convert("RGB"))

                if count == 1:
                    preview = canvas.copy().resize((300, int(300 * canvas_height / canvas_width)))
                    preview_img = ImageTk.PhotoImage(preview)
                    self.preview_label.configure(image=preview_img)
                    self.preview_label.image = preview_img

                count += 1

        if self.output_pdf_var.get() and pdf_images:
            pdf_path = os.path.join(OUTPUT_FOLDER, "poster_tiles.pdf")
            pdf_images[0].save(pdf_path, save_all=True, append_images=pdf_images[1:])

        messagebox.showinfo("Done", f"Saved {count - 1} tiles to '{OUTPUT_FOLDER}'")

        if sys.platform == "win32":
            subprocess.Popen(f'explorer "{os.path.abspath(OUTPUT_FOLDER)}"')

    def draw_corner_xs(self, draw, x0, y0, width, height, row, col):
        size = 10 + 5 * (row + col)
        points = [
            (x0 + 5, y0 + 5),
            (x0 + width - 5, y0 + 5),
            (x0 + 5, y0 + height - 5),
            (x0 + width - 5, y0 + height - 5),
        ]
        for x, y in points:
            draw.line((x - size, y - size, x + size, y + size), fill="black", width=1)
            draw.line((x - size, y + size, x + size, y - size), fill="black", width=1)

    def draw_overlap_xs(self, draw, border_px, width, height, overlap_px, row, col, rows, cols):
        """Draw X marks in the center of the overlap regions inside a tile."""
        size = 6

        # Horizontal overlap (right edge of the tile)
        if col < cols - 1 and overlap_px > 0:
            # Center of the overlapped area on the right side
            x = border_px + width - (overlap_px // 2)
            y = border_px + height // 2
            draw.line((x - size, y - size, x + size, y + size), fill="red", width=1)
            draw.line((x - size, y + size, x + size, y - size), fill="red", width=1)

        # Vertical overlap (bottom edge of the tile)
        if row < rows - 1 and overlap_px > 0:
            # Center of the overlapped area on the bottom side
            x = border_px + width // 2
            y = border_px + height - (overlap_px // 2)
            draw.line((x - size, y - size, x + size, y + size), fill="red", width=1)
            draw.line((x - size, y + size, x + size, y - size), fill="red", width=1)


if __name__ == "__main__":
    root = tk.Tk()
    app = PosterTilerApp(root)
    root.mainloop()
