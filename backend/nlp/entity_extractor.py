"""
Extracts LOCATION, TARGET_OS, SOFTWARE, and CONDITION entities from a query.

Approach: dictionary/pattern matching against your actual reference data
(real lab names, the 67 OS names, the 122 software names) rather than a
generic NER model. This guarantees every extracted entity is one your
system actually knows about -- it cannot "hallucinate" an OS or software
title that doesn't exist in your database, which a generic transformer
NER model could do.

Usage:
    from entity_extractor import EntityExtractor
    extractor = EntityExtractor()
    extractor.extract("Show all computers in Block C that cannot run Windows 11")
    # -> {"location": "Block C", "target_os": "Windows 11", "software": None, "condition": None}
"""
import re
import pandas as pd
from pathlib import Path

# Resolve paths relative to THIS file's location, not the current working
# directory -- so this works whether you run `python entity_extractor.py`,
# `uvicorn main:app` from backend/, or anything else.
DATA_DIR = Path(__file__).parent.parent.parent / "data"


class EntityExtractor:
    def __init__(
        self,
        os_requirements_path=None,
        software_requirements_path=None,
        software_cache_path=None,
        locations_path=None,
    ):
        os_requirements_path = os_requirements_path or DATA_DIR / "os_requirements.csv"
        software_requirements_path = software_requirements_path or DATA_DIR / "software_requirements.csv"
        software_cache_path = software_cache_path or DATA_DIR / "software_cache.csv"
        locations_path = locations_path or DATA_DIR / "campus_spatial_data.csv"

        osr = pd.read_csv(os_requirements_path)
        sw1 = pd.read_csv(software_requirements_path)
        sw2 = pd.read_csv(software_cache_path)
        loc = pd.read_csv(locations_path)

        # Sort longest-first so "Windows 11" matches before a hypothetical "Windows"
        self.os_names = sorted(osr["os_name"].dropna().unique(), key=len, reverse=True)
        self.software_names = sorted(
            set(sw1["software_name"].dropna()) | set(sw2["software_name"].dropna()),
            key=len, reverse=True
        )
        self.block_names = sorted(loc["block_name"].dropna().unique(), key=len, reverse=True)
        self.lab_names = sorted(loc["lab_name"].dropna().unique(), key=len, reverse=True)
        # Known ambiguous/generic location references seen in the dataset (see cleaning notes)
        self.generic_locations = ["Lab 1", "Lab 2"]

        # Known real-world shorthand for full catalog names -- without this,
        # dictionary matching fails on very common abbreviations (a genuine
        # limitation surfaced by the hand-written stress test; see
        # evaluation/nlp_stress_test.py).
        self.aliases = {
            "win11": "Windows 11",
            "win10": "Windows 10",
            "windows11": "Windows 11",
            "windows10": "Windows 10",
            "photoshop": "Adobe Photoshop",
            "premiere": "Adobe Premiere Pro",
            "vscode": "Visual Studio Code",
            "vs code": "Visual Studio Code",
        }

        self.condition_patterns = [
            (r"older than (\d+) years?", "age_gt_{}"),
            (r"more than (\d+) years? old", "age_gt_{}"),
            (r"less than (\d+)\s?gb ram", "ram_lt_{}gb"),
            (r"at least (\d+)\s?gb ram", "ram_gte_{}gb"),
        ]

    def _find_first_match(self, text: str, candidates: list[str]) -> str | None:
        text_lower = text.lower()
        for c in candidates:
            if c.lower() in text_lower:
                return c
        return None

    def _find_with_aliases(self, text: str, candidates: list[str]) -> str | None:
        direct = self._find_first_match(text, candidates)
        if direct:
            return direct
        text_lower = text.lower()
        for alias, canonical in self.aliases.items():
            if alias in text_lower and canonical in candidates:
                return canonical
        return None

    def extract(self, text: str) -> dict:
        location = self._find_first_match(text, self.block_names + self.lab_names)
        if location is None:
            location = self._find_first_match(text, self.generic_locations)

        target_os = self._find_with_aliases(text, self.os_names)
        software = self._find_with_aliases(text, self.software_names)

        condition = None
        for pattern, template in self.condition_patterns:
            m = re.search(pattern, text, re.IGNORECASE)
            if m:
                condition = template.format(m.group(1))
                break

        return {
            "location": location,
            "target_os": target_os,
            "software": software,
            "condition": condition,
            "location_is_ambiguous": location in self.generic_locations,
        }


if __name__ == "__main__":
    extractor = EntityExtractor()
    test_queries = [
        "Show all computers in Block C that cannot run Windows 11",
        "Which systems in the Programming Lab can run AutoCAD?",
        "List machines in Lab 1 that meet Fedora 42 requirements",
        "Show all systems older than 5 years",
    ]
    for q in test_queries:
        print(q)
        print(" ->", extractor.extract(q))
        print()
