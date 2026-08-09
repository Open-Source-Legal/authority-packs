# Fort Worth, Texas — Municipal Law & Procurement Authority Pack

A schema-v2 authority pack covering the law that City of Fort Worth contracts
actually cite. Built for (and validated against) a corpus of the City
Secretary's public contract records, where the recurring citations are the
city's own contract-execution ordinance, its business-equity and
anti-discrimination clauses, and the Texas procurement and
contract-verification statutes.

## Contents

| Corpus (slug) | Prefix(es) | Sections | Source |
|---|---|---|---|
| `fort-worth-city-code` | `muni-fort-worth` | 85 | Code of Ordinances: Ch. 2 Art. I (incl. § 2-9 contract execution and its $100,000 city-manager threshold), Ch. 2 Art. VII (Code of Ethics), Ch. 17 (Human Relations, incl. Art. III discrimination-in-employment provisions), Ch. 20 Art. X (Business Equity), Ch. 21 (Small Business Program) |
| `fort-worth-charter` | `fw-charter` | 34 | City Charter: Ch. V (City Manager), Ch. X (Budget & Financial Procedure), Ch. XXVII (Miscellaneous), Ch. XXVIII (Internal Audit) |
| `texas-procurement-law` | `tx-local-gov`, `tx-gov` | 28 | Tex. Loc. Gov't Code chs. 176, 252, 271 subch. F; Tex. Gov't Code § 2252.908 and chs. 2271, 2274, 2276, plus chapter-level overview documents so chapter-style citations resolve |

A fifth namespace, `tx-admin-code`, is declared for classification only (no
seeded corpus).

## Design notes

- **Citation reality drives the taxonomy.** Fort Worth contract templates cite
  chapters, not sections ("Chapter 252 of the Local Government Code",
  "Chapter 2271 of the Texas Government Code"), and OCR of scanned contracts
  garbles section markers. The pack therefore ships (a) chapter-level spec
  documents (`tx-local-gov:252`, `tx-gov:2271`, …) so chapter citations have a
  resolution target, and (b) `equivalences` folding the LLM tier's predictable
  `act:<slug>` keys (e.g. `act:chapter-2271-of-the-texas-government-code`,
  including observed OCR-noise variants) onto those canonical keys.
- **`muni-fort-worth`** matches the slug the open-vocabulary municipal grammar
  already derives from "Fort Worth Code of Ordinances § N", so table-keyed and
  open-vocab detections converge on one authority. `abbreviations` add the
  spellings the open-vocab regex cannot reach ("Fort Worth City Code",
  "City Code of the City of Fort Worth") plus the spelled-out Texas code names.
- **The `texas-procurement-law` spec deliberately has no spec-level
  `aliases`.** Spec aliases stamp `custom_meta.authority_aliases` onto every
  document in the corpus and map each alias to that document's own key prefix —
  in a corpus mixing `tx-local-gov` and `tx-gov` documents this mis-mapped
  "texas government code" → `tx-local-gov` in the alias registry (per-document
  aliases take precedence over namespace rows). Namespace aliases in the
  mappings YAML carry Tier-1 for this corpus instead.
- `tx-gov:2270` exists as a pointer document: contracts still cite former
  Chapter 2270 (renumbered 2271), and an equivalence folds `tx-gov:2270` →
  `tx-gov:2271`.

## Provenance

- City Code and Charter text: American Legal Publishing's codelibrary
  (`codelibrary.amlegal.com/codes/ftworth`), current through supplement S-20
  (2026), captured 2026-08-09. Section text is verbatim, including ordinance
  history notes.
- Texas statutes: verbatim from `texas.public.law` mirrors, verified against
  Wayback captures of the official `statutes.capitol.texas.gov` chapter pages
  (zero text mismatches; mirror-added cross-reference chrome stripped).
- Chapter-level "(chapter overview)" documents are curated summaries written
  for this pack and labeled as such in their headings; all other section text
  is verbatim law.

## Install

From an OpenContracts deployment:

```bash
python manage.py install_authority_pack fort_worth --creator <username> --check   # preflight
python manage.py install_authority_pack fort_worth --creator <username> --public  # --public matters:
                                   # a public filing corpus only resolves against public authority docs
```

Or manually, from a clone of this repo:

```bash
python manage.py load_authority_pack --path /path/to/authority-packs/fort_worth \
  --creator <username> --public
```

Workers must restart after install for the pack's `abbreviations` to reach the
grammar tier (the pack-config loader is `lru_cache`d).
