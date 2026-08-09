# OpenContracts Authority Packs

Curated bodies of law for [OpenContracts](https://github.com/Open-Source-Legal/OpenContracts)
citation enrichment: each top-level directory is a schema-v2 **authority pack** —
a citation taxonomy (namespaces, aliases, equivalences, grammar abbreviations)
plus seeded corpora of verbatim law, installable into any OpenContracts
deployment.

Packs live here, out of the platform repo, so deployments install only the
jurisdictions they want and the platform's MIT license stays untangled from
pack content licensing.

## Installing a pack

From an OpenContracts checkout (fetches from this repo, validates, installs):

```bash
python manage.py install_authority_pack fort_worth --creator <username> --public
```

Useful variants:

```bash
python manage.py install_authority_pack --list                 # what's available
python manage.py install_authority_pack fort_worth --check     # fetch + preflight only
python manage.py install_authority_pack fort_worth --ref main --creator <u> --public
```

Restart celery workers after install — the grammar-tier pack config is cached
per process.

Manual alternative (no management command): clone this repo wholesale and point
`AUTHORITY_PACK_ROOTS` at the clone; every directory containing a `pack.yaml`
is auto-discovered.

```bash
git clone https://github.com/Open-Source-Legal/authority-packs /srv/authority-packs
export AUTHORITY_PACK_ROOTS=/srv/authority-packs
python manage.py load_authority_pack --path /srv/authority-packs/fort_worth --creator <u> --public
```

## Catalog

| Pack | Jurisdiction | Corpora | Sections |
|---|---|---|---|
| [`fort_worth`](fort_worth/) | City of Fort Worth, Texas (us-tx-fort-worth) | City Code procurement provisions · City Charter (selected chapters) · Texas procurement & contract-verification statutes | 147 |

Each pack's `README.md` documents its contents, provenance, and design notes.

## Licensing

Pack content in this repository is licensed under
[**CC BY-SA 4.0**](LICENSE) (Creative Commons Attribution-ShareAlike).

Two important qualifications:

1. **The law itself is not ours to license.** Statutes, ordinances, charters,
   and other edicts of government are in the public domain (*Veeck v. SBCCI*,
   293 F.3d 791 (5th Cir. 2002) (en banc); *Georgia v. Public.Resource.Org*,
   590 U.S. 255 (2020)). The verbatim legal text inside a pack may be copied
   freely by anyone, from any source. CC BY-SA applies to what we authored:
   the selection and arrangement, citation taxonomies, alias and equivalence
   mappings, chapter overviews, personas, charters, and other editorial
   apparatus.
2. **Attribution** for the authored apparatus: "OpenContracts Authority Packs,
   Open-Source-Legal" with a link back to this repository satisfies the BY
   requirement.

The OpenContracts platform itself remains MIT-licensed; packs are data loaded
at runtime and impose no licensing obligation on the platform or on
deployments' own documents.

## Authoring new packs

See the OpenContracts guide:
[`docs/guides/authoring-authority-packs.md`](https://github.com/Open-Source-Legal/OpenContracts/blob/main/docs/guides/authoring-authority-packs.md).
The in-tree `bolivia` pack and `example_utility` test fixture remain the
minimal worked examples; packs here are the real-jurisdiction catalog.
