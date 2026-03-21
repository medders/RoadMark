#!/usr/bin/env python3
"""Build a style gallery for visual comparison of all RoadMark themes.

Generates one HTML file per style from a given input markdown file,
then writes a gallery page that lets you preview and compare them all.

Usage:
    uv run python scripts/build_gallery.py
    uv run python scripts/build_gallery.py --input examples/full_example.md
    uv run python scripts/build_gallery.py --output /tmp/my-gallery
"""

from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent
DEFAULT_INPUT = REPO_ROOT / "examples" / "full_example.md"
DEFAULT_OUTPUT = Path("/tmp/roadmark-gallery")


def build_styles(input_file: Path, output_dir: Path) -> list[str]:
    """Build one HTML file per style and return the list of style names."""
    sys.path.insert(0, str(REPO_ROOT / "src"))
    from roadmark.renderer import list_styles

    styles = list_styles()

    print(f"Building {len(styles)} styles → {output_dir}")
    for style in styles:
        output_file = output_dir / f"roadmark_{style}.html"
        subprocess.run(
            [
                "uv",
                "run",
                "roadmark",
                "build",
                str(input_file),
                "--style",
                style,
                "--output",
                str(output_file),
            ],
            check=True,
            cwd=REPO_ROOT,
        )
        print(f"  ✓ {style}")

    return styles


