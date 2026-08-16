# `export_fedreg` — Export-control rulemaking record and executive orders

Rule PREAMBLES — where the agency answers comments and says what a term means — plus the executive orders that delegate the statutory authority in the first place. The preamble is the best interpretive source in this field and exists nowhere in the codified text.

Named `export_fedreg`, not `fedreg`: this is the export-control slice of the Federal Register (State, BIS, OFAC, 2013-present), not the Federal Register. Another domain's slice is a different pack.

## Corpora

| Corpus | Prefixes | Weight | Sections |
|---|---|---|---|
| `fr` | `fr` | `INTERPRETIVE` | 745 |
| `eo` | `eo` | `CONTROLLING` | 156 |

901 sections, every one verbatim harvested text.

## Provenance

| | |
|---|---|
| Sources | `www.federalregister.gov` |
| Approval status | `harvested_unreviewed` — no attorney review |

## Composition

This is a base pack: it carries authority text and nothing about how
that authority interacts with any other body of law. The orchestration
story lives in a domain pack — see [`DOMAIN_PACKS.md`](../DOMAIN_PACKS.md)
and [`domains/us-export-control/`](../domains/us-export-control/), which
composes this pack with the rest of the US export-control regime.
