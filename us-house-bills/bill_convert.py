"""Bill-DTD XML -> markdown + reference rows (pack-shared helper).

Vendored, self-contained (stdlib ElementTree only) so the pack is
copy-to-port: providers import it RELATIVELY (`from ..bill_convert import …`
style resolves under the registry's synthetic pack namespace). The richer
harvester in Open-Source-Legal/us-house-bill-feed is the primary content
path; this converter serves the on-demand gap-fill provider and matches its
output shape.

References are deterministic markup: ``<external-xref legal-doc="usc"
parsable-cite="usc/43/1615">``. Amendatory classification: the citation's
containing ``<text>``/``<header>`` node carries an "is amended"/"is
repealed" instruction sentence.
"""

from __future__ import annotations

import re
import xml.etree.ElementTree as ET

_AMENDATORY_RE = re.compile(
    r"\b(?:is|are)\s+(?:further\s+)?(?:amended|repealed)\b", re.IGNORECASE
)
_SNIPPET_RADIUS = 160
_NESTED_LEVELS = frozenset(
    {"subsection", "paragraph", "subparagraph", "clause", "subclause", "item"}
)

_USC_RE = re.compile(r"^usc/(?P<title>\d+)/(?P<sec>[0-9A-Za-z.\-]+)")
_PL_RE = re.compile(r"^pl/(?P<cong>\d+)/(?P<num>\d+)")
_STAT_RE = re.compile(r"^statute/(?P<vol>\d+)/(?P<page>\d+)")
_BILL_RE = re.compile(
    r"^(?P<cong>\d+)(?P<kind>hr|s|hjres|sjres|hconres|sconres|hres|sres)(?P<num>\d+)$"
)


def _norm(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def _flat_text(el: ET.Element) -> str:
    return _norm("".join(el.itertext()))


def canonical_key_for_cite(parsable_cite: str) -> str | None:
    cite = (parsable_cite or "").strip()
    m = _USC_RE.match(cite)
    if m:
        return f"usc-{m.group('title')}:{m.group('sec').lower()}"
    m = _PL_RE.match(cite)
    if m:
        return f"publ:{m.group('cong')}-{m.group('num')}"
    m = _STAT_RE.match(cite)
    if m:
        return f"stat:{m.group('vol')}.{m.group('page')}"
    m = _BILL_RE.match(cite)
    if m:
        return f"{m.group('kind')}:{m.group('cong')}-{m.group('num')}"
    return None


def collect_relationships(root: ET.Element) -> tuple[list[dict], dict[str, int]]:
    """Deduped relationship rows (AMENDS beats CITES) + unhandled tally.

    verified=True is deliberate: these edges come from GPO's own reference
    markup, not model inference.
    """
    rows: dict[str, dict] = {}
    unhandled: dict[str, int] = {}
    for container in root.iter():
        if container.tag not in {"text", "header"}:
            continue
        context = _flat_text(container)
        in_amendatory = bool(_AMENDATORY_RE.search(context))
        for xref in container.iter("external-xref"):
            cite = xref.get("parsable-cite") or ""
            if not cite:
                continue
            key = canonical_key_for_cite(cite)
            if key is None:
                label = xref.get("legal-doc") or "unknown"
                unhandled[label] = unhandled.get(label, 0) + 1
                continue
            cite_text = _flat_text(xref)
            idx = context.find(cite_text) if cite_text else -1
            if idx >= 0:
                start = max(0, idx - _SNIPPET_RADIUS)
                end = min(len(context), idx + len(cite_text) + _SNIPPET_RADIUS)
                snippet = context[start:end]
            else:
                snippet = context[: _SNIPPET_RADIUS * 2]
            relationship = "AMENDS" if in_amendatory else "CITES"
            existing = rows.get(key)
            if existing is None or (
                existing["relationship_type"] == "CITES" and relationship == "AMENDS"
            ):
                rows[key] = {
                    "target_key": key,
                    "relationship_type": relationship,
                    "verified": True,
                    "metadata": {"snippet": snippet},
                }
    return list(rows.values()), unhandled


def _render_children(el: ET.Element, lines: list[str], depth: int) -> None:
    for child in el:
        tag = child.tag
        if tag == "section":
            enum = _norm(child.findtext("enum") or "")
            header = _norm(child.findtext("header") or "")
            lines.append("")
            lines.append(f"## Sec. {enum} {header}".rstrip())
            text_el = child.find("text")
            if text_el is not None:
                lines.append("")
                lines.append(_flat_text(text_el))
            _render_children(child, lines, depth)
        elif tag in _NESTED_LEVELS:
            enum = _norm(child.findtext("enum") or "")
            header = _norm(child.findtext("header") or "")
            text_el = child.find("text")
            body = _flat_text(text_el) if text_el is not None else ""
            label = " ".join(part for part in (enum, header) if part)
            line = f"{'  ' * depth}- {label}" + (f" — {body}" if body else "")
            lines.append(line)
            _render_children(child, lines, depth + 1)
        elif tag == "quoted-block":
            block_lines: list[str] = []
            _render_children(child, block_lines, 0)
            if not block_lines:
                block_lines = [_flat_text(child)]
            lines.append("")
            for bl in block_lines:
                if bl:
                    lines.append(f"> {bl}")
            lines.append("")
        elif tag in {"text", "enum", "header", "after-quoted-block"}:
            continue
        else:
            flat = _flat_text(child)
            if flat and tag not in {"metadata", "endorsement", "form"}:
                lines.append("")
                lines.append(flat)


def bill_xml_to_markdown(xml_bytes: bytes) -> tuple[str, str, str]:
    """Returns (markdown, legis_num, official_title)."""
    root = ET.fromstring(xml_bytes)
    form = root.find("form")
    legis_num = _norm(form.findtext("legis-num") or "") if form is not None else ""
    official_el = form.find("official-title") if form is not None else None
    official = _flat_text(official_el) if official_el is not None else ""

    lines: list[str] = [f"# {legis_num}".rstrip()]
    if official:
        lines.append("")
        lines.append(f"*{official}*")
    body = root.find("legis-body")
    if body is not None:
        _render_children(body, lines, 0)
    markdown = re.sub(r"\n{3,}", "\n\n", "\n".join(lines)).strip() + "\n"
    return markdown, legis_num, official
