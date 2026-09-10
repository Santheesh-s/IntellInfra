"""
Combines intent classification + entity extraction into a single call.
This is what main.py's /query endpoint uses.
"""
import joblib
from pathlib import Path
from entity_extractor import EntityExtractor

MODEL_PATH = Path(__file__).parent / "saved_models" / "intent_classifier.joblib"


class NLPPipeline:
    def __init__(self):
        self.intent_model = joblib.load(MODEL_PATH)
        self.entity_extractor = EntityExtractor()

    def process(self, text: str) -> dict:
        intent = self.intent_model.predict([text])[0]
        confidence = float(max(self.intent_model.predict_proba([text])[0]))
        entities = self.entity_extractor.extract(text)

        return {
            "text": text,
            "intent": intent,
            "intent_confidence": round(confidence, 3),
            **entities,
        }


if __name__ == "__main__":
    pipeline = NLPPipeline()
    for q in [
        "Show all computers in Block C that cannot run Windows 11",
        "Recommend the best OS for the Research Lab",
        "Which systems in the CAD Lab can run AutoCAD?",
    ]:
        print(q)
        print(" ->", pipeline.process(q))
        print()
