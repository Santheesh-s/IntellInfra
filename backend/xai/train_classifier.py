"""
Builds a training dataset of every (asset, OS) pair -- 500 assets x 67 OS
options = 33,500 rows -- using the same 6 fit-ratio criteria the TOPSIS
ranker computes, then trains a Random Forest to predict a binary
ground-truth compatibility label (does this machine meet every hard
requirement for this OS, yes/no).

Why a classifier at all, if we already have deterministic rules?
Because SHAP needs a model to explain. The Random Forest re-learns the
same rules from data, and in exchange we get principled, consistent
feature-contribution values (SHAP) for every prediction -- e.g. "missing
TPM contributed -40% to this machine's Windows 11 compatibility score" --
which a hand-written if/else block cannot produce on its own.

Usage:
    python train_classifier.py
"""
import sys
from pathlib import Path
import pandas as pd
import numpy as np
import joblib
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report

sys.path.append(str(Path(__file__).parent.parent / "mcdm"))
from topsis_ranker import (
    TOPSISRanker, CRITERIA_ORDER, _ratio_fit, _tpm_fit, _secure_boot_fit
)

MODEL_DIR = Path(__file__).parent / "saved_models"
MODEL_DIR.mkdir(exist_ok=True)


def is_hard_compatible(asset_row, os_row) -> int:
    """Ground truth: 1 only if EVERY hard requirement is actually met."""
    if asset_row["ram_gb"] < os_row["min_ram_gb"]:
        return 0
    if asset_row["storage_gb"] < os_row["min_storage_gb"]:
        return 0
    if asset_row["cpu_cores"] < os_row["min_cpu_cores"]:
        return 0
    if asset_row["cpu_clock_ghz"] < os_row["min_clock_ghz"]:
        return 0
    if pd.notna(os_row["tpm_required"]):
        if pd.isna(asset_row["tpm_version"]) or asset_row["tpm_version"] < os_row["tpm_required"]:
            return 0
    if bool(os_row["secure_boot_required"]) and not bool(asset_row["secure_boot_support"]):
        return 0
    return 1


def build_dataset(ranker: TOPSISRanker) -> pd.DataFrame:
    rows = []
    for _, asset_row in ranker.hardware.iterrows():
        os_df = ranker._compatible_os(asset_row["architecture"])
        for _, os_row in os_df.iterrows():
            features = [
                _ratio_fit(asset_row["ram_gb"], os_row["min_ram_gb"]),
                _ratio_fit(asset_row["storage_gb"], os_row["min_storage_gb"]),
                _ratio_fit(asset_row["cpu_cores"], os_row["min_cpu_cores"]),
                _ratio_fit(asset_row["cpu_clock_ghz"], os_row["min_clock_ghz"]),
                _tpm_fit(asset_row["tpm_version"], os_row["tpm_required"]),
                _secure_boot_fit(asset_row["secure_boot_support"], os_row["secure_boot_required"]),
            ]
            label = is_hard_compatible(asset_row, os_row)
            rows.append(features + [label, asset_row["asset_id"], os_row["os_id"]])

    df = pd.DataFrame(rows, columns=CRITERIA_ORDER + ["compatible", "asset_id", "os_id"])
    return df


def main():
    ranker = TOPSISRanker()
    print("Building (asset x OS) training dataset...")
    df = build_dataset(ranker)
    print(f"Dataset shape: {df.shape}")
    print(df["compatible"].value_counts(normalize=True).rename("proportion"))

    X = df[CRITERIA_ORDER]
    y = df["compatible"]

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )

    clf = RandomForestClassifier(
        n_estimators=200, max_depth=8, class_weight="balanced", random_state=42
    )
    clf.fit(X_train, y_train)

    y_pred = clf.predict(X_test)
    print("\n=== Classification Report ===")
    print(classification_report(y_test, y_pred))

    joblib.dump(clf, MODEL_DIR / "compatibility_classifier.joblib")
    df.to_csv(MODEL_DIR / "training_dataset.csv", index=False)
    print(f"\nModel saved to {MODEL_DIR / 'compatibility_classifier.joblib'}")
    print(f"Training dataset saved to {MODEL_DIR / 'training_dataset.csv'}")


if __name__ == "__main__":
    main()
