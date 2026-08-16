# `ofac` — OFAC sanctions regulations (31 C.F.R. Chapter V)

The sanctions programs, part by part. Carries the RULES only — the SDN List and the other restricted-party rosters are deliberately absent, because screening is a lookup against current list data and a roster frozen at harvest time is worse than no roster at all.

## Corpora

| Corpus | Prefixes | Weight | Sections |
|---|---|---|---|
| `ofac` | `ofac` | `IMPLEMENTING` | 978 |

978 sections, every one verbatim harvested text.

## Provenance

| | |
|---|---|
| Sources | `www.ecfr.gov` |
| Approval status | `harvested_unreviewed` — no attorney review |

## Composition

This is a base pack: it carries authority text and nothing about how
that authority interacts with any other body of law. The orchestration
story lives in a domain pack — see [`DOMAIN_PACKS.md`](../DOMAIN_PACKS.md)
and [`domains/us-export-control/`](../domains/us-export-control/), which
composes this pack with the rest of the US export-control regime.
