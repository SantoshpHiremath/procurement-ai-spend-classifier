"""
Spend classification: predicts a canonical spend category from the free-text
item description, independent of whatever (often missing or inconsistent)
category_raw label the ERP export happened to carry.

This is the "structuring data for AI" + "AI use case in procurement" core:
category_raw is deliberately NOT used as a model feature — the point is to
classify from the description text itself, since that's the only field
that's reliably present and consistent in real procurement exports.
"""
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, classification_report


def load_data(path):
    return pd.read_csv(path)


def train_classifier(df, seed=42):
    """Train a TF-IDF + logistic regression classifier on description text.

    Ground truth (category_true) is used only for training/evaluation, as
    it would be in a real project: category_true simulates a category
    manager's manually-labeled sample used to train the model, which is
    then applied to the full, messier dataset.
    """
    X_train, X_test, y_train, y_test = train_test_split(
        df["description"], df["category_true"],
        test_size=0.25, random_state=seed, stratify=df["category_true"],
    )

    vectorizer = TfidfVectorizer(ngram_range=(1, 2), min_df=2)
    X_train_vec = vectorizer.fit_transform(X_train)
    X_test_vec = vectorizer.transform(X_test)

    model = LogisticRegression(max_iter=1000, random_state=seed)
    model.fit(X_train_vec, y_train)

    y_pred = model.predict(X_test_vec)
    acc = accuracy_score(y_test, y_pred)
    report = classification_report(y_test, y_pred, zero_division=0)

    return model, vectorizer, acc, report, (X_test, y_test, y_pred)


def predict_categories(model, vectorizer, descriptions):
    vec = vectorizer.transform(descriptions)
    return model.predict(vec)


def classify_full_dataset(df, model, vectorizer):
    """Apply the trained classifier to every row's description, regardless
    of what category_raw says — this is the step that actually fixes the
    messy/missing-label problem."""
    df = df.copy()
    df["category_predicted"] = predict_categories(model, vectorizer, df["description"])
    return df


if __name__ == "__main__":
    df = load_data("data/po_lines.csv")
    model, vectorizer, acc, report, _ = train_classifier(df)
    print(f"Held-out test accuracy: {acc:.3f}")
    print(report)

    classified = classify_full_dataset(df, model, vectorizer)
    # How many rows had a missing/non-canonical category_raw that the
    # classifier was still able to fill in from the description alone?
    canonical = set(df["category_true"].unique())
    messy_mask = ~df["category_raw"].isin(canonical)
    n_messy = messy_mask.sum()
    n_messy_fixed_correctly = (
        (classified.loc[messy_mask, "category_predicted"] == df.loc[messy_mask, "category_true"])
    ).sum()
    print(f"\nRows with missing/non-canonical category_raw: {n_messy}")
    print(f"Of those, correctly classified from description alone: {n_messy_fixed_correctly} "
          f"({n_messy_fixed_correctly / n_messy:.1%})")