def build_gallery_html(styles: list[str], output_dir: Path) -> Path:
    """Write the gallery HTML file and return its path."""
    style_buttons = "\n    ".join(
        f'<button class="nav__btn{" active" if i == 0 else ""}" '
        f"onclick=\"show('{s}', this)\">{s.capitalize()}</button>"
        for i, s in enumerate(styles)
    )

    panels = "\n    ".join(
        f'<div class="panel{" active" if i == 0 else ""}" id="panel-{s}">'
        f'<iframe src="roadmark_{s}.html"></iframe></div>'
        for i, s in enumerate(styles)
    )

    dark_styles = [
        s
        for s in styles
        if any(k in s for k in ("bold", "velocity", "terminal", "onyx", "github"))
    ]
    light_styles = [s for s in styles if s not in dark_styles]

    def js_array(names: list[str]) -> str:
        return "[" + ",".join(f"'{n}'" for n in names) + "]"

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>RoadMark — Style Gallery</title>
  <style>
    *, *::before, *::after {{ box-sizing: border-box; margin: 0; padding: 0; }}

    body {{
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
      background: #0a0a0f;
      color: #f1f5f9;
      min-height: 100vh;
      display: flex;
      flex-direction: column;
    }}

    .gallery-header {{
      padding: 20px 32px 16px;
      border-bottom: 1px solid #1e1e2a;
      display: flex;
      align-items: baseline;
      gap: 16px;
    }}

    .gallery-header h1 {{
      font-size: 1rem;
      font-weight: 700;
      letter-spacing: -0.02em;
      color: #f1f5f9;
    }}

    .gallery-header p {{
      font-size: 0.78rem;
      color: #4a4a62;
    }}

    .nav {{
      display: flex;
      gap: 5px;
      padding: 10px 32px;
      border-bottom: 1px solid #1e1e2a;
      flex-wrap: wrap;
      align-items: center;
    }}

    .nav__label {{
      font-size: 0.65rem;
      font-weight: 700;
      text-transform: uppercase;
      letter-spacing: 0.1em;
      color: #3a3a4e;
      margin-right: 2px;
    }}

    .nav__btn {{
      padding: 4px 11px;
      border-radius: 5px;
      font-size: 0.73rem;
      font-weight: 500;
      cursor: pointer;
      border: 1px solid #2a2a3a;
      background: transparent;
      color: #6b6b80;
      transition: all 0.12s ease;
      font-family: inherit;
    }}

    .nav__btn:hover {{ border-color: #5a5a72; color: #e2e2e9; }}
    .nav__btn.active {{ background: #f1f5f9; color: #0a0a0f; border-color: #f1f5f9; font-weight: 600; }}

    .nav__divider {{ width: 1px; height: 18px; background: #1e1e2a; margin: 0 6px; }}

    .nav__compare-btn {{
      padding: 4px 11px;
      border-radius: 5px;
      font-size: 0.73rem;
      font-weight: 500;
      cursor: pointer;
      border: 1px solid #2a2a3a;
      background: transparent;
      color: #6b6b80;
      transition: all 0.12s ease;
      font-family: inherit;
    }}

    .nav__compare-btn:hover {{ border-color: #5a5a72; color: #e2e2e9; }}
    .nav__compare-btn.active {{ background: #1e1e2a; color: #e2e2e9; border-color: #3a3a52; }}

    .panels {{ flex: 1; }}

    .panel {{ display: none; height: calc(100vh - 92px); }}
    .panel.active {{ display: block; }}
    .panel iframe {{ width: 100%; height: 100%; border: none; display: block; }}

    .compare-grid {{ display: none; }}
    .compare-grid.active {{ display: grid; }}
    .compare-grid.cols-2 {{ grid-template-columns: 1fr 1fr; gap: 1px; background: #1a1a24; }}
    .compare-grid.cols-3 {{ grid-template-columns: 1fr 1fr 1fr; gap: 1px; background: #1a1a24; }}

    .compare-grid__cell {{ background: #0a0a0f; position: relative; }}

    .compare-grid__label {{
      position: absolute;
      top: 10px; left: 10px;
      z-index: 10;
      background: rgba(10,10,15,0.92);
      color: #94a3b8;
      font-size: 0.62rem;
      font-weight: 700;
      letter-spacing: 0.1em;
      text-transform: uppercase;
      padding: 3px 8px;
      border-radius: 4px;
      pointer-events: none;
      border: 1px solid #2a2a3a;
    }}

    .compare-grid.cols-2 iframe {{ width: 100%; height: calc((100vh - 92px) / 2); border: none; display: block; }}
    .compare-grid.cols-3 iframe {{ width: 100%; height: calc((100vh - 92px) / 2); border: none; display: block; }}
  </style>
</head>
<body>

  <div class="gallery-header">
    <h1>RoadMark Style Gallery</h1>
    <p>{len(styles)} styles — click to preview, or use compare groups</p>
  </div>

  <nav class="nav">
    <span class="nav__label">Styles</span>
    {style_buttons}
    <div class="nav__divider"></div>
    <span class="nav__label">Compare</span>
    <button class="nav__compare-btn" onclick="compare({js_array(dark_styles)}, 2, this)">Dark</button>
    <button class="nav__compare-btn" onclick="compare({js_array(light_styles)}, 2, this)">Light</button>
    <button class="nav__compare-btn" onclick="compare({js_array(styles)}, 3, this)">All</button>
  </nav>

  <div class="panels">
    {panels}
    <div class="compare-grid" id="panel-compare"></div>
  </div>

  <script>
    function show(name, btn) {{
      document.querySelectorAll('.panel, .compare-grid').forEach(el => el.classList.remove('active'));
      document.querySelectorAll('.nav__btn, .nav__compare-btn').forEach(b => b.classList.remove('active'));
      document.getElementById('panel-' + name).classList.add('active');
      btn.classList.add('active');
    }}

    function compare(styles, cols, btn) {{
      document.querySelectorAll('.panel, .compare-grid').forEach(el => el.classList.remove('active'));
      document.querySelectorAll('.nav__btn, .nav__compare-btn').forEach(b => b.classList.remove('active'));
      const grid = document.getElementById('panel-compare');
      grid.innerHTML = '';
      grid.className = 'compare-grid cols-' + cols;
      styles.forEach(name => {{
        const cell = document.createElement('div');
        cell.className = 'compare-grid__cell';
        cell.innerHTML = `<div class="compare-grid__label">${{name}}</div><iframe src="roadmark_${{name}}.html"></iframe>`;
        grid.appendChild(cell);
      }});
      grid.classList.add('active');
      btn.classList.add('active');
    }}
  </script>

</body>
</html>
"""

    gallery_path = output_dir / "index.html"
    gallery_path.write_text(html, encoding="utf-8")
    return gallery_path


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--input",
        "-i",
        type=Path,
        default=DEFAULT_INPUT,
        help=f"Markdown file to render (default: {DEFAULT_INPUT.relative_to(REPO_ROOT)})",
    )
    parser.add_argument(
        "--output",
        "-o",
        type=Path,
        default=DEFAULT_OUTPUT,
        help=f"Output directory (default: {DEFAULT_OUTPUT})",
    )
    parser.add_argument(
        "--open",
        action="store_true",
        help="Open the gallery in the default browser when done",
    )
    args = parser.parse_args()

    input_file: Path = args.input
    output_dir: Path = args.output

    if not input_file.exists():
        print(f"Error: input file not found: {input_file}", file=sys.stderr)
        sys.exit(1)

    if output_dir.exists():
        shutil.rmtree(output_dir)
    output_dir.mkdir(parents=True)

    styles = build_styles(input_file, output_dir)
    gallery_path = build_gallery_html(styles, output_dir)

    print(f"\nGallery ready: {gallery_path}")

    if args.open:
        import webbrowser

        webbrowser.open(gallery_path.as_uri())


if __name__ == "__main__":
    main()
