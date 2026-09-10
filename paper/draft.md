# A Spatial Decision Support Framework Integrating NLP-Driven Query Resolution, GIS-Based Asset Localization, and Explainable AI for Intelligent Hardware and Software Compatibility Assessment in Academic Infrastructure

**[Author Name(s)]**
**[Institution]**
**[Contact email]**

---

## Abstract

Institutional IT administrators managing large, heterogeneous computer inventories face a recurring but under-tooled problem: assessing which machines can support current and upcoming operating systems and software, and communicating that assessment transparently to non-technical stakeholders. This paper presents a Spatial Decision Support System (DSS) that integrates Geographic Information Systems (GIS), Natural Language Processing (NLP), Multi-Criteria Decision Making (MCDM), and Explainable Artificial Intelligence (XAI) into a single pipeline: a natural-language query is parsed into intent and entities, resolved against a spatially indexed hardware inventory, ranked across 67 operating system options using a fixed-bound TOPSIS formulation, and explained at the feature level using SHAP. The system was built and evaluated on a hybrid dataset of 500 campus assets, 67 OS profiles, and 72 curated software compatibility records, supplemented by a two-tier dynamic software lookup mechanism. Evaluation reveals both strengths and honestly reported limitations: entity extraction achieves near-perfect accuracy after a lightweight shorthand-alias correction (95%→100% on a hand-written adversarial test set), while intent classification exhibits a substantial generalization gap between synthetic in-distribution queries (100%) and hand-crafted real-world-style queries (50%), motivating future data augmentation work. During development, a genuine normalization failure mode in standard TOPSIS was identified and resolved via fixed theoretical criterion bounds rather than data-dependent bounds — a correction applicable to other TOPSIS applications involving well-provisioned alternative sets. We discuss the system's architecture, dataset construction methodology, and limitations, and argue that the combination of these four techniques — while individually well-established in isolation — has not previously been applied together to institutional hardware and software compatibility management, an area presently dominated by commercial inventory tools rather than academic, explainable decision support research.

**Keywords:** Geographic Information Systems, Natural Language Processing, Explainable AI, Multi-Criteria Decision Making, IT Asset Management, TOPSIS, SHAP

---

## 1. Introduction

### 1.1 Problem Statement

Educational institutions typically manage hundreds of computers across multiple buildings and laboratories, each with different ages, hardware specifications, and installed software. When a new operating system is released — or, as with Windows 10's end-of-support deadline, an old one is retired — administrators must determine which machines can be upgraded, which need replacement, and which can run specific required software, often for procurement or curriculum-planning purposes.

In practice, this assessment is typically performed manually: an administrator cross-references spreadsheets of hardware specifications against vendor-published minimum requirements, one machine and one software title at a time. This process does not scale well past a few dozen machines, offers no spatial context (administrators cannot easily see *where* problem machines are physically located), provides no ranked alternatives (a binary pass/fail obscures cases where a different OS would actually be a better fit), and offers no explanation a non-technical stakeholder (e.g. a department head approving a budget) could use to understand *why* a recommendation was made.

### 1.2 Research Gap

