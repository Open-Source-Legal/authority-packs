# `cfius` — CFIUS / FIRRMA (31 C.F.R. Parts 800, 802)

Inbound investment review. Shares CFR title 31 with OFAC, which is a trap rather than a convenience: a namespace alias maps a whole title to one prefix, so `31 C.F.R. § 800.215` extracts as `ofac:800.215` and resolves to nothing. The folding rows that fix it span two packs and therefore live in the domain layer, not here.

## Corpora

| Corpus | Prefixes | Weight | Sections |
|---|---|---|---|
| `cfius` | `cfius` | `IMPLEMENTING` | 194 |

194 sections, every one verbatim harvested text.

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
