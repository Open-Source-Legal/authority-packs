# Fort Worth, Texas — Municipal Law, Procurement & Residential Construction

A schema-v2 authority pack covering two bodies of Fort Worth law.

**Contracting** — the law that City of Fort Worth contracts actually cite.
Built for (and validated against) a corpus of the City Secretary's public
contract records, where the recurring citations are the city's own
contract-execution ordinance, its business-equity and anti-discrimination
clauses, and the Texas procurement and contract-verification statutes.

**Residential construction and permitting** — the law a homeowner runs into
when they pull a permit or do the work themselves: what needs a permit, what
Fort Worth changed in the model codes, where a structure may sit on the lot,
and whether the owner may lawfully do the work.

## Contents

| Corpus (slug) | Prefix(es) | Sections | Source |
|---|---|---|---|
| `fort-worth-city-code` | `muni-fort-worth` | 317 | Code of Ordinances. *Contracting:* Ch. 2 Art. I (incl. § 2-9 contract execution and its $100,000 city-manager threshold), Ch. 2 Art. VII (Code of Ethics), Ch. 17 (Human Relations), Ch. 20 Art. X (Business Equity), Ch. 21 (Small Business Program). *Construction:* Ch. 7 (Buildings) in full — technical-code adoptions and amendments, Minimum Building Standards Code, demolition, floodplain, one- and two-family dwelling registration — plus Ch. 11 (Electricity), Ch. 15 (Gas), Ch. 26 (Plumbing) |
| `fort-worth-charter` | `fw-charter` | 34 | City Charter: Ch. V (City Manager), Ch. X (Budget & Financial Procedure), Ch. XXVII (Miscellaneous), Ch. XXVIII (Internal Audit) |
| `fort-worth-building-admin-code` | `fw-admin-code` | 19 | Fort Worth Building Administrative Code §§ 101–119 as adopted by City Code § 7-1: § 105 Permits (and the work exempt from permit), § 109 Fees, § 110 Inspections, § 111 Certificate of Occupancy, § 118 Contractor Registration, § 119 Fee Tables |
| `fort-worth-residential-code-amendments` | `fw-res-code` | 53 | Fort Worth's local amendments to the 2021 IRC (Ord. 25383-03-2022, codified at § 7-62), keyed by the amended IRC section across the R/N/M/G/P series |
| `fort-worth-zoning` | `fw-zoning` | 157 | Zoning Ordinance (Appendix A) chs. 1, 3 (review procedures), 4 (district regulations incl. the one-family districts), 5 (supplemental use standards), 6 (development standards incl. fences and screening), 9 (definitions) |
| `texas-residential-trades` | `tx-occ`, `tx-prop` | 273 | Tex. Occ. Code chs. 1301 (plumbing, incl. § 1301.051 homestead exemption), 1302, 1305 (electricians, incl. § 1305.003 exemptions); Tex. Prop. Code chs. 202 (restrictive covenants, incl. § 202.010 solar) and 209 |
| `texas-procurement-law` | `tx-local-gov`, `tx-gov` | 28 | Tex. Loc. Gov't Code chs. 176, 252, 271 subch. F; Tex. Gov't Code § 2252.908 and chs. 2271, 2274, 2276, plus chapter-level overview documents so chapter-style citations resolve |

An eighth namespace, `tx-admin-code`, is declared for classification only (no
seeded corpus).

## Adopted code editions (as of 2026-08-09)

The editions are of **mixed vintage** — assuming "2021 everything" is wrong:

| Code | Edition | Adopting authority |
|---|---|---|
| Residential (IRC) | 2021 | § 7-61; Ord. 25383-03-2022 |
| Building (IBC) | 2021 | § 7-46; Ord. 25382-03-2022 |
| Mechanical (IMC) | 2021 | Ord. 25384-03-2022 |
| Plumbing / Fuel Gas (IPC/IFGC) | 2021 | Ord. 25385-03-2022 |
| Existing Building (IEBC) | 2021 | Ord. 25386-03-2022 |
| Energy (IECC) | **2015** | § 7-41 |
| Swimming Pool and Spa (ISPSC) | **2018** | Ch. 7 Art. XII |
| Electrical (NEC) | **2023** | Ch. 11 |

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

### Residential construction

- **The International Residential Code must not use the prefix `irc`.** That
  prefix is already bound, globally, to the **Internal Revenue Code**. The
  residential code uses `fw-res-code`, and bare `"irc"` is deliberately not
  registered as an alias for the same collision reason.
- **One municipal code, one corpus.** A namespace prefix binds to exactly one
  corpus, so Chapter 7 extends the existing `muni-fort-worth` corpus rather
  than creating a rival "Fort Worth building code" corpus. A rival corpus would
  actively break resolution: the alias "Fort Worth City Code" already maps to
  `muni-fort-worth`, so a citation to § 7-61 would resolve into the existing
  corpus and find nothing.
- **§ 7-1 is a pointer, not a duplicate.** § 7-1 adopts the Building
  Administrative Code and reproduces it in full (~165k chars). That text is
  carried, decomposed by its own section numbers, in
  `fort-worth-building-admin-code`. Keeping both verbatim would return every
  permit answer twice, so § 7-1 keeps its adopting language and an editorial
  note pointing at `fw-admin-code:101`–`119`.
- **Only Fort Worth's amendments to the model codes are reproduced**, never the
  ICC base text. Where Fort Worth has not amended a section, the corpus is
  silent and the base code governs — the personas require the agent to say so
  rather than infer a local rule. Under *Veeck v. SBCCI* (5th Cir. 2002, en
  banc) a model code adopted as law enters the public domain in this circuit,
  so this is a conservative editorial choice rather than a legal necessity.
- **The two homeowner exemptions are not symmetrical**, and the
  `texas-residential-trades` persona exists largely to keep them apart:
  § 1301.051 exempts a property owner from plumbing *licensure* in their own
  homestead unconditionally; § 1305.003(a)(6) reaches electrical work in an
  owner-occupied dwelling only where that work is "not specifically regulated
  by a municipal ordinance." Neither waives a Fort Worth permit or inspection.
- **Fees.** § 109 and § 119 carry the codified ordinance fee tables, which are
  law. The city's separately published Development Fees Schedule is revised
  more often and belongs in a document corpus, not here; the persona requires
  any dollar figure to be flagged verify-with-Development-Services.
- The zoning corpus does not know any parcel's district, and most dimensional
  answers depend on it — the persona requires that assumption to be stated.
  Historic and urban-design overlays are flagged, not modelled.

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
- Residential-construction additions (captured 2026-08-09): City Code chs. 7,
  11, 15, 26 and Zoning Appendix A verbatim from `codelibrary.amlegal.com`;
  Tex. Occ. Code chs. 1301/1302/1305 and Tex. Prop. Code chs. 202/209 verbatim
  from the official `statutes.capitol.texas.gov` chapter pages.
- The Occupations Code genuinely carries **two distinct sections numbered
  § 1301.258** (Advisory Committees; Board Committees), enacted by different
  acts. Both are reproduced under the one key with a note, since a citation to
  that number reaches both.
- The only editorial insertions are the § 7-1 pointer note and the § 1301.258
  duplicate-numbering note; both are bracketed and labeled.

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
