# `ear` — Export Administration Regulations and the Commerce Control List

The dual-use half of the system: scope and the ITAR carve-out (Part 734), de minimis, deemed exports, the ten General Prohibitions (Part 736), the Country Chart (Part 738), Part 772 definitions one document per defined term, and every ECCN as its own addressable document.

ECCN keys are LOWERCASE (`ccl:3a611`). Authority-key matching is case-sensitive on the section part and the extractor lowercases what it finds, so an ECCN keyed the conventional uppercase way is unreachable from every real citation.

## Corpora

| Corpus | Prefixes | Weight | Sections |
|---|---|---|---|
| `ear-regulations` | `ear` | `IMPLEMENTING` | 626 |
| `ccl` | `ccl` | `IMPLEMENTING` | 644 |

1,270 sections, every one verbatim harvested text.

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
