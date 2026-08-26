"""
Procurement data-quality checks: duplicate invoice-line detection and
price-outlier detection within a spend category — the "AI-assisted spend
review" half of the use case, aimed at catching overpayment risk and
pricing errors that a category manager would otherwise have to find
manually in a spreadsheet.
"""
import pandas as pd


def find_duplicate_lines(df):
    """Flag near-identical PO lines (same supplier, description stripped
    of whitespace, price, and quantity) as likely duplicate invoice
    entries — a common source of accidental overpayment."""
    work = df.copy()
    work["_desc_norm"] = work["description"].str.strip().str.lower()
    key_cols = ["supplier", "_desc_norm", "unit_price", "quantity"]

    dup_mask = work.duplicated(subset=key_cols, keep=False)
    duplicates = work.loc[dup_mask].sort_values(key_cols)
    return duplicates.drop(columns=["_desc_norm"])


def find_price_outliers(df, z_threshold=3.0, min_group_size=5):
    """Flag line items whose unit price is a statistical outlier relative
    to other purchases of the same description — a common early signal of
    a pricing error or a data-entry mistake worth a category manager's
    attention, not an automatic conclusion of fraud."""
    results = []
    for desc, group in df.groupby("description"):
        if len(group) < min_group_size:
            continue
        median = group["unit_price"].median()
        mad = (group["unit_price"] - median).abs().median()
        if mad == 0:
            continue
        # 1.4826 scales MAD to be comparable to a standard deviation
        # under a normal distribution — the same robust z-score approach
        # used in the BIRKENSTOCK anomaly-detection project.
        scaled_mad = 1.4826 * mad
        z = (group["unit_price"] - median) / scaled_mad
        flagged = group.loc[z.abs() >= z_threshold].copy()
        if len(flagged):
            flagged["price_z_score"] = z.loc[flagged.index].round(2)
            flagged["category_median_price"] = median
            results.append(flagged)

    if not results:
        return pd.DataFrame(columns=list(df.columns) + ["price_z_score", "category_median_price"])
    return pd.concat(results).sort_values("price_z_score", key=abs, ascending=False)


if __name__ == "__main__":
    df = pd.read_csv("data/po_lines.csv")

    dups = find_duplicate_lines(df)
    print(f"Flagged {len(dups)} rows as likely duplicate invoice lines "
          f"({len(dups)//2} pairs)")

    outliers = find_price_outliers(df)
    print(f"Flagged {len(outliers)} rows as price outliers")
    print(outliers[["po_line_id", "description", "unit_price",
                     "category_median_price", "price_z_score"]].to_string(index=False))
