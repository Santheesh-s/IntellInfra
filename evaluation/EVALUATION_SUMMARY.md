# Evaluation Summary

## 1. NLP Intent Classification

| Test Set | Accuracy | Notes |
|---|---|---|
| Synthetic templated queries (train/test split, n=2,000 held out) | 100% | See `backend/nlp/saved_models/evaluation_report.csv`. Expected for templated synthetic data — reflects separability of the generation templates, not real-world generalization. |
| Hand-written adversarial stress test (n=40) | 50% | See `nlp_stress_test.py` / `nlp_stress_test_results.csv`. Deliberately varied, indirect, typo-containing phrasing written without reference to the training templates. |

**Entity extraction on the same stress test:**

| Entity | Before alias fix | After alias fix |
|---|---|---|
| Location | 100% | 100% |
| Target OS | 95% | 100% |
| Software | 97.5% | 97.5% |

**Interpretation for the paper:** entity extraction is robust and improved further with a small shorthand-alias layer (e.g. "Win11" → "Windows 11", "Photoshop" → "Adobe Photoshop"). Intent classification, however, drops sharply on realistic phrasing — this is a genuine limitation, not a data or code bug, and should be reported as such. Recommended framing: *"While the intent classifier achieves near-perfect accuracy on in-distribution synthetic queries, a hand-crafted adversarial test set reveals a substantial generalization gap (100% → 50%), indicating the templated training data does not capture the phrasing diversity of real administrator queries. This motivates future work in data augmentation or few-shot prompting approaches for intent classification in this domain."*

---

## 2. MCDM (TOPSIS) Ranking Validation

- **Method:** stratified sample of 45 (asset, OS) pairs — 15 confirmed hard-incompatible pairs (fail at least one of RAM/storage/CPU/TPM/Secure Boot requirements) and 30 confirmed compatible pairs, drawn from the full 500-asset × up-to-67-OS space.
- **Sample file:** `expert_validation_sample.csv` (blind — no score or ground truth shown)
- **Process:** hand this file to 2-3 independent reviewers (classmates, advisor, or IT staff) who fill in `expert_verdict` (compatible / not_compatible / borderline) using only the visible hardware specs — without seeing the system's own score.
- **Scoring:** run `python mcdm_validation_sample.py --score` after reviewers complete their verdicts. This reports system-expert agreement and can be extended to Cohen's Kappa across multiple reviewers.

> **⚠️ Current status — NOT yet independently validated.** The `expert_verdict` column in `expert_validation_sample.csv` was filled in by the researcher (via Claude) applying the same deterministic rule the system itself uses, as a stopgap to unblock the project pipeline. The resulting 100% agreement is **circular and must not be reported as expert validation** in the paper — it only confirms the code is internally consistent, not that independent humans agree with the system's judgments. **Before submission, this file must be re-done by 2-3 people who did not write the system**, ideally without access to this conversation's rule table, so their judgment is genuinely independent. Until then, the paper should either omit this validation step or explicitly disclose it was not yet performed independently.

**Known distributional property, worth reporting rather than hiding:** across the full dataset, only ~0.9% of all (asset, OS) pairs are genuinely hard-incompatible — nearly all incompatibility is concentrated in Windows 11's TPM 2.0/Secure Boot requirements against older machines. Modern Linux distributions' modest requirements mean the vast majority of machine-OS pairs are trivially compatible. This is a real property of a mixed-age campus inventory, not a scoring artifact, and should be described in the dataset/results section.

---

## 3. XAI (SHAP) Explanation Quality

- **Qualitative validation:** spot-checked against known ground truth (e.g. `PC-0041` vs Windows 11 → TPM and Secure Boot correctly identified as the dominant negative contributors at -44% to -50%; the same machine vs Ubuntu 24.04 → the same two factors flip to the dominant positive contributors).
- **Recommended addition before submission:** a small user comprehension survey (10-15 respondents, ideally including non-technical staff) shown 5-6 example explanations, asked to rate clarity/trust on a Likert scale. This is standard in XAI papers and strengthens the "explainable" claim beyond a technical correctness check.

---

## 4. Software Compatibility Tier 1/2

Not yet built at time of this evaluation. If included in the final paper, describe as a working proof-of-concept (Tier 1 curated catalog of 72 titles) with Tier 2 dynamic lookup as a designed-but-not-fully-implemented extension, or complete Phase 6 before submission.

---

## What To Do Next

1. Get 2-3 people to fill in `expert_validation_sample.csv`
2. Run `python mcdm_validation_sample.py --score` and record the agreement rate here
3. Optionally run the small XAI comprehension survey
4. Fold these numbers directly into your paper's Results/Evaluation section
