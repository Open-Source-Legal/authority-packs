#!/usr/bin/env python3
"""Emit `irc:<section>` -> `fw-res-code:<section>` equivalences for the pack.

Why this exists
---------------
The citation extractor derives a prefix from the abbreviation printed in the
document, so "IRC R311" in a Fort Worth permit guide becomes `irc:r311`. The
`irc` prefix is bound GLOBALLY to the *Internal Revenue Code*, so without these
rows every residential building-code citation is filed under federal tax law.

A regex rewrite rule would be the tidier mechanism, but a pack's
`rewrite_rules` are not loaded (authority_mapping_loader reads `equivalences`
only), so the mapping is expressed as explicit rows.

Only alphanumeric section IDs are mapped (R/N/M/G/P/E + digit). Genuine tax
citations are purely numeric (irc:501(c)(3), irc:1031) and are never touched.
"""
import json
import re
from pathlib import Path

SPEC = (
    Path.home()
    / "Code/Authorities/authority-packs/fort_worth/specs"
    / "fort-worth-residential-code-amendments.json"
)

keys = [s["key"].split(":", 1)[1] for s in json.loads(SPEC.read_text())["sections"]]

# Subsection citations observed in the live corpus that must fall back to the
# amended section this pack actually carries.
OBSERVED_SUBSECTIONS = {
    "r301.2": "r301.2(1)",
    "r317.1": "r317",
    "r317.5": "r317",
    "r318.1": "r318",
    "r322.1": "r322",
    "r327.1.1": "r327",
    "r401.2": "r401",
    "r401.3": "r401",
    "r401.5": "r401",
    "r403.1.1": "r403",
    "r403.4": "r403",
    "r602.6.1": "r602",
}

lines = []
for k in keys:
    if re.match(r"^[rnmgpe]\d", k):
        lines.append(f'  - {{ from_key: "irc:{k}", to_key: "fw-res-code:{k}" }}')

for sub, base in sorted(OBSERVED_SUBSECTIONS.items()):
    if base in keys:
        lines.append(
            f'  - {{ from_key: "irc:{sub}", to_key: "fw-res-code:{base}", '
            f'note: "subsection -> amended section" }}'
        )
        lines.append(
            f'  - {{ from_key: "fw-res-code:{sub}", to_key: "fw-res-code:{base}", '
            f'note: "subsection -> amended section" }}'
        )

print("\n".join(lines))
print(f"\n# {len(lines)} rows", file=__import__("sys").stderr)
