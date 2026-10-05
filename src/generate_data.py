"""
Synthetic procurement spend data generator.

Generates realistic purchase-order line items with messy, inconsistent
free-text descriptions (as real ERP/procurement exports actually look —
abbreviations, inconsistent casing, typos, missing fields) across multiple
spend categories and suppliers, with deliberately injected data-quality
problems:

1. Inconsistent / missing spend category labels (the real-world state
   procurement data is usually in before any classification effort).
2. Duplicate invoice line items (a common source of overpayment).
3. Price outliers on an otherwise-consistent SKU (a common early signal
   of a pricing error or a data-entry mistake).

All data is synthetic. No real supplier or pricing data
is used or implied anywhere in this project.
"""
import csv
import random

RNG_SEED = 42

SUPPLIERS = [
    "Continental AG", "ZF Friedrichshafen", "Bosch Rexroth", "Voith Turbo",
    "Wabco Holdings", "SKF Group", "Faiveley Transport", "Haldex AB",
    "Schaeffler Technologies", "Freudenberg Sealing", "Trelleborg Sealing",
    "Bilstein GmbH", "Elringklinger AG", "Mahle GmbH", "Hella GmbH",
]

# category -> list of (item description template, unit price range)
CATEGORY_TEMPLATES = {
    "Raw Materials - Steel": [
        ("Steel sheet {grade} {thickness}mm", (180, 420)),
        ("Forged steel billet {grade}", (350, 900)),
        ("Steel coil hot-rolled {grade}", (200, 480)),
    ],
    "Raw Materials - Rubber": [
        ("Rubber compound {grade} sheet", (12, 45)),
        ("EPDM rubber seal stock {grade}", (18, 60)),
        ("Vulcanized rubber block {grade}", (25, 70)),
    ],
    "Electronic Components": [
        ("PCB assembly {spec}", (8, 220)),
        ("Pressure sensor unit {spec}", (35, 310)),
        ("Wiring harness connector {spec}", (5, 90)),
    ],
    "MRO - Maintenance Supplies": [
        ("Industrial lubricant {spec} 20L drum", (60, 180)),
        ("Hydraulic hose fitting {spec}", (10, 55)),
        ("Bearing assembly {spec}", (40, 260)),
    ],
    "Packaging & Logistics": [
        ("Wooden pallet EUR standard", (8, 22)),
        ("Corrugated shipping crate {spec}", (15, 60)),
        ("Stretch wrap film {spec} roll", (12, 35)),
    ],
    "IT & Office Equipment": [
        ("Laptop {spec} business grade", (650, 1450)),
        ("Office chair ergonomic {spec}", (120, 380)),
        ("Monitor 27in {spec}", (140, 320)),
    ],
}

# Deliberately ambiguous / overlapping-vocabulary items that exist in real
# procurement catalogs across more than one category, so the classification
# task isn't trivially separable by disjoint per-category keywords alone.
AMBIGUOUS_TEMPLATES = {
    "Electronic Components": [("Connector assembly {spec} sealed", (6, 95))],
    "MRO - Maintenance Supplies": [("Seal kit connector housing {spec}", (12, 70))],
    "Raw Materials - Rubber": [("Sealing gasket sheet {grade}", (10, 40))],
    "Packaging & Logistics": [("Protective foam sheet {spec}", (9, 28))],
}
for _cat, _templates in AMBIGUOUS_TEMPLATES.items():
    CATEGORY_TEMPLATES[_cat].extend(_templates)

GRADES = ["S355", "S235", "DC01", "X5CrNi", "42CrMo4", "70Sh-A", "60Sh-A", "NBR-70"]
SPECS = ["v2", "v3", "Rev.B", "Type-A", "std", "HD", "compact", "M12", "24V", "230V"]
THICKNESS = ["1.5", "2.0", "3.0", "4.0", "6.0", "8.0"]

# Messy casing / abbreviation variants applied to category labels to
# simulate inconsistent ERP data entry — the real starting condition
# spend-classification projects have to clean up first.
CATEGORY_LABEL_VARIANTS = {
    "Raw Materials - Steel": ["Raw Materials - Steel", "RAW MAT-STEEL", "raw materials/steel", "Steel", ""],
    "Raw Materials - Rubber": ["Raw Materials - Rubber", "RAW MAT-RUBBER", "rubber", "Raw Mat. Rubber", ""],
    "Electronic Components": ["Electronic Components", "ELEC COMP", "electronics", "Elec. Components", ""],
    "MRO - Maintenance Supplies": ["MRO - Maintenance Supplies", "MRO", "maintenance", "MRO/Maint", ""],
    "Packaging & Logistics": ["Packaging & Logistics", "PACKAGING", "packaging/logistics", "Pack & Log", ""],
    "IT & Office Equipment": ["IT & Office Equipment", "IT EQUIP", "it/office", "IT & Office", ""],
}

CURRENCIES = ["EUR"]


def _fill_template(template, rng):
    return template.format(
        grade=rng.choice(GRADES),
        spec=rng.choice(SPECS),
        thickness=rng.choice(THICKNESS),
    )


