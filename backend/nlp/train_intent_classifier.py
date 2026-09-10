"""
Trains the intent classifier on nlp_query_dataset_10000.csv.

Approach: TF-IDF + Logistic Regression. This is deliberately NOT a heavy
transformer model — for a 6-class, single-domain, 10k-row dataset like
this one, TF-IDF + Logistic Regression trains in seconds, is easy to
explain in a paper (no black-box concerns), and typically reaches 95%+
accuracy on well-separated intents like these. Swap in DistilBERT later
(see train_intent_classifier_bert.py) only if you need the comparison
for your paper's "model choice justification" section.

Usage:
    python train_intent_classifier.py
"""
import pandas as pd
import joblib
from pathlib import Path
from sklearn.model_selection import train_test_split
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import classification_report, confusion_matrix
from sklearn.pipeline import Pipeline

DATA_PATH = Path(__file__).parent.parent.parent / "data" / "nlp_query_dataset_10000.csv"
MODEL_DIR = Path(__file__).parent / "saved_models"
MODEL_DIR.mkdir(exist_ok=True)


def main():
    df = pd.read_csv(DATA_PATH)
    print(f"Loaded {len(df)} queries across {df['intent'].nunique()} intents.")
    print(df['intent'].value_counts(), "\n")

    X = df["text"]
    y = df["intent"]

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )

    pipeline = Pipeline([
        ("tfidf", TfidfVectorizer(
            ngram_range=(1, 2),      # unigrams + bigrams capture phrases like "not compatible"
            max_features=5000,
            stop_words="english",
        )),
        ("clf", LogisticRegression(
            max_iter=1000,
            C=5.0,
            class_weight="balanced",  # guards against the slight class imbalance
        )),
    ])

    print("Training...")
    pipeline.fit(X_train, y_train)

    y_pred = pipeline.predict(X_test)

    print("\n=== Classification Report (test set) ===")
    print(classification_report(y_test, y_pred))

    print("=== Confusion Matrix ===")
    labels = sorted(y.unique())
    cm = confusion_matrix(y_test, y_pred, labels=labels)
    cm_df = pd.DataFrame(cm, index=labels, columns=labels)
    print(cm_df)

    model_path = MODEL_DIR / "intent_classifier.joblib"
    joblib.dump(pipeline, model_path)
    print(f"\nModel saved to {model_path}")

    # Save the classification report to disk for your paper's evaluation section
    report_dict = classification_report(y_test, y_pred, output_dict=True)
    report_df = pd.DataFrame(report_dict).transpose()
    report_df.to_csv(MODEL_DIR / "evaluation_report.csv")
    print(f"Evaluation report saved to {MODEL_DIR / 'evaluation_report.csv'}")


if __name__ == "__main__":
    main()
