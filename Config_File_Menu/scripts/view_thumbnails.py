"""Generate placeholder Perspective view thumbnails referenced by resource.json."""

from __future__ import annotations

import json
from pathlib import Path

try:
    from PIL import Image, ImageDraw, ImageFont
except ImportError as exc:  # pragma: no cover
    raise SystemExit("Pillow is required: pip install Pillow") from exc


def _short_label(view_dir: Path) -> str:
    name = view_dir.name
    if len(name) <= 14:
        return name
    words = [part for part in name.replace("_", " ").split() if part]
    if len(words) >= 2:
        return "".join(word[0].upper() for word in words[:4])
    return name[:12] + "…"


def write_view_thumbnail(path: Path, label: str, *, size: int = 200) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    img = Image.new("RGBA", (size, size), (247, 248, 250, 255))
    draw = ImageDraw.Draw(img)
    draw.rounded_rectangle(
        (12, 12, size - 12, size - 12),
        radius=16,
        outline=(216, 222, 228, 255),
        width=2,
        fill=(255, 255, 255, 255),
    )
    draw.rectangle((12, 12, size - 12, 52), fill=(0, 86, 145, 255))
    try:
        title_font = ImageFont.truetype("arial.ttf", 16)
        body_font = ImageFont.truetype("arial.ttf", 22)
    except OSError:
        title_font = ImageFont.load_default()
        body_font = ImageFont.load_default()
    draw.text((24, 20), "CFM", fill=(255, 255, 255, 255), font=title_font)
    text = label
    bbox = draw.textbbox((0, 0), text, font=body_font)
    text_w = bbox[2] - bbox[0]
    text_h = bbox[3] - bbox[1]
    draw.text(
        ((size - text_w) / 2, (size - text_h) / 2 + 8 - bbox[1]),
        text,
        fill=(0, 86, 145, 255),
        font=body_font,
    )
    img.save(path, format="PNG", optimize=True)


def ensure_view_thumbnails(views_root: Path, *, force: bool = False) -> int:
    """Create thumbnail.png for views whose resource.json lists it.

    With force=True, existing thumbnails are overwritten with the neutral CFM
    placeholder. This is required for public/Exchange builds: Designer captures a
    live screenshot of the rendered view when a developer saves it, which can embed
    that developer's gateway branding, hostnames, and menu content into the resource.
    Regenerating placeholders on every build guarantees no captured screenshot ships.
    """
    created = 0
    for resource_path in sorted(views_root.rglob("resource.json")):
        try:
            data = json.loads(resource_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            continue
        files = data.get("files") or []
        if "thumbnail.png" not in files:
            continue
        thumb_path = resource_path.parent / "thumbnail.png"
        if thumb_path.is_file() and not force:
            continue
        write_view_thumbnail(thumb_path, _short_label(resource_path.parent))
        created += 1
    return created
