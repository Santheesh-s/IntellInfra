"""
Ranks all compatible OS options for a given machine using TOPSIS
(Technique for Order of Preference by Similarity to Ideal Solution).

For each asset x OS pair, builds a 6-criteria "fitness" vector:
    [ram_fit, storage_fit, cpu_cores_fit, cpu_clock_fit, tpm_fit, secure_boot_fit]

Each criterion is a 0-2 "fit ratio": 1.0 means exactly meets the
requirement, >1.0 means headroom above it (capped at 2.0 so a machine
with 10x the required RAM doesn't dominate the ranking), and <1.0
means it falls short. TPM/Secure Boot are graded satisfaction scores
rather than raw ratios since they're pass/fail requirements in reality.

Usage:
    from topsis_ranker import rank_os_for_asset
    rank_os_for_asset("C-102")
"""
import pandas as pd
import numpy as np
from pathlib import Path

import sys
sys.path.append(str(Path(__file__).parent))
from weights_config import get_weights_for_location, DEFAULT_WEIGHTS

DATA_DIR = Path(__file__).parent.parent.parent / "data"

CRITERIA_ORDER = [
    "ram_fit", "storage_fit", "cpu_cores_fit",
    "cpu_clock_fit", "tpm_fit", "secure_boot_fit",
]

RATIO_CAP = 2.0  # headroom beyond 2x the requirement stops adding value

# Fixed theoretical bounds per criterion -- NOT derived from the data.
# This is what makes scoring stable even when every OS option is equally
# "perfect" for a given machine (a real, common case for newer hardware):
# pymcdm's default min-max normalization divides by zero when all
# alternatives are tied on a criterion, since it derives bounds from the
# candidate set itself. Using fixed bounds avoids that failure mode
# entirely and is arguably more correct: a machine's fit for Windows 11
# shouldn't depend on which other OS options happen to be compared.
CRITERION_MAX = {
    "ram_fit": RATIO_CAP, "storage_fit": RATIO_CAP,
    "cpu_cores_fit": RATIO_CAP, "cpu_clock_fit": RATIO_CAP,
    "tpm_fit": 1.0, "secure_boot_fit": 1.0,
}
CRITERION_MIN = {c: 0.0 for c in CRITERIA_ORDER}


def _ratio_fit(actual, required, cap=RATIO_CAP):
    if required is None or required == 0:
        return cap  # no requirement -> automatically "excellent fit"
    return min(actual / required, cap)


def _tpm_fit(asset_tpm, os_tpm_required):
    if pd.isna(os_tpm_required):
        return 1.0  # not required -> fully satisfied
    if pd.isna(asset_tpm):
        return 0.15  # required but machine has no TPM at all -> heavy penalty, not zero
    return 1.0 if asset_tpm >= os_tpm_required else 0.4


def _secure_boot_fit(asset_supports, os_requires):
    if not bool(os_requires):
        return 1.0
    return 1.0 if bool(asset_supports) else 0.15


class TOPSISRanker:
    def __init__(self):
        self.hardware = pd.read_csv(DATA_DIR / "hardware_inventory.csv")
        self.os_requirements = pd.read_csv(DATA_DIR / "os_requirements.csv")

    def _compatible_os(self, asset_arch: str) -> pd.DataFrame:
        """Filters to OS entries whose architecture_support includes the asset's arch."""
        mask = self.os_requirements["architecture_support"].apply(
            lambda s: asset_arch in [a.strip() for a in str(s).split(";")]
        )
        return self.os_requirements[mask].reset_index(drop=True)

    def _build_criteria_matrix(self, asset_row: pd.Series, os_df: pd.DataFrame) -> np.ndarray:
        rows = []
        for _, os_row in os_df.iterrows():
            rows.append([
                _ratio_fit(asset_row["ram_gb"], os_row["min_ram_gb"]),
                _ratio_fit(asset_row["storage_gb"], os_row["min_storage_gb"]),
                _ratio_fit(asset_row["cpu_cores"], os_row["min_cpu_cores"]),
                _ratio_fit(asset_row["cpu_clock_ghz"], os_row["min_clock_ghz"]),
                _tpm_fit(asset_row["tpm_version"], os_row["tpm_required"]),
                _secure_boot_fit(asset_row["secure_boot_support"], os_row["secure_boot_required"]),
            ])
        return np.array(rows)

    def _topsis_fixed_bounds(self, matrix: np.ndarray, weight_vector: np.ndarray) -> np.ndarray:
        """
        TOPSIS using fixed theoretical bounds (CRITERION_MIN/MAX) instead of
        bounds derived from the candidate set. All criteria are "benefit"
        type (higher = better), so the ideal solution is CRITERION_MAX and
        the anti-ideal is CRITERION_MIN for every criterion.
        """
        maxes = np.array([CRITERION_MAX[c] for c in CRITERIA_ORDER])
        mins = np.array([CRITERION_MIN[c] for c in CRITERIA_ORDER])

        normalized = (matrix - mins) / (maxes - mins)
        weighted = normalized * weight_vector

        ideal = weight_vector  # normalized ideal is 1.0 per criterion -> weighted ideal = weights
        anti_ideal = np.zeros_like(weight_vector)

        dist_to_ideal = np.sqrt(((weighted - ideal) ** 2).sum(axis=1))
        dist_to_anti = np.sqrt(((weighted - anti_ideal) ** 2).sum(axis=1))

        denom = dist_to_ideal + dist_to_anti
        # If a row is exactly at the ideal point, both distances can be 0 for
        # that row's own comparison -- guard divide-by-zero, score is then 1.0.
        scores = np.where(denom == 0, 1.0, dist_to_anti / denom)
        return scores

    def rank(self, asset_id: str, weights: dict = None) -> list[dict]:
        asset_row = self.hardware[self.hardware["asset_id"] == asset_id]
        if asset_row.empty:
            raise ValueError(f"Asset '{asset_id}' not found")
        asset_row = asset_row.iloc[0]

        os_df = self._compatible_os(asset_row["architecture"])
        if os_df.empty:
            return []

        matrix = self._build_criteria_matrix(asset_row, os_df)

        weights = weights or get_weights_for_location(asset_row["block"], asset_row["lab"])
        weight_vector = np.array([weights[c] for c in CRITERIA_ORDER])

        scores = self._topsis_fixed_bounds(matrix, weight_vector)

        results = []
        for i, os_row in os_df.iterrows():
            results.append({
                "os_id": os_row["os_id"],
                "os_name": os_row["os_name"],
                "suitability_score": round(float(scores[i]), 4),
                "criteria_breakdown": {
                    CRITERIA_ORDER[j]: round(float(matrix[i][j]), 2)
                    for j in range(len(CRITERIA_ORDER))
                },
            })

        results.sort(key=lambda r: r["suitability_score"], reverse=True)
        for rank, r in enumerate(results, start=1):
            r["rank"] = rank

        return results


if __name__ == "__main__":
    ranker = TOPSISRanker()
    sample_asset = ranker.hardware.iloc[0]["asset_id"]
    print(f"Ranking OS options for asset: {sample_asset}\n")
    for r in ranker.rank(sample_asset)[:5]:
        print(f"#{r['rank']}  {r['os_name']:<20} score={r['suitability_score']}")
        print(f"      {r['criteria_breakdown']}")
