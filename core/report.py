"""Report step: combine text, charts and tables into one self-contained HTML page."""

from pathlib import Path

import pandas as pd
import plotly.graph_objects as go

from core.validate import REPORTS

# A section is (heading, text, chart or None, table or None).
Section = tuple[str, str, go.Figure | None, pd.DataFrame | None]

CSS = """
body { font-family: system-ui, sans-serif; max-width: 900px; margin: 2rem auto;
       padding: 0 16px; color: #222; background: #fff; line-height: 1.5; }
table { border-collapse: collapse; margin: 1rem 0; font-size: 0.9rem; }
th, td { padding: 4px 10px; border-bottom: 1px solid #ddd; text-align: left; }
"""


def build_html(title: str, sections: list[Section]) -> str:
    """Turn sections into one HTML page; plotly.js is loaded once from its CDN."""
    parts = [f"<h1>{title}</h1>"]
    plotly_js = "cdn"
    for heading, text, fig, table in sections:
        parts += [f"<h2>{heading}</h2>", f"<p>{text}</p>"]
        if fig is not None:
            parts.append(fig.to_html(full_html=False, include_plotlyjs=plotly_js))
            plotly_js = False
        if table is not None:
            parts.append(table.to_html(index=False, border=0))
    body = "\n".join(parts)
    return f"<!doctype html><html><head><meta charset='utf-8'><title>{title}</title><style>{CSS}</style></head><body>{body}</body></html>"


def save_html(html: str, name: str, out_dir: Path = REPORTS) -> Path:
    """Save the page as reports/<name>.html."""
    path = out_dir / f"{name}.html"
    path.write_text(html, encoding="utf-8")
    return path
