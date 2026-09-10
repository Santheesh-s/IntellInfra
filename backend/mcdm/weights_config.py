"""
Criteria weights for TOPSIS ranking, by lab context.

Criteria order (must match topsis_ranker.py build_criteria_matrix):
    [ram_fit, storage_fit, cpu_cores_fit, cpu_clock_fit, tpm_fit, secure_boot_fit]

All weights sum to 1.0 within each profile.
"""

DEFAULT_WEIGHTS = {
    "ram_fit": 0.25,
    "storage_fit": 0.15,
    "cpu_cores_fit": 0.20,
    "cpu_clock_fit": 0.10,
    "tpm_fit": 0.15,
    "secure_boot_fit": 0.15,
}

# Security-critical contexts (admin offices, exam systems) weight
# TPM/Secure Boot much higher -- these labs care more about compliance
# than raw performance headroom.
SECURITY_FOCUSED_WEIGHTS = {
    "ram_fit": 0.15,
    "storage_fit": 0.10,
    "cpu_cores_fit": 0.10,
    "cpu_clock_fit": 0.05,
    "tpm_fit": 0.30,
    "secure_boot_fit": 0.30,
}

# Performance-focused contexts (programming/AI/research labs) weight
# CPU/RAM higher since dev workloads are resource-heavy and TPM/Secure
# Boot matter less for a machine that's never exposed to end users.
PERFORMANCE_FOCUSED_WEIGHTS = {
    "ram_fit": 0.30,
    "storage_fit": 0.20,
    "cpu_cores_fit": 0.25,
    "cpu_clock_fit": 0.15,
    "tpm_fit": 0.05,
    "secure_boot_fit": 0.05,
}

# Map real lab names (from campus_spatial_data.csv) to a weight profile
LAB_PROFILE_MAP = {
    "Admin": SECURITY_FOCUSED_WEIGHTS,
    "AI Lab": PERFORMANCE_FOCUSED_WEIGHTS,
    "Research Lab": PERFORMANCE_FOCUSED_WEIGHTS,
    "Programming Lab": PERFORMANCE_FOCUSED_WEIGHTS,
    "CAD Lab": PERFORMANCE_FOCUSED_WEIGHTS,
    "Network Lab": DEFAULT_WEIGHTS,
    "Language Lab": DEFAULT_WEIGHTS,
    "Library": DEFAULT_WEIGHTS,
}


def get_weights_for_location(block: str = None, lab: str = None) -> dict:
    """Returns the appropriate weight profile for a given block/lab."""
    if lab in LAB_PROFILE_MAP:
        return LAB_PROFILE_MAP[lab]
    if block in LAB_PROFILE_MAP:
        return LAB_PROFILE_MAP[block]
    return DEFAULT_WEIGHTS