def _add_realistic_noise(description, rng):
    """Apply realistic ERP free-text noise: typos, truncation, extra
    whitespace, inconsistent casing, and occasional irrelevant supplier
    boilerplate — so the classification task isn't trivially separable
    by clean per-category vocabulary alone."""
    text = description

    # ~12% chance: truncate the description (common in fixed-width ERP fields)
    if rng.random() < 0.12 and len(text) > 12:
        cut = rng.randint(int(len(text) * 0.6), len(text) - 1)
        text = text[:cut]

    # ~15% chance: a simple character-level typo (swap two adjacent chars)
    if rng.random() < 0.15 and len(text) > 4:
        pos = rng.randint(0, len(text) - 2)
        chars = list(text)
        chars[pos], chars[pos + 1] = chars[pos + 1], chars[pos]
        text = "".join(chars)

    # ~20% chance: ALL CAPS or all lowercase (inconsistent ERP entry)
    r = rng.random()
    if r < 0.10:
        text = text.upper()
    elif r < 0.20:
        text = text.lower()

    # ~10% chance: prepend generic order boilerplate that carries no
    # category signal, forcing the model to rely on the actual item words
    if rng.random() < 0.10:
        text = rng.choice(["PO item: ", "order ref pending - ", "misc / "]) + text

    return text


def generate_po_lines(n_lines=4200, seed=RNG_SEED):
    """Generate synthetic PO line items with realistic messiness.

    Returns a list of dicts. Roughly 30% of rows get a non-canonical or
    blank category label (simulating real ERP export inconsistency) —
    the classifier is trained/evaluated on the canonical labels and
    tested specifically on its ability to handle the messy ones.
    """
    rng = random.Random(seed)
    categories = list(CATEGORY_TEMPLATES.keys())
    rows = []
    po_counter = 100000

    for i in range(n_lines):
        category = rng.choice(categories)
        template, price_range = rng.choice(CATEGORY_TEMPLATES[category])
        description = _fill_template(template, rng)
        description = _add_realistic_noise(description, rng)
        supplier = rng.choice(SUPPLIERS)
        unit_price = round(rng.uniform(*price_range), 2)
        qty = rng.choice([1, 2, 5, 10, 20, 50, 100, 200])
        po_counter += 1

        label_variant = rng.choices(
            CATEGORY_LABEL_VARIANTS[category],
            weights=[55, 15, 15, 10, 5],
            k=1,
        )[0]

        rows.append({
            "po_line_id": f"PO-{po_counter}-{i%7 or 7}",
            "supplier": supplier,
            "description": description,
            "category_raw": label_variant,
            "category_true": category,  # ground truth, kept separate for evaluation only
            "unit_price": unit_price,
            "quantity": qty,
            "currency": "EUR",
        })

    # --- Inject duplicate invoice lines (overpayment risk signal) ---
    # Pick a handful of rows and duplicate them near-identically, as
    # would happen with a double-submitted invoice or a re-keyed entry.
    dup_source_idx = rng.sample(range(len(rows)), 14)
    injected_duplicate_ids = []
    for idx in dup_source_idx:
        original = rows[idx]
        po_counter += 1
        dup = dict(original)
        dup["po_line_id"] = f"PO-{po_counter}-{rng.randint(1,7)}"
        # tiny formatting difference, as real duplicate re-entries usually have
        dup["description"] = original["description"] + " "
        rows.append(dup)
        injected_duplicate_ids.append((original["po_line_id"], dup["po_line_id"]))

    # --- Inject price outliers on otherwise-consistent items ---
    # Take a description that appears many times (>=25 rows, so a small
    # number of outliers can't meaningfully drag the group's own median/MAD
    # baseline — a real limitation of robust z-scores on small groups,
    # documented in the README rather than avoided by tuning the threshold)
    # and give a few instances a wildly different price (a common signal of
    # a data-entry error or a supplier pricing mistake worth flagging to a
    # category manager). All outliers use the same direction (price too
    # high) to keep this a clean, unambiguous injected signal.
    from collections import Counter
    desc_counts = Counter(r["description"] for r in rows)
    common_desc = [d for d, c in desc_counts.items() if c >= 25]
    injected_outlier_ids = []
    if common_desc:
        target_desc = rng.choice(common_desc)
        candidates = [r for r in rows if r["description"] == target_desc]
        outlier_rows = rng.sample(candidates, min(3, len(candidates)))
        for r in outlier_rows:
            multiplier = rng.choice([5.5, 6.0])
            r["unit_price"] = round(r["unit_price"] * multiplier, 2)
            injected_outlier_ids.append(r["po_line_id"])

    rng.shuffle(rows)
    return rows, injected_duplicate_ids, injected_outlier_ids


def write_csv(rows, path):
    fieldnames = ["po_line_id", "supplier", "description", "category_raw",
                  "category_true", "unit_price", "quantity", "currency"]
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


if __name__ == "__main__":
    rows, dup_ids, outlier_ids = generate_po_lines()
    write_csv(rows, "data/po_lines.csv")
    print(f"Generated {len(rows)} PO line items")
    print(f"Injected duplicate pairs: {dup_ids}")
    print(f"Injected price outliers: {outlier_ids}")
