# `export_caselaw` — Federal decisions construing the AECA, the ITAR and the EAR

The judicial gloss. Penalty exposure turns on the willfulness standard, which is a holding rather than a regulation.

Every opinion here had to satisfy two independent gates: matched by NAME and confirmed by SUBJECT. Passing one hides failing the other — matching by name alone put an unrelated 2024 case in the layer, and matching by subject alone filed a real export-control case under the key of a different one.

## Corpora

| Corpus | Prefixes | Weight | Sections |
|---|---|---|---|
| `caselaw` | `case` | `INTERPRETIVE` | 5 |

5 sections, every one verbatim harvested text.

## Provenance

| | |
|---|---|
| Sources | `api.govinfo.gov` · `www.govinfo.gov` |
| Approval status | `harvested_unreviewed` — no attorney review |

## Composition

This is a base pack: it carries authority text and nothing about how
that authority interacts with any other body of law. The orchestration
story lives in a domain pack — see [`DOMAIN_PACKS.md`](../DOMAIN_PACKS.md)
and [`domains/us-export-control/`](../domains/us-export-control/), which
composes this pack with the rest of the US export-control regime.
