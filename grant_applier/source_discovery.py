"""Official source discovery and source index updates."""

from __future__ import annotations

import json
import re
import urllib.parse
import urllib.request
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Any

from .analyzer import render_yaml
from .discovery import Opportunity, list_local_source_files
from .profiles import ensure_profile

DEFAULT_TIMEOUT_SECONDS = 12

AGENCY_DOMAINS: dict[str, list[str]] = {
    "National Science Foundation": ["new.nsf.gov", "nsf.gov"],
    "Department of Education": ["ed.gov"],
    "USDA NIFA": ["nifa.usda.gov"],
    "Department of Justice / National Institute of Justice": ["nij.ojp.gov", "ojp.gov"],
    "HHS / ACL / NIDILRR": ["acl.gov", "hhs.gov"],
    "Department of State": ["state.gov", "usembassy.gov"],
}


@dataclass(frozen=True)
class SourceCandidate:
    title: str
    url: str
    source_type: str
    verified: bool
    notes: str

    def as_dict(self) -> dict[str, Any]:
        return {
            "title": self.title,
            "url": self.url,
            "local_path": None,
            "source_type": self.source_type,
            "retrieved_date": date.today().isoformat(),
            "verified": self.verified,
            "notes": self.notes,
        }


def run_source_discovery(
    opportunity: Opportunity,
    overwrite: bool = False,
    online: bool = True,
) -> dict[str, Any]:
    profile = ensure_profile(opportunity, overwrite=False)
    opportunity_number = str(profile.get("opportunity_number", opportunity.opportunity_folder))
    funder = str(profile.get("funder", "[CONFIRM]"))

    local_sources = list_local_source_files(opportunity.path)
    local_rel_paths = [str(path.relative_to(opportunity.path)) for path in local_sources]

    candidates = build_seed_candidates(funder, opportunity_number)
    if online:
        candidates.extend(search_duckduckgo_candidates(funder, opportunity_number))

    deduped = dedupe_candidates(candidates)
    official_verified = any(candidate.verified for candidate in deduped)
    full_nofo_found = any(
        marker in (candidate.title + " " + candidate.url).lower()
        for marker in ("nofo", "solicitation", "funding opportunity", "rfa", "program solicitation")
        for candidate in deduped
    )

    sources_path = opportunity.path / "Sources" / "sources.json"
    merged_sources = merge_sources_json(
        sources_path=sources_path,
        local_relative_paths=local_rel_paths,
        candidates=deduped,
        overwrite=overwrite,
    )
    sources_path.parent.mkdir(parents=True, exist_ok=True)
    sources_path.write_text(json.dumps(merged_sources, indent=2), encoding="utf-8")

    write_source_index(opportunity, local_rel_paths, deduped)
    write_source_research(opportunity, funder, opportunity_number, deduped)

    profile.setdefault("source_status", {})
    profile["source_status"]["official_funder_page_found"] = official_verified
    profile["source_status"]["full_nofo_found"] = bool(
        profile["source_status"].get("full_nofo_found", False) or full_nofo_found
    )
    profile["source_status"]["local_grants_gov_notice_found"] = bool(
        profile["source_status"].get("local_grants_gov_notice_found", False)
    )

    (opportunity.path / "Analysis").mkdir(parents=True, exist_ok=True)
    (opportunity.path / "Analysis" / "opportunity_profile.json").write_text(
        json.dumps(profile, indent=2), encoding="utf-8"
    )
    (opportunity.path / "Analysis" / "opportunity_profile.yaml").write_text(
        render_yaml(profile).rstrip() + "\n", encoding="utf-8"
    )
    return profile


def build_seed_candidates(funder: str, opportunity_number: str) -> list[SourceCandidate]:
    encoded = urllib.parse.quote_plus(opportunity_number)
    seeds: list[SourceCandidate] = [
        SourceCandidate(
            title=f"Grants.gov opportunity search for {opportunity_number}",
            url=f"https://www.grants.gov/search-results-detail/{encoded}",
            source_type="grants_gov_listing_candidate",
            verified=False,
            notes="Candidate constructed from opportunity number; verify manually.",
        )
    ]
    for domain in AGENCY_DOMAINS.get(funder, []):
        query = urllib.parse.quote_plus(f'site:{domain} "{opportunity_number}"')
        seeds.append(
            SourceCandidate(
                title=f"Potential official listing on {domain}",
                url=f"https://duckduckgo.com/?q={query}",
                source_type="official_search_query",
                verified=False,
                notes="Search query URL to locate authoritative funder source.",
            )
        )
    return seeds


def search_duckduckgo_candidates(funder: str, opportunity_number: str) -> list[SourceCandidate]:
    domains = AGENCY_DOMAINS.get(funder, [])
    queries = [
        f'"{opportunity_number}" NOFO',
        f'"{opportunity_number}" funding opportunity',
        f'"{opportunity_number}" application instructions',
        f'site:grants.gov "{opportunity_number}"',
    ]
    for domain in domains:
        queries.append(f'site:{domain} "{opportunity_number}"')

    collected: list[SourceCandidate] = []
    for query in queries:
        url = "https://duckduckgo.com/html/?" + urllib.parse.urlencode({"q": query})
        try:
            request = urllib.request.Request(
                url=url,
                headers={"User-Agent": "Mozilla/5.0 grant-applier-bot"},
            )
            with urllib.request.urlopen(request, timeout=DEFAULT_TIMEOUT_SECONDS) as response:
                body = response.read().decode("utf-8", errors="ignore")
        except Exception:
            continue

        for title, link in extract_duckduckgo_results(body):
            if not link.startswith("http"):
                continue
            is_official = bool(domains) and any(f"://{domain}" in link or f".{domain}/" in link for domain in domains)
            if "grants.gov" in link:
                source_type = "grants_gov_listing"
            elif is_official:
                source_type = "official_funder_page"
            else:
                source_type = "supporting_source"
            verified = verify_url(link)
            collected.append(
                SourceCandidate(
                    title=title[:180] if title else f"Search result for {opportunity_number}",
                    url=link,
                    source_type=source_type,
                    verified=verified,
                    notes=f'Found via query: {query}',
                )
            )
    return collected