GIS-based asset visualization, NLP-based query interfaces, MCDM-based multi-alternative ranking, and XAI-based model explanation have each been studied extensively in isolation. [Cite relevant related work here once you've done a literature pass — see Section 2.] However, to the best of our knowledge, no prior system combines all four specifically for the problem of institutional hardware/software compatibility assessment. Existing GIS query systems (e.g. GeoNLU-style natural language geospatial querying) address spatial querying but not compatibility scoring or explanation; existing IT asset management tools address inventory tracking but not natural language interaction, multi-criteria ranking, or transparent reasoning.

### 1.3 Contributions

This paper makes the following contributions:

1. A unified pipeline combining NLP intent/entity extraction, GIS-based spatial asset resolution, TOPSIS-based multi-criteria OS ranking, and SHAP-based explanation generation, applied to a previously unaddressed domain.
2. A fixed-bound TOPSIS normalization scheme that avoids a normalization failure mode (division-by-zero on zero-variance criteria) present in standard dynamic-bound TOPSIS implementations when many alternatives are equally well-suited to a given machine — a common occurrence with modern, well-provisioned hardware.
3. A hybrid dataset construction methodology combining real/augmented hardware records, officially sourced OS requirement specifications, and a validated synthetic NLP query corpus, documented transparently including its limitations.
4. An honest evaluation demonstrating both the capabilities and generalization limits of the NLP component, contrasting near-perfect in-distribution accuracy with substantially lower performance on hand-crafted adversarial queries.

---

## 2. Related Work

### 2.1 Natural Language Interfaces for Spatial/Geographic Data

Natural language interaction with spatial databases has a long history but has only recently matured with the arrival of large language models. Early controlled-language approaches such as Spot (Wallgrün et al.) demonstrated natural-language querying over OpenStreetMap data, while more recent work has focused on NL2SQL-style translation for spatial queries: Jiang and Yang (2024) evaluated ChatGPT's ability to translate natural language into spatial SQL over PostGIS, and Liu et al. (2025) proposed NALSpatial, a dedicated natural language interface for spatial databases. Monkuu extends this line of work with dynamic schema mapping and geographic disambiguation for LLM-powered geospatial querying. Reviews of NLP applied to GIS interfaces more broadly (e.g. recent IEEE conference work on geo-parsing and geo-coding) note persistent challenges around geographic ambiguity and scalability — a challenge this paper's system encounters directly and addresses via explicit ambiguity flagging (Section 3.2) rather than silent resolution.

These systems, however, focus exclusively on query *translation and retrieval* — converting a natural language question into a spatial query and returning matching records. None extends into multi-criteria decision ranking or explanation generation once matching assets are retrieved, which is the gap this paper's system addresses.

### 2.2 MCDM for Technology and Software Selection

TOPSIS (Technique for Order Preference by Similarity to Ideal Solution), introduced by Hwang and Yoon (1981), is a well-established MCDM method with documented applications across manufacturing, automotive, and information technology domains. Within IT-specific contexts, TOPSIS and its fuzzy/hybrid variants have been applied to software requirements selection under uncertainty, ETL software selection via a combined AHP-TOPSIS methodology, security requirements engineering method selection for healthcare software, and hospital information system ranking and selection. These studies confirm TOPSIS's suitability for technology-selection problems structurally similar to OS/hardware fit assessment, but none apply it specifically to operating system suitability for existing hardware, nor do any address the zero-variance normalization failure this paper identifies and resolves via fixed theoretical bounds (Section 3.3).

### 2.3 Explainable AI in Decision Support and Geospatial Contexts

SHAP (SHapley Additive exPlanations), grounded in cooperative game theory, has become a dominant model-agnostic explanation method, valued for its consistent, additive attribution of feature contributions. Its application in clinical decision support systems has been extensively reviewed, and it has been used to explain classification results in remote sensing and land-use classification tasks within GeoAI specifically. However, Xing and Sieber's widely cited review of XAI-GeoAI integration challenges identifies a persistent gap: existing geospatial XAI work centers on deep learning models for imagery/remote-sensing classification, not on tabular, criteria-based decision-support scoring of the kind this paper's system performs, and existing geospatial XAI visualizations (e.g. SHAP summary/beeswarm plots) are noted as poorly suited to representing geographic feature contributions specifically — a concern this paper sidesteps by applying SHAP to non-spatial hardware/OS criteria rather than to spatial coordinates directly.

### 2.4 IT Asset Management

Institutional hardware and software asset management is a well-established *practitioner* domain, formalized through frameworks such as NIST's IT asset management lifecycle guidance and implemented in commercial platforms (e.g. ServiceNow-based university ITAM programs, SolarWinds Service Desk, Lansweeper, InvGate). These systems provide inventory tracking, lifecycle stage management, and in some cases geographic/site-level asset mapping. Notably, this search did not surface peer-reviewed academic literature applying NLP, MCDM, or XAI techniques within this specific domain — asset management here remains dominated by rule-based inventory and reporting tools rather than intelligent, explainable decision support. This absence of academic treatment is itself a point in favor of this paper's novelty: the combination of techniques presented here has, to the best of our knowledge, not been studied for this specific, practically important problem.

### 2.5 Positioning

Table 0 summarizes how this paper's contribution relates to each area above.

| Area | What exists | What's missing (addressed here) |
|---|---|---|
| NLP + spatial querying | Query translation/retrieval | Ranking, scoring, and explanation after retrieval |
| MCDM for technology selection | TOPSIS applied to software/hospital/ETL selection | Applied to OS/hardware compatibility; fixed-bound normalization fix |
| XAI in GeoAI | SHAP for imagery/remote-sensing classification | SHAP for tabular hardware/OS criteria, avoiding the geospatial-visualization mismatch noted in prior XAI-GeoAI critique |
| IT asset management | Commercial inventory/lifecycle tools | Academic, NLP/MCDM/XAI-driven decision support layer |

---

## 3. System Architecture

### 3.1 Overview

Figure 1 [insert architecture diagram] shows the end-to-end pipeline. A natural language query is processed by an NLP module that performs (a) intent classification into one of six categories — OS compatibility check, OS recommendation, upgrade planning, hardware query, software compatibility check, and reverse software lookup — and (b) entity extraction, identifying the location, target OS, software title, and any numeric conditions (e.g. "older than 5 years") mentioned in the query. Extracted entities resolve against a spatially indexed asset database (PostgreSQL with the PostGIS extension) to retrieve the relevant machines. For OS-related intents, each retrieved machine is scored against all architecture-compatible OS profiles using a TOPSIS-based multi-criteria ranking (Section 3.3), and the resulting score is explained at the feature level using a SHAP-based post-hoc explanation layer (Section 3.4) trained on the same underlying criteria.

### 3.2 NLP Module

Intent classification uses a TF-IDF (unigram + bigram) feature representation with a multinomial Logistic Regression classifier — a deliberately lightweight choice justified by the dataset's single-domain, six-class structure, where a large transformer model would add cost without a demonstrated need. Entity extraction uses dictionary-based matching against the system's own reference vocabularies (real location names, all cataloged OS names, all cataloged software names) rather than a generic Named Entity Recognition model, guaranteeing that every extracted entity corresponds to something the downstream system actually knows about. A lightweight alias table (e.g. mapping "Win11" → "Windows 11", "Photoshop" → "Adobe Photoshop") was added after initial evaluation revealed common real-world shorthand was not being matched (Section 5.1).

### 3.3 MCDM Ranking Module

For each (machine, OS) pair, six criteria are computed: RAM fit ratio, storage fit ratio, CPU core count fit ratio, CPU clock speed fit ratio, TPM satisfaction, and Secure Boot satisfaction. Ratio-based criteria are capped at 2.0x the requirement (additional headroom beyond 2x is treated as equivalent, avoiding runaway domination by extremely over-provisioned machines), while TPM and Secure Boot are graded satisfaction scores (1.0 if satisfied or not required, a reduced partial score if required but absent) rather than binary pass/fail, allowing partial credit consistent with the graduated compatibility scoring described in Section 1.

Unlike standard TOPSIS implementations, which derive normalization bounds dynamically from the set of alternatives being compared, this system normalizes against **fixed theoretical bounds** (the known maximum of each criterion, e.g. 2.0 for ratio criteria, 1.0 for satisfaction criteria). This design choice was necessitated by an observed failure mode: when a machine is powerful enough to perfectly satisfy every criterion for every OS option — common among newer machines in the dataset — dynamic min-max normalization produces zero-variance columns and division-by-zero errors. Fixed-bound normalization avoids this entirely and is arguably more theoretically appropriate, since a machine's fitness for a given OS should not depend on which other OS options happen to be included in the comparison set. Context-dependent criteria weighting (Section 3.3.1) allows the same ranking engine to reflect different institutional priorities (e.g. security-focused administrative machines versus performance-focused research/development labs).

#### 3.3.1 Contextual Weighting

[Describe your `weights_config.py` DEFAULT / SECURITY_FOCUSED / PERFORMANCE_FOCUSED profiles here, and the lab-type mapping.]

### 3.4 Explainable AI Module

A Random Forest classifier is trained on the same six criteria to predict a binary hard-compatibility label (derived deterministically from whether all requirements are met), across all 33,500 (asset, OS) pairs in the dataset. This model is not intended to outperform the deterministic rule it approximates — its purpose is solely to provide a model SHAP's TreeExplainer can operate on, yielding principled per-feature contribution values for any given (asset, OS) pair. Contributions are normalized to percentage points for presentation (Section 5.3 shows representative examples).

### 3.5 GIS Visualization

[Describe your Leaflet.js dashboard, the campus spatial data model, and how results are rendered spatially.]

---

## 4. Dataset Construction

### 4.1 Hardware Inventory

[Describe: N assets, real vs. augmented split if applicable, fields captured, distribution across blocks/labs — pull actual numbers from your data/hardware_inventory.csv.]

### 4.2 OS Requirements Matrix

67 operating systems were cataloged, spanning Windows, and a wide range of Linux distributions (general-purpose, security-focused, and specialized), with minimum/recommended RAM, storage, CPU, TPM, and Secure Boot requirements sourced from official vendor documentation.

### 4.3 Software Compatibility Catalog

A two-tier model is used: a manually curated Tier 1 catalog of 72 software titles across 21 categories (development, design, data science, office, networking), each sourced from official vendor documentation, and a Tier 2 dynamic cache designed to hold lower-confidence entries obtained via on-demand lookup for software outside the curated catalog. [State clearly whether Tier 2 lookup was fully implemented, partially implemented as a proof-of-concept, or left as designed-but-unbuilt future work — be honest here.]

### 4.4 NLP Query Corpus

A corpus of 10,000 natural language queries was constructed via LLM-assisted generation followed by structural validation against the system's known intent and entity vocabularies, covering six intent categories in approximately balanced proportions (1,618-1,717 queries per category). [Report your inter-annotator agreement here if you obtain it — currently not yet computed, see Section 6 limitations.] Approximately 2,225 queries (22.3%) reference generic location terms ("Lab 1", "Lab 2") that do not resolve to any specific named location in the spatial dataset; rather than silently mapping these to arbitrary real locations, they are retained and flagged by the system as ambiguous, and are discussed here as an intentional test of ambiguous-entity handling rather than a resolved data quality issue.

### 4.5 Campus Spatial Data

36 locations spanning 6 blocks and 6 lab types were mapped, with coordinates and asset counts cross-validated against the hardware inventory (Section 5.2 confirms 1:1 consistency).

---

## 5. Evaluation and Results

### 5.1 NLP Performance

Table 1 reports intent classification accuracy on two test sets: a held-out split of the synthetic query corpus (2,000 queries), and a hand-crafted adversarial set (40 queries) written independently of the generation templates, deliberately incorporating informal phrasing, typos, indirect requests, and minimal keyword overlap with the training data.

| Test Set | Intent Accuracy | Location | Target OS | Software |
|---|---|---|---|---|
| Synthetic (held-out split) | 100% | — | — | — |
| Hand-written adversarial (n=40) | 50% | 100% | 100%* | 97.5% |

*after adding a shorthand-alias correction layer (95% before)

The stark contrast between in-distribution (100%) and adversarial (50%) intent accuracy indicates that the synthetic query corpus, while useful for initial development, does not capture the phrasing diversity of real administrator language, and the reported 100% figure should not be interpreted as representative of real-world performance. Entity extraction proved more robust, and a lightweight fix (mapping common shorthand such as "Win11" and "Photoshop" to their catalog names) fully closed the gap for OS-name extraction. We discuss this generalization gap further in Section 6.

### 5.2 Dataset Consistency Checks

Cross-referential validation confirmed full consistency between the hardware inventory and spatial dataset: all block and lab names matched exactly, and per-location asset counts in the spatial dataset matched the actual count of hardware records at each location with zero discrepancies.

### 5.3 MCDM Ranking Behavior

[Insert 1-2 concrete before/after examples here, e.g. the PC-0041 case: Windows 11 ranks last due to missing TPM/Secure Boot, while modern Linux distributions tie at the maximum score due to their modest, easily-satisfied requirements.] Across the full dataset, only 0.9% of all (asset, OS) pairs are hard-incompatible under the deterministic ground-truth rule, concentrated almost entirely in Windows 11 evaluations against pre-2018 machines lacking TPM 2.0 — a distributional property of the dataset (skewed toward reasonably modern hardware) rather than an artifact of the scoring method.

*[Insert your genuine expert validation results here once 2-3 independent reviewers complete `expert_validation_sample.csv`. Do NOT use the researcher-filled placeholder numbers — see the explicit warning in `evaluation/EVALUATION_SUMMARY.md`.]*

### 5.4 Explanation Quality (SHAP)

For the representative case of a 2017-purchased, TPM-absent machine (PC-0041) evaluated against Windows 11, SHAP attributes -49.9 and -49.0 percentage points to Secure Boot and TPM absence respectively, with RAM contributing a small positive offset (+1.1). The same machine evaluated against Ubuntu 24.04 shows the identical two features flipping to the dominant positive contributors (+49.7 and +49.1), correctly reflecting that Ubuntu imposes no such requirement. [If you run the comprehension survey mentioned in EVALUATION_SUMMARY.md, report results here.]

---

## 6. Discussion and Limitations

**NLP generalization gap.** The most significant limitation identified in this work is the substantial drop in intent classification accuracy between in-distribution synthetic queries (100%) and hand-written adversarial queries (50%, Section 5.1). This gap indicates that the LLM-generated, template-validated query corpus — while useful for initial system development and for demonstrating the pipeline's mechanics — does not capture the phrasing diversity of genuine administrator language. The entity extraction component proved considerably more robust and was further strengthened by a small shorthand-alias correction layer, suggesting that dictionary-based extraction against a closed, known vocabulary generalizes better than free-text intent classification in this domain. We recommend that future work either substantially diversify the training corpus (e.g. through paraphrase augmentation or collection of real anonymized query logs from IT support tickets, where available) or adopt a hybrid approach that falls back to a clarifying question when intent confidence is low, rather than committing to a possibly incorrect classification.

**MCDM validation status.** The multi-criteria ranking engine was stress-tested computationally across all 500 real assets with zero errors, and its qualitative behavior on representative cases (Section 5.3) matches domain expectations (Windows 11's TPM/Secure Boot requirements correctly and specifically penalizing pre-2018 hardware). However, genuine external validation — independent human experts judging a blind sample without reference to the system's own scoring logic — had not been completed at the time of writing. A sampling and scoring methodology for this validation is provided (`evaluation/mcdm_validation_sample.py`) and should be executed with real, independent reviewers before the ranking engine's outputs are presented as externally validated in any final version of this work.

**Software compatibility coverage.** The two-tier software compatibility model (Section 3, 4.3) — a manually curated Tier 1 catalog supplemented by dynamic Tier 2 lookup — is a deliberate design response to the practical impossibility of manually cataloging "all software." The Tier 2 implementation presented here uses Wikipedia's public API as a free, structured data source with conservative regex-based extraction, erring toward returning no data rather than an incorrect value. This is a considerably more constrained approach than an LLM-based extraction pipeline would offer, and its coverage and accuracy on a broad sample of real software titles has not yet been formally evaluated; this is identified as a direction for future work.

**Dataset composition and disclosure.** In keeping with transparent research practice, [describe here the actual real/synthetic composition of your hardware inventory once finalized]. The NLP query corpus's approximately 22% of queries referencing generic, unresolved location terms ("Lab 1", "Lab 2") is retained deliberately as a test of ambiguous-entity handling (which the system correctly flags rather than silently mis-resolving) rather than corrected, and this design choice is disclosed explicitly here to avoid the appearance of an unaddressed data quality defect.

**Distributional skew in compatibility outcomes.** Across the full dataset, only approximately 0.9% of all (asset, OS) pairs are genuinely hard-incompatible under the deterministic ground-truth rule used to train the SHAP-supporting classifier (Section 3.4), concentrated almost entirely in Windows 11 evaluations against machines lacking TPM 2.0. While this reflects a real property of the constructed dataset (skewed toward reasonably modern hardware), it also means the classifier's reported near-perfect accuracy (Section 3.4) should be interpreted as a reflection of a well-separated, low-noise labeling task rather than as evidence the model has learned any conceptually difficult inference — the ground truth is, by construction, a deterministic function of the same input features.

## 7. Conclusion

This paper presented a Spatial Decision Support System integrating natural language query resolution, GIS-based asset localization, multi-criteria OS ranking via a fixed-bound TOPSIS formulation, and SHAP-based explanation generation — a combination that, to the best of our knowledge, has not previously been applied to institutional hardware and software compatibility management. The system was implemented end-to-end and evaluated on a hybrid dataset of 500 campus hardware assets, 67 operating system profiles, and a 10,000-query NLP corpus, and is demonstrably functional: a natural language question about a specific campus location and operating system resolves, in one pipeline, to a ranked, spatially situated, and feature-level-explained compatibility assessment.

Evaluation surfaced both genuine strengths and genuine limitations, reported here without adjustment: entity extraction proved robust and improvable with minimal effort (a shorthand-alias layer), while intent classification revealed a substantial and instructive generalization gap between synthetic and real-world-style phrasing. The MCDM ranking engine required and received a genuine methodological correction during development — replacing dynamic min-max normalization with fixed theoretical bounds to resolve a real division-by-zero failure mode — which we argue is itself a modest but legitimate contribution for future TOPSIS applications involving well-provisioned, high-scoring alternative sets. Independent human validation of the ranking engine's judgments, broader Tier 2 software coverage evaluation, and NLP training data diversification are identified as the most valuable directions for continued work.

---

## References

1. Hwang, C. L., & Yoon, K. (1981). *Multiple Attribute Decision Making: Methods and Applications*. Springer-Verlag.
2. Lundberg, S. M., & Lee, S.-I. (2017). A Unified Approach to Interpreting Model Predictions. *Advances in Neural Information Processing Systems (NeurIPS)*, 30.
3. Jiang, Y., & Yang, C. (2024). Is ChatGPT a Good Geospatial Data Analyst? Exploring the Integration of Natural Language into Structured Query Language within a Spatial Database. *ISPRS International Journal of Geo-Information*, 13(1), 26. https://doi.org/10.3390/ijgi13010026
3. Wang, H., Guo, L., Liang, Y., Liu, L., & Huang, J. (2025). GPT-Based Text-to-SQL for Spatial Databases. *ISPRS International Journal of Geo-Information*, 14(8), 288.
4. Liu, M., Wang, X., Xu, J., Lu, H., & Tong, Y. (2025). NALSpatial: A Natural Language Interface for Spatial Databases. *IEEE Transactions on Knowledge and Data Engineering*, 37(4), 2056–2070. https://doi.org/10.1109/TKDE.2025.3525587
5. Li, Z., & Ning, H. (2023). Autonomous GIS: The Next-Generation AI-Powered GIS. *International Journal of Digital Earth*, 16(2), 4668–4686. https://doi.org/10.1080/17538947.2023.2278895
6. Xing, J., & Sieber, R. (2023). The Challenges of Integrating Explainable Artificial Intelligence into GeoAI. *Transactions in GIS*, 27, 626–645. https://doi.org/10.1111/tgis.13045
7. Chaudhary, W., & Mohammad, R. (2020). Selection of Software Requirements Using TOPSIS Under Fuzzy Environment. *International Journal of Computers and Applications*, 44(6), 503–512. https://doi.org/10.1080/1206212X.2020.1820689
8. Application of an Integrated Multi-Criteria Decision Making AHP-TOPSIS Methodology for ETL Software Selection. (2016). *SpringerPlus*, 5, 2032. https://doi.org/10.1186/s40064-016-1888-z
9. A Fuzzy TOPSIS Based Analysis Toward Selection of Effective Security Requirements Engineering Approach for Trustworthy Healthcare Software Development. *PMC*. https://pmc.ncbi.nlm.nih.gov/articles/PMC7502023/
10. Ranking and Selecting Hospital Information Systems: A Multi-Criteria Decision Making Approach Using TOPSIS in Hamadan, Iran. *PMC*. https://pmc.ncbi.nlm.nih.gov/articles/PMC12456787/
11. National Institute of Standards and Technology (NIST). *IT Asset Management*. NIST Special Publication 1800-5. https://nvlpubs.nist.gov/nistpubs/specialpublications/nist.sp.1800-5.pdf

*[Add: your OS vendor documentation citations (Microsoft, Ubuntu, Debian, Fedora, etc. — already sourced in your os_requirements.csv `source_url` column, just needs formatting as references), and any additional papers your advisor suggests.]*

---

## Appendix A: Full Criteria Weight Profiles

[Insert the DEFAULT_WEIGHTS / SECURITY_FOCUSED_WEIGHTS / PERFORMANCE_FOCUSED_WEIGHTS tables from weights_config.py]

## Appendix B: NLP Stress Test Queries and Results

[Insert the full 40-query table from evaluation/nlp_stress_test_results.csv]
