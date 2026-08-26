"""
End-to-end pipeline: generate synthetic PO data, train the spend
classifier, apply it to fix messy category labels, and run the
duplicate/price-outlier checks — then print a management-style summary.
"""
import pandas as pd

from generate_data import generate_po_lines, write_csv
from classifier import train_classifier, classify_full_dataset
from anomaly_checks import find_duplicate_lines, find_price_outliers


def run():
    rows, injected_dup_ids, injected_outlier_ids = generate_po_lines()
    write_csv(rows, "data/po_lines.csv")
    df = pd.DataFrame(rows)

    print(f"Loaded {len(df)} synthetic PO line items across "
          f"{df['category_true'].nunique()} spend categories and "
          f"{df['supplier'].nunique()} suppliers.\n")

    # --- Spend classification ---
    model, vectorizer, acc, report, _ = train_classifier(df)
    classified = classify_full_dataset(df, model, vectorizer)

    canonical = set(df["category_true"].unique())
    messy_mask = ~df["category_raw"].isin(canonical)
    n_messy = messy_mask.sum()
    n_fixed = (classified.loc[messy_mask, "category_predicted"]
               == df.loc[messy_mask, "category_true"]).sum()

    print(f"[Spend Classification] Held-out test accuracy: {acc:.1%}")
    print(f"[Spend Classification] {n_messy} of {len(df)} rows had a missing "
          f"or non-canonical category label in the raw export.")
    print(f"[Spend Classification] {n_fixed} of those ({n_fixed/n_messy:.1%}) "
          f"were correctly reclassified from the item description alone.\n")

    # --- Data quality checks ---
    dups = find_duplicate_lines(df)
    outliers = find_price_outliers(df)

    print(f"[Data Quality] {len(dups)} rows flagged as likely duplicate "
          f"invoice lines ({len(dups)//2} pairs) — potential overpayment risk.")
    print(f"[Data Quality] {len(outliers)} rows flagged as price outliers "
          f"relative to their category's typical price — worth a category "
          f"manager's review.\n")

    classified.to_csv("data/po_lines_classified.csv", index=False)
    dups.to_csv("data/flagged_duplicates.csv", index=False)
    outliers.to_csv("data/flagged_outliers.csv", index=False)
    print("Wrote: data/po_lines_classified.csv, data/flagged_duplicates.csv, "
          "data/flagged_outliers.csv")


if __name__ == "__main__":
    run()