def extract_duckduckgo_results(html: str) -> list[tuple[str, str]]:
    pattern = re.compile(
        r'<a[^>]*class="result__a"[^>]*href="(?P<href>[^"]+)"[^>]*>(?P<title>.*?)</a>',
        re.IGNORECASE | re.DOTALL,
    )
    results: list[tuple[str, str]] = []
    for match in pattern.finditer(html):
        href = html_unescape(strip_tags(match.group("href")))
        title = html_unescape(strip_tags(match.group("title")))
        decoded = decode_duckduckgo_redirect(href)
        results.append((title, decoded))
    return results


def decode_duckduckgo_redirect(url: str) -> str:
    if "duckduckgo.com/l/?" not in url:
        return url
    parsed = urllib.parse.urlparse(url)
    query = urllib.parse.parse_qs(parsed.query)
    if "uddg" in query and query["uddg"]:
        return query["uddg"][0]
    return url


def verify_url(url: str) -> bool:
    try:
        request = urllib.request.Request(
            url=url,
            headers={"User-Agent": "Mozilla/5.0 grant-applier-bot"},
        )
        with urllib.request.urlopen(request, timeout=DEFAULT_TIMEOUT_SECONDS):
            return True
    except Exception:
        return False


def merge_sources_json(
    sources_path: Path,
    local_relative_paths: list[str],
    candidates: list[SourceCandidate],
    overwrite: bool,
) -> list[dict[str, Any]]:
    existing: list[dict[str, Any]] = []
    if sources_path.exists() and not overwrite:
        try:
            existing = json.loads(sources_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            existing = []

    today = date.today().isoformat()
    merged_by_key: dict[str, dict[str, Any]] = {}
    for record in existing:
        key = source_key(record.get("local_path"), record.get("url"))
        merged_by_key[key] = record
    for relative_path in local_relative_paths:
        record = {
            "title": Path(relative_path).name,
            "url": None,
            "local_path": relative_path,
            "source_type": "local_source",
            "retrieved_date": today,
            "verified": True,
            "notes": "Local source file available in opportunity folder.",
        }
        merged_by_key[source_key(relative_path, None)] = record
    for candidate in candidates:
        record = candidate.as_dict()
        merged_by_key[source_key(None, candidate.url)] = record
    return sorted(
        merged_by_key.values(),
        key=lambda item: (item.get("source_type", ""), item.get("title", "")),
    )


def write_source_index(
    opportunity: Opportunity,
    local_relative_paths: list[str],
    candidates: list[SourceCandidate],
) -> None:
    local_items = "\n".join(f"- `{path}`" for path in local_relative_paths) or "- [TODO] No local files."
    official_lines = []
    for candidate in candidates[:25]:
        official_lines.append(
            f"- [{candidate.title}]({candidate.url}) "
            f"(type: `{candidate.source_type}`, verified: `{candidate.verified}`)"
        )
    if not official_lines:
        official_lines.append("- [TODO] No official candidate sources discovered automatically.")

    text = f"""# Source Index

## Local Sources

{local_items}

## Official and Candidate Sources

{chr(10).join(official_lines)}

## Research Notes

- Candidate links must be reviewed by a human before submission use.
- Use official funder and policy sources as the authoritative requirement basis.
"""
    path = opportunity.path / "Sources" / "source_index.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text.rstrip() + "\n", encoding="utf-8")


def write_source_research(
    opportunity: Opportunity,
    funder: str,
    opportunity_number: str,
    candidates: list[SourceCandidate],
) -> None:
    agency_domains = ", ".join(AGENCY_DOMAINS.get(funder, [])) or "[CONFIRM]"
    lines = [
        "# Source Research Log",
        "",
        f"- Funder: `{funder}`",
        f"- Opportunity number: `{opportunity_number}`",
        f"- Preferred official domains: `{agency_domains}`",
        "",
        "## Candidate Results",
        "",
    ]
    if not candidates:
        lines.extend(["- [TODO] No web candidates discovered automatically.", ""])
    else:
        for candidate in candidates[:40]:
            lines.append(
                f"- `{candidate.source_type}` | verified=`{candidate.verified}` | "
                f"[{candidate.title}]({candidate.url})"
            )
    lines.extend(
        [
            "",
            "## Human Verification Required",
            "",
            "- [ ] Confirm the primary official NOFO/solicitation URL.",
            "- [ ] Confirm the agency policy manual URL used for compliance decisions.",
            "- [ ] Confirm retrieval date and archive copies where required.",
        ]
    )
    path = opportunity.path / "Sources" / "source_research.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")


def dedupe_candidates(candidates: list[SourceCandidate]) -> list[SourceCandidate]:
    by_url: dict[str, SourceCandidate] = {}
    for candidate in candidates:
        by_url[candidate.url] = candidate
    return sorted(by_url.values(), key=lambda item: item.url)


def source_key(local_path: str | None, url: str | None) -> str:
    if url:
        return f"url::{url}"
    return f"path::{local_path}"


def strip_tags(value: str) -> str:
    return re.sub(r"<[^>]+>", "", value)


def html_unescape(value: str) -> str:
    return (
        value.replace("&amp;", "&")
        .replace("&quot;", '"')
        .replace("&#x27;", "'")
        .replace("&#39;", "'")
        .replace("&lt;", "<")
        .replace("&gt;", ">")
    )
