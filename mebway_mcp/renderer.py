"""Dependency-free renderer: bounded summaries in, escaped static HTML out."""
from __future__ import annotations

from html import escape
import math
import re
import unicodedata
from urllib.parse import urlsplit

NEUTRAL_COLOUR = "#d9ddda"
MAX_ROOMS = 100
MAX_FURNITURE = 2000


def _mapping(value, name):
    if not isinstance(value, dict):
        raise ValueError(f"{name} must be an object")
    return value


def _text(value, name, limit=500):
    if not isinstance(value, str) or len(value) > limit or any(unicodedata.category(c) in {"Cc", "Cf", "Cs"} and c not in "\n\t" for c in value):
        raise ValueError(f"{name} must be bounded text")
    return value


def _identifier(value):
    if isinstance(value, bool) or not isinstance(value, (int, str)):
        raise ValueError("Invalid identifier")
    return _text(str(value), "identifier", 128)


def _number(value, name, minimum=-100000, maximum=100000):
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"{name} must be numeric")
    if not minimum <= value <= maximum or not math.isfinite(value):
        raise ValueError(f"{name} outside allowed bounds")
    return value


def _array(value, name, limit):
    if not isinstance(value, list) or len(value) > limit:
        raise ValueError(f"{name} must be a bounded array")
    return value


def _link(value):
    value = _text(value, "project URL", 2048)
    if not value:
        return ""
    if any(c.isspace() or ord(c) < 32 for c in value) or "\\" in value:
        raise ValueError("Invalid project URL")
    parsed = urlsplit(value)
    if (parsed.scheme != "https" or parsed.hostname not in {"mebway.ai", "www.mebway.ai", "mcp.mebway.ai"}
            or parsed.username is not None or parsed.password is not None or parsed.port not in (None, 443)):
        raise ValueError("Only HTTPS Mebway project links are allowed")
    return value


def _validate(data):
    """Select and validate public fields only; never copy arbitrary payload fields."""
    _mapping(data, "presentation")
    if data.get("schema_version") != "1.0" or data.get("manufacturing_approved") is not False:
        raise ValueError("Unsupported presentation version or manufacturing approval")
    project = _mapping(data.get("project"), "project")
    result = {"name": _text(project.get("name"), "project name"), "url": _link(project.get("url", "")), "rooms": []}
    _identifier(project.get("id"))
    count = 0
    for room in _array(project.get("rooms"), "rooms", MAX_ROOMS):
        _mapping(room, "room")
        _identifier(room.get("id"))
        clean = {"name": _text(room.get("name"), "room name"), "furniture": []}
        for field in ("width_cm", "depth_cm"):
            clean[field] = _number(room.get(field), field, 0.1)
        for item in _array(room.get("furniture"), "furniture", MAX_FURNITURE):
            count += 1
            if count > MAX_FURNITURE:
                raise ValueError("Too many furniture items")
            _mapping(item, "furniture item")
            _identifier(item.get("id"))
            furniture = {"name": _text(item.get("name"), "furniture name"),
                         "sku": _text(item.get("sku", ""), "SKU"), "finishes": []}
            for field in ("width_cm", "depth_cm", "height_cm"):
                furniture[field] = _number(item.get(field), field, 0.1)
            for field in ("x_cm", "y_cm"):
                furniture[field] = _number(item.get(field), field)
            furniture["rotation_deg"] = _number(item.get("rotation_deg"), "rotation", -360, 360)
            for finish in _array(item.get("finishes", []), "finishes", 30):
                _mapping(finish, "finish")
                clean_finish = {key: _text(finish.get(key), key) for key in ("option", "decor")}
                colour = finish.get("color_hex")
                if colour is not None and (not isinstance(colour, str) or not re.fullmatch(r"#[0-9a-fA-F]{6}", colour)):
                    raise ValueError("Finish colour must be a six-digit hex value or null")
                if finish.get("color_provenance") not in (None, "estimated"):
                    raise ValueError("Finish colour provenance must be estimated or null")
                clean_finish["color_hex"] = colour
                furniture["finishes"].append(clean_finish)
            clean["furniture"].append(furniture)
        result["rooms"].append(clean)
    quote = _mapping(data.get("quotation"), "quotation")
    if quote.get("status") != "indicative":
        raise ValueError("Quotation must be indicative")
    currency = _text(quote.get("currency"), "currency", 3)
    if not re.fullmatch(r"[A-Z]{3}", currency):
        raise ValueError("Currency must be three uppercase letters")
    total = quote.get("total")
    if total is not None:
        total = _number(total, "quotation total", 0, 1_000_000_000)
    for item in _array(quote.get("items", []), "quotation items", MAX_FURNITURE):
        _mapping(item, "quotation item")
    result["quotation"] = {"total": total, "currency": currency,
                           "disclaimer": _text(quote.get("disclaimer", ""), "disclaimer", 2000)}
    return result


def _format(value):
    return f"{value:.3f}".rstrip("0").rstrip(".")


def _colour(item):
    # Only a validated server-projected sample becomes paint; labels are never CSS.
    return next((finish["color_hex"] for finish in item["finishes"] if finish["color_hex"]), NEUTRAL_COLOUR)


