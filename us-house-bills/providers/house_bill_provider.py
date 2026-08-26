"""On-demand fetch of one House bill by canonical key (hr:<congress>-<number>).

Serves the frontier/crawl gap-fill path: a bill cited by an in-window bill (or
any other corpus) that is NOT in the rolling window gets fetched here, so
citations to older or quiet bills still resolve. The continuous
us-house-bill-feed harvester remains the primary ingest path.

Version choice is status-driven, not mtime-driven: BILLSTATUS textVersions
names the latest published version; we then fetch that version's bill-DTD XML
(probing session 2 then 1 — bulkdata splits BILLS by session but not
BILLSTATUS).
"""

from __future__ import annotations

import logging
import re
from typing import ClassVar

from opencontractserver.constants.safe_http import AUTHORITY_PROVIDER_USER_AGENT
from opencontractserver.enrichment.authorities import AuthoritySection
from opencontractserver.enrichment.authority_sources import SourceRelationship
from opencontractserver.pipeline.base.base_authority_source_provider import (
    AuthorityRequest,
    BaseAuthoritySourceProvider,
)
from opencontractserver.utils.safe_http import safe_fetch_bytes

from ..bill_convert import bill_xml_to_markdown, collect_relationships

logger = logging.getLogger(__name__)

_KEY_RE = re.compile(r"^hr:(?P<cong>\d{1,3})-(?P<num>\d{1,5})$")
_BULKDATA = "https://www.govinfo.gov/bulkdata"
_SESSIONS = (2, 1)
_VERSION_FROM_URL_RE = re.compile(r"BILLS-\d+hr\d+([a-z0-9]+)[/.]")


class HouseBillSourceProvider(BaseAuthoritySourceProvider):
    """Fetches a House bill's latest text version from GovInfo bulkdata."""

    title = "U.S. House Bills (govinfo bulkdata)"
    description = (
        "Fetches the latest published text version of a House bill from GPO "
        "govinfo bulkdata (public domain, no API key)."
    )
    license: ClassVar[str] = "public-domain"
    supported_prefixes: ClassVar[tuple[str, ...]] = ("hr",)

    def can_handle(self, canonical_key: str) -> bool:
        # Only congress-qualified keys are fetchable; the shape-level
        # unqualified hr:1234 emitted by the citation grammar resolves via
        # equivalence rows, not via a network fetch.
        return bool(_KEY_RE.match(canonical_key))

    def _locate_impl(self, canonical_key: str, **all_kwargs) -> AuthorityRequest:
        m = _KEY_RE.match(canonical_key)
        if not m:
            raise ValueError(f"Not a congress-qualified House bill key: {canonical_key!r}")
        congress = m.group("cong")
        number = m.group("num")
        status_url = (
            f"{_BULKDATA}/BILLSTATUS/{congress}/hr/BILLSTATUS-{congress}hr{number}.xml"
        )
        return AuthorityRequest(
            canonical_key=canonical_key,
            url=status_url,
            citation=f"H.R. {number} ({congress}th Congress)",
            extra={"congress": congress, "number": number},
        )

    def _fetch_impl(
        self, request: AuthorityRequest, **all_kwargs
    ) -> list[AuthoritySection]:
        import xml.etree.ElementTree as ET

        extra = request.extra or {}
        congress = extra["congress"]
        number = extra["number"]

        status_bytes = self._fetch_bytes(request.url)
        status_root = ET.fromstring(status_bytes)
        bill = status_root.find("bill")
        if bill is None:
            logger.warning("HouseBillProvider: %s is not a BILLSTATUS doc", request.url)
            return []

        version = self._latest_version(bill) or "ih"
        xml_bytes, text_url = self._fetch_bill_xml(congress, number, version)
        if xml_bytes is None:
            logger.warning(
                "HouseBillProvider: no text file found for %s", request.canonical_key
            )
            return []

        markdown, _legis_num, official = bill_xml_to_markdown(xml_bytes)
        text_root = ET.fromstring(xml_bytes)
        relationship_rows, unhandled = collect_relationships(text_root)

        short_title = self._short_title(bill) or official
        latest_action = bill.findtext("latestAction/text")
        section = AuthoritySection(
            key=request.canonical_key,
            heading=f"H.R. {number} — {short_title} ({version.upper()})",
            text=markdown,
            source_url=text_url,
            metadata={
                "congress": int(congress),
                "bill_number": int(number),
                "bill_version": version,
                "sponsor": bill.findtext("sponsors/item/fullName"),
                "introduced_date": bill.findtext("introducedDate"),
                "latest_action": latest_action,
                "latest_action_date": bill.findtext("latestAction/actionDate"),
                "policy_area": bill.findtext("policyArea/name"),
                "short_title": short_title,
                "authority_weight": "PROPOSED",
                "instrument_type": "BILL",
                "unhandled_cite_tally": unhandled,
            },
            relationships=tuple(
                SourceRelationship(
                    target_key=row["target_key"],
                    relationship_type=row["relationship_type"],
                    verified=row["verified"],
                    metadata=row["metadata"],
                )
                for row in relationship_rows
            ),
        )
        return [section]

    # ---- seams (patched in tests) ----------------------------------------- #

    def _fetch_bytes(self, url: str) -> bytes:
        body, _host = safe_fetch_bytes(
            url, headers={"User-Agent": AUTHORITY_PROVIDER_USER_AGENT}
        )
        return body

    def _fetch_bill_xml(
        self, congress: str, number: str, version: str
    ) -> tuple[bytes | None, str]:
        """Try the named version across sessions; fall back through earlier
        versions (rare: a status names a version whose file is not yet up)."""
        for ver in (version, "enr", "eh", "rh", "ih"):
            for session in _SESSIONS:
                url = (
                    f"{_BULKDATA}/BILLS/{congress}/{session}/hr/"
                    f"BILLS-{congress}hr{number}{ver}.xml"
                )
                try:
                    return self._fetch_bytes(url), url
                except Exception:  # noqa: BLE001 — probe misses are expected; the terminal miss is reported by the caller
                    continue
        return None, ""

    # ---- BILLSTATUS helpers ----------------------------------------------- #

    @staticmethod
    def _latest_version(bill) -> str | None:
        versions: list[tuple[str, str]] = []
        for item in bill.findall("textVersions/item"):
            date = item.findtext("date") or ""
            for fmt in item.findall("formats/item"):
                url = fmt.findtext("url") or ""
                m = _VERSION_FROM_URL_RE.search(url)
                if m:
                    versions.append((date, m.group(1)))
                    break
        if not versions:
            return None
        versions.sort()
        return versions[-1][1]

    @staticmethod
    def _short_title(bill) -> str | None:
        for item in bill.findall("titles/item"):
            if "short title" in (item.findtext("titleType") or "").lower():
                if item.findtext("title"):
                    return item.findtext("title")
        display = bill.findtext("title")
        if display and not display.startswith("To "):
            return display
        return None
