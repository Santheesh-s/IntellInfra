"""
Generates SHAP feature-contribution explanations for any (asset, OS) pair,
in the same style as the original proposal's example:

    Windows 11 Compatibility Score: 42%
    RAM Limitation      : -25%
    TPM Absence         : -40%
    Storage Limitation  : -10%
    CPU Compatibility   : +15%

Usage:
    from shap_explainer import CompatibilityExplainer
    explainer = CompatibilityExplainer()
    explainer.explain("PC-0041", "win11")
"""
import sys
from pathlib import Path
import pandas as pd
import numpy as np
import joblib
import shap

sys.path.append(str(Path(__file__).parent.parent / "mcdm"))
from topsis_ranker import TOPSISRanker, CRITERIA_ORDER, _ratio_fit, _tpm_fit, _secure_boot_fit

MODEL_PATH = Path(__file__).parent / "saved_models" / "compatibility_classifier.joblib"

# Human-readable labels for the paper/dashboard, mapped from internal
# criteria names
DISPLAY_NAMES = {
    "ram_fit": "RAM",
    "storage_fit": "Storage",
    "cpu_cores_fit": "CPU Cores",
    "cpu_clock_fit": "CPU Clock Speed",
    "tpm_fit": "TPM",
    "secure_boot_fit": "Secure Boot",
}


