"""
Tier 2 software compatibility lookup: for software NOT in the curated
Tier 1 catalog, attempts to resolve compatibility data on demand from
Wikipedia's public API, caches the result, and assigns a confidence
score based on how the data was obtained.

This deliberately does NOT call out to a paid LLM API for extraction --
the original design discussion considered that as an option, but it adds
an external cost and dependency this project doesn't otherwise have.
Instead, this uses Wikipedia's structured "Infobox software" data via
regex extraction, which is free, is a matter of public record, and errs
towards a lower confidence score to reflect its weaker reliability
compared to a human-verified Tier 1 entry.

NOTE: This module makes live HTTP requests to en.wikipedia.org. It has
been validated for correct logic and error handling, but the live network
call itself could not be executed inside the development sandbox (which
restricts outbound domains) -- test it on your own machine, which will
have normal internet access, before relying on it.

Usage:
    from enrichment_pipeline import SoftwareEnrichmentPipeline
    pipeline = SoftwareEnrichmentPipeline()
    pipeline.lookup("Blender")
"""
import re
import requests
from datetime import datetime, timezone

WIKIPEDIA_API = "https://en.wikipedia.org/w/api.php"
REQUEST_TIMEOUT = 8  # seconds -- fail fast rather than hang a user-facing request


class SoftwareEnrichmentPipeline:
    def __init__(self, cache_lookup_fn=None, cache_save_fn=None):
        """
        cache_lookup_fn(name) -> dict or None   -- checks Tier 2 cache (e.g. DB query)
        cache_save_fn(entry: dict) -> None       -- persists a new Tier 2 entry
        Both are injected rather than hardcoded so this can be wired to
        the real SoftwareCache table without this module needing to know
        about SQLAlchemy directly.
        """
        self.cache_lookup_fn = cache_lookup_fn
        self.cache_save_fn = cache_save_fn

    def lookup(self, software_name: str) -> dict:
        if self.cache_lookup_fn:
            cached = self.cache_lookup_fn(software_name)
            if cached:
                return cached

        result = self._wikipedia_lookup(software_name)

        if self.cache_save_fn:
            self.cache_save_fn(result)

        return result

    def _wikipedia_lookup(self, software_name: str) -> dict:
        try:
            page_text, page_url = self._fetch_wikipedia_wikitext(software_name)
        except (requests.RequestException, ValueError) as e:
            return self._unresolved_entry(software_name, reason=str(e))

        if page_text is None:
            return self._unresolved_entry(software_name, reason="No matching Wikipedia article found")

        extracted = self._extract_requirements_from_wikitext(page_text)

        if not extracted:
            return self._unresolved_entry(
                software_name,
                reason="Article found but no structured system requirements detected",
                source_url=page_url,
            )

        return {
            "software_id": self._slugify(software_name),
            "software_name": software_name,
            "min_ram_gb": extracted.get("min_ram_gb"),
            "min_storage_gb": extracted.get("min_storage_gb"),
            "supported_os": extracted.get("supported_os"),
            "gpu_required": extracted.get("gpu_required", False),
            "confidence": "medium",  # structured infobox match, but not human-verified
            "source": "wikipedia_infobox",
            "raw_extraction_text": page_text[:500],
            "source_url": page_url,
            "queried_at": datetime.now(timezone.utc).isoformat(),
            "verified_by_human": False,
        }

    def _fetch_wikipedia_wikitext(self, software_name: str):
        """Fetches raw wikitext for the best-matching article title."""
        search_resp = requests.get(
            WIKIPEDIA_API,
            params={
                "action": "query", "list": "search", "srsearch": software_name,
                "format": "json", "srlimit": 1,
            },
            timeout=REQUEST_TIMEOUT,
        )
        search_resp.raise_for_status()
        search_results = search_resp.json().get("query", {}).get("search", [])
        if not search_results:
            return None, None

        page_title = search_results[0]["title"]

        content_resp = requests.get(
            WIKIPEDIA_API,
            params={
                "action": "query", "prop": "revisions", "titles": page_title,
                "rvslots": "main", "rvprop": "content", "format": "json",
            },
            timeout=REQUEST_TIMEOUT,
        )
        content_resp.raise_for_status()
        pages = content_resp.json().get("query", {}).get("pages", {})
        page = next(iter(pages.values()), {})
        wikitext = page.get("revisions", [{}])[0].get("slots", {}).get("main", {}).get("*", "")

        page_url = f"https://en.wikipedia.org/wiki/{page_title.replace(' ', '_')}"
        return wikitext, page_url

    def _extract_requirements_from_wikitext(self, wikitext: str) -> dict:
        """
        Pulls fields out of a Wikipedia "Infobox software" block using
        regex. This is intentionally simple and conservative -- it is
        designed to avoid false positives (returning nothing rather than
        a wrong number) more than to maximize recall.
        """
        result = {}

        os_match = re.search(r"\|\s*operating system\s*=\s*(.+)", wikitext, re.IGNORECASE)
        if os_match:
            raw_os = re.sub(r"\{\{.*?\}\}|\[\[|\]\]|<br\s*/?>", " ", os_match.group(1))
            os_list = [o.strip() for o in re.split(r",|/", raw_os) if o.strip()]
            if os_list:
                result["supported_os"] = "; ".join(os_list[:5])

        ram_match = re.search(r"(\d+)\s*GB\s*(of\s*)?RAM", wikitext, re.IGNORECASE)
        if ram_match:
            result["min_ram_gb"] = int(ram_match.group(1))

        gpu_match = re.search(r"(OpenGL|DirectX|GPU|graphics card)", wikitext, re.IGNORECASE)
        if gpu_match:
            result["gpu_required"] = True

        return result

    def _unresolved_entry(self, software_name: str, reason: str, source_url: str = None) -> dict:
        return {
            "software_id": self._slugify(software_name),
            "software_name": software_name,
            "min_ram_gb": None,
            "min_storage_gb": None,
            "supported_os": None,
            "gpu_required": None,
            "confidence": "none",
            "source": "unresolved",
            "raw_extraction_text": reason,
            "source_url": source_url,
            "queried_at": datetime.now(timezone.utc).isoformat(),
            "verified_by_human": False,
        }

    @staticmethod
    def _slugify(name: str) -> str:
        return re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")


if __name__ == "__main__":
    # Manual test -- requires real internet access, will not work inside
    # a network-restricted sandbox. Run this file directly on your own
    # machine to verify.
    pipeline = SoftwareEnrichmentPipeline()
    for name in ["Blender", "GIMP", "SomeCompletelyMadeUpSoftwareXYZ123"]:
        print(f"\nLooking up: {name}")
        result = pipeline.lookup(name)
        for k, v in result.items():
            print(f"  {k}: {v}")
