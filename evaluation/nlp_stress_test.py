"""
Hand-crafted stress test for the NLP pipeline.

Why this exists: the training/test split on nlp_query_dataset_10000.csv
gave 100% accuracy (see backend/nlp/saved_models/evaluation_report.csv).
That's expected for a templated synthetic dataset, but it says nothing
about how the model handles the messier phrasing real admins actually
use. This file is 40 queries written by hand -- deliberately varied,
indirect, occasionally ambiguous or combining ideas -- specifically to
give an honest, reportable measure of generalization for the paper.

Usage:
    python nlp_stress_test.py
"""
import sys
from pathlib import Path
import pandas as pd

sys.path.append(str(Path(__file__).parent.parent / "backend" / "nlp"))
from nlp_pipeline import NLPPipeline

# Each entry: (query text, true_intent, true_location_or_None, true_os_or_None, true_software_or_None)
# Ground truth assigned by hand -- this is the "expert-labeled" adversarial set.
STRESS_TEST_QUERIES = [
    ("Can the machines in Block A even handle Windows 11?", "os_compatibility_check", "Block A", "Windows 11", None),
    ("I don't think the Network Lab PCs support Win11, can you check?", "os_compatibility_check", "Network Lab", "Windows 11", None),
    ("Whats the deal with Block B and Windows 10 compatibility", "os_compatibility_check", "Block B", "Windows 10", None),
    ("Is there any chance the AI Lab computers run Fedora 42 ok?", "os_compatibility_check", "AI Lab", "Fedora 42", None),
    ("please tell me if programming lab systems r compatible w ubuntu 24.04", "os_compatibility_check", "Programming Lab", "Ubuntu 24.04", None),
    ("Block C machines -- Windows 11 yes or no", "os_compatibility_check", "Block C", "Windows 11", None),
    ("so which os is actually best for the library computers", "os_recommendation", "Library", None, None),
    ("if you had to pick one OS for CAD Lab what would it be", "os_recommendation", "CAD Lab", None, None),
    ("whats the ideal operating system given the specs in block d", "os_recommendation", "Block D", None, None),
    ("Language Lab needs a new OS, suggestions?", "os_recommendation", "Language Lab", None, None),
    ("what should we install on the research lab machines", "os_recommendation", "Research Lab", None, None),
    ("out of curiosity what os would you recommend for admin", "os_recommendation", "Admin", None, None),
    ("these block a computers are ancient, what needs replacing", "upgrade_planning", "Block A", None, None),
    ("figure out which machines in the network lab are due for an upgrade", "upgrade_planning", "Network Lab", None, None),
    ("we've got budget this year, what should we prioritize upgrading in block c", "upgrade_planning", "Block C", None, None),
    ("anything ancient still running in the library that needs attention", "upgrade_planning", "Library", None, None),
    ("time to replace old hardware -- where should we start in block b", "upgrade_planning", "Block B", None, None),
    ("does the programming lab even have enough ram for anything modern", "hardware_query", "Programming Lab", None, None),
    ("how many machines in block d have ssds", "hardware_query", "Block D", None, None),
    ("give me the cpu breakdown for the ai lab", "hardware_query", "AI Lab", None, None),
    ("whats the average ram across the research lab computers", "hardware_query", "Research Lab", None, None),
    ("do any admin block machines have tpm chips", "hardware_query", "Admin", None, None),
    ("can blender actually run on the cad lab machines", "software_compatibility_check", "CAD Lab", None, "Blender"),
    ("checking if photoshop would work on block c hardware", "software_compatibility_check", "Block C", None, "Photoshop"),
    ("will the network lab pcs handle wireshark fine", "software_compatibility_check", "Network Lab", None, "Wireshark"),
    ("thinking about installing matlab in the research lab, feasible?", "software_compatibility_check", "Research Lab", None, "MATLAB"),
    ("does anaconda run ok on the ai lab systems", "software_compatibility_check", "AI Lab", None, "Anaconda"),
    ("not sure if the library computers could run libreoffice smoothly", "software_compatibility_check", "Library", None, "LibreOffice"),
    ("what could we actually install on the current programming lab setup", "reverse_software_lookup", "Programming Lab", None, None),
    ("given the hardware in block a, what software options do we have", "reverse_software_lookup", "Block A", None, None),
    ("list stuff compatible with whatever is running in the language lab", "reverse_software_lookup", "Language Lab", None, None),
    ("what can these old admin machines actually still run", "reverse_software_lookup", "Admin", None, None),
    ("show compatible apps for block d hardware", "reverse_software_lookup", "Block D", None, None),
    # Deliberately harder: combined/ambiguous phrasing, minimal keyword overlap with templates
    ("upgrade or os change, which fixes block c faster", "upgrade_planning", "Block C", None, None),
    ("running old software on new labs, what os makes sense for that in the cad lab", "os_recommendation", "CAD Lab", None, None),
    ("lab 2 -- worth upgrading or just switch os?", "upgrade_planning", "Lab 2", None, None),
    ("what does the research lab even have installed right now", "hardware_query", "Research Lab", None, None),
    ("any machine anywhere that can run autocad without upgrades", "reverse_software_lookup", None, None, "AutoCAD"),
    ("give me a straight answer: win11 on block b, yes or no", "os_compatibility_check", "Block B", "Windows 11", None),
    ("honestly just tell me the best linux distro for ai lab", "os_recommendation", "AI Lab", None, None),
]


def run_stress_test():
    pipeline = NLPPipeline()
    results = []

    for text, true_intent, true_loc, true_os, true_sw in STRESS_TEST_QUERIES:
        parsed = pipeline.process(text)
        results.append({
            "text": text,
            "true_intent": true_intent,
            "pred_intent": parsed["intent"],
            "intent_correct": parsed["intent"] == true_intent,
            "intent_confidence": parsed["intent_confidence"],
            "true_location": true_loc,
            "pred_location": parsed["location"],
            "location_correct": parsed["location"] == true_loc,
            "true_os": true_os,
            "pred_os": parsed["target_os"],
            "os_correct": parsed["target_os"] == true_os,
            "true_software": true_sw,
            "pred_software": parsed["software"],
            "software_correct": parsed["software"] == true_sw,
        })

    df = pd.DataFrame(results)

    intent_acc = df["intent_correct"].mean()
    location_acc = df["location_correct"].mean()
    os_acc = df["os_correct"].mean()
    software_acc = df["software_correct"].mean()

    print(f"Stress test: {len(df)} hand-written adversarial queries\n")
    print(f"Intent accuracy:   {intent_acc:.1%}")
    print(f"Location accuracy: {location_acc:.1%}")
    print(f"Target OS accuracy: {os_acc:.1%}")
    print(f"Software accuracy: {software_acc:.1%}")

    print("\n--- Misclassified intents ---")
    wrong = df[~df["intent_correct"]]
    if wrong.empty:
        print("(none)")
    else:
        print(wrong[["text", "true_intent", "pred_intent"]].to_string(index=False))

    print("\n--- Entity extraction misses ---")
    entity_misses = df[~df["location_correct"] | ~df["os_correct"] | ~df["software_correct"]]
    if entity_misses.empty:
        print("(none)")
    else:
        print(entity_misses[["text", "true_location", "pred_location",
                              "true_os", "pred_os", "true_software", "pred_software"]].to_string(index=False))

    out_path = Path(__file__).parent / "nlp_stress_test_results.csv"
    df.to_csv(out_path, index=False)
    print(f"\nFull results saved to {out_path}")

    return df


if __name__ == "__main__":
    run_stress_test()