class CompatibilityExplainer:
    def __init__(self):
        self.model = joblib.load(MODEL_PATH)
        self.ranker = TOPSISRanker()
        # TreeExplainer is exact and fast for tree-based models like Random Forest
        self.shap_explainer = shap.TreeExplainer(self.model)

    def _build_feature_row(self, asset_row: pd.Series, os_row: pd.Series) -> pd.DataFrame:
        features = {
            "ram_fit": _ratio_fit(asset_row["ram_gb"], os_row["min_ram_gb"]),
            "storage_fit": _ratio_fit(asset_row["storage_gb"], os_row["min_storage_gb"]),
            "cpu_cores_fit": _ratio_fit(asset_row["cpu_cores"], os_row["min_cpu_cores"]),
            "cpu_clock_fit": _ratio_fit(asset_row["cpu_clock_ghz"], os_row["min_clock_ghz"]),
            "tpm_fit": _tpm_fit(asset_row["tpm_version"], os_row["tpm_required"]),
            "secure_boot_fit": _secure_boot_fit(asset_row["secure_boot_support"], os_row["secure_boot_required"]),
        }
        return pd.DataFrame([features], columns=CRITERIA_ORDER)

    def explain(self, asset_id: str, os_id: str) -> dict:
        asset_row = self.ranker.hardware[self.ranker.hardware["asset_id"] == asset_id]
        os_row = self.ranker.os_requirements[self.ranker.os_requirements["os_id"] == os_id]
        if asset_row.empty:
            raise ValueError(f"Asset '{asset_id}' not found")
        if os_row.empty:
            raise ValueError(f"OS '{os_id}' not found")
        asset_row, os_row = asset_row.iloc[0], os_row.iloc[0]

        X = self._build_feature_row(asset_row, os_row)

        compat_probability = float(self.model.predict_proba(X)[0][1])

        # shap_values for binary RandomForest: array shape (1, n_features, 2)
        # in modern SHAP -- take the "class 1" (compatible) contributions
        raw_shap = self.shap_explainer.shap_values(X)
        if isinstance(raw_shap, list):
            contributions = raw_shap[1][0]
        else:
            contributions = raw_shap[0][:, 1] if raw_shap.ndim == 3 else raw_shap[0]

        # Normalize contributions to percentage points that sum toward the
        # final score, matching the original proposal's presentation style
        total_abs = np.abs(contributions).sum()
        pct_contributions = {
            DISPLAY_NAMES[CRITERIA_ORDER[i]]: round(float(contributions[i] / total_abs * 100), 1)
            if total_abs > 0 else 0.0
            for i in range(len(CRITERIA_ORDER))
        }

        raw_criteria = X.iloc[0].round(2).to_dict()

        summary_sentence = self._generate_summary_sentence(
            os_name=os_row["os_name"],
            score_pct=round(compat_probability * 100, 1),
            contributions=pct_contributions,
            asset_row=asset_row,
            os_row=os_row,
        )

        return {
            "asset_id": asset_id,
            "os_id": os_id,
            "os_name": os_row["os_name"],
            "compatibility_score_pct": round(compat_probability * 100, 1),
            "summary_sentence": summary_sentence,
            "feature_contributions_pct": dict(
                sorted(pct_contributions.items(), key=lambda kv: abs(kv[1]), reverse=True)
            ),
            "raw_criteria_values": raw_criteria,
        }

    def _describe_problem(self, feature_key: str, asset_row: pd.Series, os_row: pd.Series) -> str:
        """Turns a failing OR relatively-weak criterion into a specific,
        plain-English phrase using the actual numbers involved. SHAP can
        flag a criterion as a negative contributor even when the machine
        technically meets that requirement (e.g. it meets the minimum with
        zero headroom, which scores lower than a criterion the machine
        exceeds comfortably) -- so this checks the real numbers rather
        than assuming "flagged negative" always means "fails the
        requirement", to avoid stating something false."""
        if feature_key == "tpm_fit":
            required = os_row["tpm_required"]
            have = asset_row["tpm_version"]
            if pd.isna(have):
                return f"it has no TPM chip, but this OS requires TPM {required}"
            if have < required:
                return f"it only has TPM {have}, but this OS requires TPM {required}"
            return f"its TPM {have} only just meets the TPM {required} requirement, with no margin"
        if feature_key == "secure_boot_fit":
            if not bool(asset_row["secure_boot_support"]):
                return "it doesn't support Secure Boot, which this OS requires"
            return "Secure Boot is supported but this is a tighter requirement than others"
        if feature_key == "ram_fit":
            actual, required = asset_row["ram_gb"], os_row["min_ram_gb"]
            if actual < required:
                return f"it has {int(actual)}GB RAM, below the {int(required)}GB minimum"
            return f"it has {int(actual)}GB RAM, which exactly meets the {int(required)}GB minimum with no headroom"
        if feature_key == "storage_fit":
            actual, required = asset_row["storage_gb"], os_row["min_storage_gb"]
            if actual < required:
                return f"it has {int(actual)}GB storage, below the {int(required)}GB minimum"
            return f"it has {int(actual)}GB storage, which exactly meets the {int(required)}GB minimum with no headroom"
        if feature_key == "cpu_cores_fit":
            actual, required = asset_row["cpu_cores"], os_row["min_cpu_cores"]
            if actual < required:
                return f"it has {int(actual)} CPU cores, below the {int(required)} required"
            return f"its {int(actual)} CPU cores exactly meet the requirement with no headroom"
        if feature_key == "cpu_clock_fit":
            actual, required = asset_row["cpu_clock_ghz"], os_row["min_clock_ghz"]
            if actual < required:
                return f"its CPU clock speed is below the {required}GHz minimum"
            return f"its CPU clock speed exactly meets the {required}GHz minimum with no headroom"
        return feature_key

    def _describe_strength(self, feature_key: str, asset_row: pd.Series) -> str:
        """Turns a strongly-positive criterion into a short plain-English phrase."""
        if feature_key == "tpm_fit":
            return "its TPM chip meets the requirement"
        if feature_key == "secure_boot_fit":
            return "it supports Secure Boot"
        if feature_key == "ram_fit":
            return f"it has ample RAM ({int(asset_row['ram_gb'])}GB)"
        if feature_key == "storage_fit":
            return f"it has plenty of storage ({int(asset_row['storage_gb'])}GB)"
        if feature_key == "cpu_cores_fit":
            return f"its {int(asset_row['cpu_cores'])}-core CPU is more than sufficient"
        if feature_key == "cpu_clock_fit":
            return "its CPU clock speed comfortably exceeds the requirement"
        return feature_key

    def _generate_summary_sentence(
        self, os_name: str, score_pct: float, contributions: dict,
        asset_row: pd.Series, os_row: pd.Series,
    ) -> str:
        reverse_names = {v: k for k, v in DISPLAY_NAMES.items()}
        ranked = sorted(contributions.items(), key=lambda kv: kv[1])  # most negative first

        negatives = [(reverse_names[name], pct) for name, pct in ranked if pct < -5]
        positives = [(reverse_names[name], pct) for name, pct in reversed(ranked) if pct > 5]

        if score_pct >= 70:
            reasons = [self._describe_strength(k, asset_row) for k, _ in positives[:2]]
            reason_text = " and ".join(reasons) if reasons else "it meets all the key requirements"
            return f"This machine is compatible with {os_name}: {reason_text}."

        if score_pct < 35:
            reasons = [self._describe_problem(k, asset_row, os_row) for k, _ in negatives[:2]]
            reason_text = " and ".join(reasons) if reasons else "it fails to meet key requirements"
            return f"This machine is not compatible with {os_name}: {reason_text}."

        problem = self._describe_problem(negatives[0][0], asset_row, os_row) if negatives else None
        strength = self._describe_strength(positives[0][0], asset_row) if positives else None
        if problem and strength:
            return (f"This machine can partially run {os_name}: {strength}, but {problem}, "
                    f"which may cause issues.")
        if problem:
            return f"This machine may struggle to run {os_name} because {problem}."
        return f"This machine should mostly work with {os_name}, though it doesn't exceed the requirements by much."


if __name__ == "__main__":
    explainer = CompatibilityExplainer()

    print("=== PC-0041 vs Windows 11 (expect low score, TPM/Secure Boot penalties) ===")
    result = explainer.explain("PC-0041", "win11")
    print(f"Compatibility Score: {result['compatibility_score_pct']}%")
    for feature, pct in result["feature_contributions_pct"].items():
        sign = "+" if pct >= 0 else ""
        print(f"  {feature:<18}: {sign}{pct}%")

    print("\n=== PC-0041 vs Ubuntu 24.04 (expect high score) ===")
    result = explainer.explain("PC-0041", "ubuntu2404")
    print(f"Compatibility Score: {result['compatibility_score_pct']}%")
    for feature, pct in result["feature_contributions_pct"].items():
        sign = "+" if pct >= 0 else ""
        print(f"  {feature:<18}: {sign}{pct}%")
