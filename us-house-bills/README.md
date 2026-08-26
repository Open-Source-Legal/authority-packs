# `us-house-bills` — U.S. House Bills (119th Congress, rolling window)

Proposed legislation as an authority corpus: the latest published text version
of every H.R. with recent activity, keyed `hr:119-<number>`, with **verified
AMENDS/CITES relationships** parsed from GPO's own `parsable-cite` markup — so
"what does this bill change" is a graph edge, not a guess.

## Corpora

| Corpus | Prefixes | Weight | Sections |
|---|---|---|---|
| `house-bills-119` | `hr` | `PROPOSED` | 6 (seed) + continuous feed |

**Content is PROPOSED LEGISLATION, not law** — `PROPOSED` weight, and the
persona keeps the proposed/enacted line drawn. **Silence semantics are the
opposite of full-coverage packs**: an absent bill is usually outside the
rolling window, never proof it doesn't exist.

## Content flow

1. **Seed** (`specs/house-bills-119.json`): a handful of currently-active
   bills so the corpus is alive at install.
2. **Continuous**: the private
   [`us-house-bill-feed`](https://github.com/Open-Source-Legal/us-house-bill-feed)
   harvester pushes rolling-window payloads to
   `POST /api/worker-uploads/authority-sections/` under a corpus token.
3. **Gap-fill**: `providers/house_bill_provider.py` fetches a cited-but-absent
   bill on demand (frontier/crawl), status-driven version choice.

Unqualified citations ("H.R. 1234" → grammar key `hr:1234`) fold onto the
current congress via equivalence rows — seeded here, continuously upserted by
the ingest drain, re-pointed each congress.

## Provenance

| | |
|---|---|
| Sources | `www.govinfo.gov` (bulkdata BILLS bill-DTD XML + BILLSTATUS) |
| Approval status | `harvested_unreviewed` — no attorney review |

## Platform requirements

Needs OpenContracts with the house-bills core seams (bill citation grammar,
`AUTHORITY_TYPE_BILL`, `AuthorityWeight.PROPOSED`, authority-section push
endpoint) — Open-Source-Legal/OpenContracts PR #2279.
