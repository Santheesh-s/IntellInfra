"""
Builds a stratified sample of (asset, OS) pairs across the score spectrum
for manual expert validation -- the "2-3 people hand-check 30-50 scores"
step referenced throughout this project's planning. Produces a CSV with
an empty "expert_verdict" column for reviewers to fill in, and a script
to compute agreement once that column is filled.

Usage:
    python mcdm_validation_sample.py            # generates the blank sample
    python mcdm_validation_sample.py --score    # scores a completed sample
"""
import sys
from pathlib import Path
import pandas as pd
import numpy as np

sys.path.append(str(Path(__file__).parent.parent / "backend" / "mcdm"))
sys.path.append(str(Path(__file__).parent.parent / "backend" / "xai"))
from topsis_ranker import TOPSISRanker
from train_classifier import is_hard_compatible

OUT_PATH = Path(__file__).parent / "expert_validation_sample.csv"


def build_sample(n_per_bucket=15, seed=42):
    """
    Stratifies using the actual hard-compatibility rule (not just the raw
    TOPSIS score) -- an earlier version of this script bucketed purely by
    suitability_score, but with fixed-bound normalization almost every
    pair scores >=0.5 (only ~0.9% of all asset-OS pairs are genuinely
    hard-incompatible; see xai/train_classifier.py). Bucketing on score
    alone produced a validation sample with zero real failure cases,
    which defeats the point of expert review. This version guarantees a
    meaningful number of true incompatible pairs are included.
    """
    ranker = TOPSISRanker()
    rng = np.random.default_rng(seed)

    all_pairs = []
    for _, asset_row in ranker.hardware.iterrows():
        os_df = ranker._compatible_os(asset_row["architecture"])
        ranked = {r["os_id"]: r for r in ranker.rank(asset_row["asset_id"])}
        for _, os_row in os_df.iterrows():
            hard_label = is_hard_compatible(asset_row, os_row)
            r = ranked[os_row["os_id"]]
            all_pairs.append({
                "asset_id": asset_row["asset_id"],
                "os_id": os_row["os_id"],
                "os_name": os_row["os_name"],
                "suitability_score": r["suitability_score"],
                "hard_compatible_ground_truth": hard_label,
            })

    df = pd.DataFrame(all_pairs)

    incompatible = df[df["hard_compatible_ground_truth"] == 0]
    compatible = df[df["hard_compatible_ground_truth"] == 1]

    n_incompatible = min(n_per_bucket, len(incompatible))
    sample_incompatible = incompatible.sample(n_incompatible, random_state=seed)
    sample_compatible = compatible.sample(min(n_per_bucket * 2, len(compatible)), random_state=seed)

    sample = pd.concat([sample_incompatible, sample_compatible]).reset_index(drop=True)

    hw = ranker.hardware.set_index("asset_id")
    sample["ram_gb"] = sample["asset_id"].map(hw["ram_gb"])
    sample["storage_gb"] = sample["asset_id"].map(hw["storage_gb"])
    sample["cpu_cores"] = sample["asset_id"].map(hw["cpu_cores"])
    sample["tpm_version"] = sample["asset_id"].map(hw["tpm_version"])
    sample["secure_boot_support"] = sample["asset_id"].map(hw["secure_boot_support"])

    # Drop the ground-truth/score columns the reviewer shouldn't see while
    # scoring, keep them in a hidden reference file for later comparison
    sample_blind = sample.drop(columns=["suitability_score", "hard_compatible_ground_truth"]).copy()
    sample_blind["expert_verdict"] = ""
    sample_blind["reviewer_notes"] = ""
    sample_blind = sample_blind.sample(frac=1, random_state=seed).reset_index(drop=True)

    sample_blind.to_csv(OUT_PATH, index=False)
    sample.sample(frac=1, random_state=seed).reset_index(drop=True).to_csv(
        Path(__file__).parent / "_validation_answer_key.csv", index=False
    )

    print(f"Blind review sample of {len(sample_blind)} asset-OS pairs saved to {OUT_PATH}")
    print(f"  -> includes {n_incompatible} genuinely incompatible pairs and "
          f"{len(sample_compatible)} compatible pairs")
    print(f"Answer key (score + ground truth, for after review) saved separately -- "
          f"do not share this with reviewers before they complete their verdicts.")
    print("\nHand expert_validation_sample.csv to 2-3 reviewers. Each should")
    print("independently fill in 'expert_verdict' (compatible / not_compatible /")
    print("borderline), then re-run this script with --score.")


def score_completed_sample():
    reviewed = pd.read_csv(OUT_PATH)
    answer_key = pd.read_csv(Path(__file__).parent / "_validation_answer_key.csv")

    if reviewed["expert_verdict"].isna().all() or (reviewed["expert_verdict"] == "").all():
        print("No expert verdicts filled in yet. Fill the 'expert_verdict' column first.")
        return

    merged = reviewed.merge(
        answer_key[["asset_id", "os_id", "suitability_score", "hard_compatible_ground_truth"]],
        on=["asset_id", "os_id"],
    )
    merged["system_verdict"] = np.where(
        merged["hard_compatible_ground_truth"] == 1, "compatible", "not_compatible"
    )

    filled = merged[merged["expert_verdict"].isin(["compatible", "not_compatible"])]
    agreement = (filled["expert_verdict"] == filled["system_verdict"]).mean()
    print(f"System-expert agreement on {len(filled)} labeled pairs: {agreement:.1%}")
    print(filled[["asset_id", "os_name", "suitability_score", "system_verdict", "expert_verdict"]].to_string(index=False))


if __name__ == "__main__":
    if "--score" in sys.argv:
        score_completed_sample()
    else:
        build_sample()
