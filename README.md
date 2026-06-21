# MosaicGenerator

MosaicGenerator is a production-focused desktop application engine for creating printable adult mosaic coloring pages from photographs or artwork.

## Version 0.3

The current release runs end-to-end:

1. Load and optimize an input image.
2. Calculate a millimetre-accurate printable circle layout.
3. Reduce the image to a numbered adaptive palette.
4. Generate one `Circle` dataclass object per printable dot.
5. Export a print-ready coloring page SVG.
6. Export numbered and colored PNG previews.
7. Export a filled answer page.
8. Export a color legend.
9. Export PDF pages.
10. Save the project data as JSON.

## Run

```powershell
python -m src.main
```

Optional overrides:

```powershell
python -m src.main --input input_images/sample.jpg --colors 12 --circle-diameter 3.5 --circle-gap 0.3
```

Outputs are written to `output/`:

- `coloring_page.svg`
- `preview.png`
- `preview_numbered.png`
- `preview_colored.png`
- `answer_page.png`
- `color_legend.png`
- `coloring_page.pdf`
- `answer_page.pdf`
- `color_legend.pdf`
- `project.json`

## Architecture

```text
Image
  -> Image Engine
  -> Optimized Image
  -> Palette Engine
  -> Reduced Color Image
  -> Layout Engine
  -> Circle Coordinates
  -> Mosaic Engine
  -> Circle Objects
  -> SVG Exporter
  -> Preview Exporter
```

Exporters do not calculate layout coordinates. They consume the generated `Circle` objects and page metadata.
