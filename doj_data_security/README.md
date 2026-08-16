# `doj_data_security` — DOJ Data Security Program (28 C.F.R. Part 202)

Access to bulk U.S. sensitive personal data and government-related data by countries of concern and covered persons. Overlaps export-control reasoning about foreign-person access without being the same test, which is exactly why it needs to be quotable rather than remembered.

## Corpora

| Corpus | Prefixes | Weight | Sections |
|---|---|---|---|
| `dsp` | `dsp` | `IMPLEMENTING` | 104 |

104 sections, every one verbatim harvested text.

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