def render_html(data) -> str:
    """Return standalone HTML. This function has no I/O or network operations."""
    project = _validate(data)
    rooms = []
    for index, room in enumerate(project["rooms"], 1):
        width, depth = room["width_cm"], room["depth_cm"]
        shapes = [f'<rect x="0" y="0" width="{_format(width)}" height="{_format(depth)}" fill="#faf9f5" stroke="#55625a" stroke-width="2"/>']
        details = []
        for number, item in enumerate(room["furniture"], 1):
            x, y = item["x_cm"], item["y_cm"]
            w, d = item["width_cm"], item["depth_cm"]
            title = escape(f'{item["name"]} ({item["sku"]})')
            shapes.append(f'<g transform="translate({_format(x)} {_format(y)}) rotate({_format(item["rotation_deg"])})">'
                          f'<title>{title}</title><rect x="0" y="0" width="{_format(w)}" height="{_format(d)}" '
                          f'fill="{_colour(item)}" stroke="#55625a" stroke-width="1"/>'
                          f'<text x="{_format(w / 2)}" y="{_format(d / 2)}" text-anchor="middle" dominant-baseline="middle" '
                          f'font-size="{_format(max(1, min(w, d) / 3))}">{number}</text></g>')
            finishes = "; ".join(f'{f["option"]}: {f["decor"]}' for f in item["finishes"])
            colour_status = ("Estimated colour; texture/grain not represented"
                             if any(f["color_hex"] for f in item["finishes"]) else "Colour unavailable; neutral placeholder")
            details.append(f'<li><span class="swatch" style="background:{_colour(item)}"></span>'
                           f'<strong>{number}. {escape(item["name"])}</strong> <span>{escape(item["sku"])}</span>'
                           f'<div>{_format(w)} × {_format(d)} × {_format(item["height_cm"])} cm</div>'
                           f'<div>{escape(finishes)}</div><div>{colour_status}</div></li>')
        rooms.append(f'<section class="room"><h2>{escape(room["name"])}</h2>'
                     f'<p>{_format(width)} × {_format(depth)} cm · schematic 2D plan</p>'
                     f'<svg xmlns="http://www.w3.org/2000/svg" role="img" aria-labelledby="room-{index}" '
                     f'viewBox="-5 -5 {_format(width + 10)} {_format(depth + 10)}">'
                     f'<title id="room-{index}">{escape(room["name"])}</title>{"".join(shapes)}</svg>'
                     f'<ol class="furniture">{"".join(details)}</ol></section>')
    quote = project["quotation"]
    price = "Price unavailable — Mebway review required" if quote["total"] is None else f'{quote["total"]:,.2f} {quote["currency"]}'
    project_link = f'<a href="{escape(project["url"], quote=True)}" rel="noopener noreferrer" referrerpolicy="no-referrer">Open project in Mebway (sign in)</a>' if project["url"] else ""
    return f'''<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<meta http-equiv="Content-Security-Policy" content="default-src 'none'; script-src 'none'; style-src 'unsafe-inline'; img-src 'none'; connect-src 'none'; object-src 'none'; base-uri 'none'; form-action 'none'">
<meta name="referrer" content="no-referrer"><title>{escape(project["name"])} · Mebway presentation</title>
<style>
*{{box-sizing:border-box}}body{{margin:0;background:#f3f2ed;color:#24382d;font:16px/1.55 system-ui,sans-serif;overflow-wrap:anywhere}}
main{{max-width:1200px;margin:auto;padding:32px}}header{{margin-bottom:24px}}h1{{font-size:clamp(1.5rem,4vw,2.6rem);line-height:1.2;margin:8px 0}}
h2{{font-size:1.3rem;margin:0}}p{{margin:8px 0}}.brand{{font-size:.8rem;letter-spacing:.12em;text-transform:uppercase}}
.layout{{display:grid;grid-template-columns:minmax(0,1fr) minmax(240px,320px);gap:24px;align-items:start}}
.room,aside{{background:white;border:1px solid #dce1d8;border-radius:16px;padding:24px;margin-bottom:20px;min-width:0}}
svg{{display:block;width:100%;max-height:560px;aspect-ratio:5/4;margin-top:16px;overflow:hidden}}svg text{{fill:#24382d;font-family:system-ui,sans-serif}}
.furniture{{list-style:none;padding:0;margin:20px 0 0}}.furniture li{{padding:12px 0;border-top:1px solid #e4e8e0}}
.furniture span,.furniture div{{font-size:.875rem}}.swatch{{display:inline-block;width:12px;height:12px;border:1px solid #89998c;border-radius:3px;margin-right:8px}}
.price{{font-size:1.5rem;font-weight:700}}.notice{{font-size:.875rem;color:#526156}}a{{color:#195539;text-underline-offset:3px;display:inline-block;padding:8px 0}}
@media(max-width:760px){{main{{padding:16px}}.layout{{grid-template-columns:1fr}}.room,aside{{padding:18px}}aside{{grid-row:1}}}}
@media print{{body{{background:white}}main{{padding:0}}.layout{{display:block}}.room,aside{{break-inside:avoid}}}}
</style></head><body><main><header><div class="brand">Mebway · project presentation</div><h1>{escape(project["name"])}</h1>
<p>Generic furniture rectangles. Sampled colours are estimated; texture/grain is not represented. Confirm dimensions and finishes with Mebway.</p>{project_link}</header>
<div class="layout"><div>{"".join(rooms) or '<p>No rooms in this presentation.</p>'}</div>
<aside><h2>Indicative estimate</h2><p class="price">{price}</p><p>Not a binding quotation.</p><p>{escape(quote["disclaimer"])}</p>
<p class="notice">Manufacturing approval: no. This presentation does not place an order or start production.</p>
<p class="notice">Ask your assistant to send this concept to Mebway for a final valuation. Nothing is submitted until you request it.</p>
</aside></div></main></body></html>'''
