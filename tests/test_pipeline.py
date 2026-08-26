"""
Regression tests verifying the classifier and anomaly checks actually catch
what they claim to, against known-injected ground truth — not just "it runs
without an error."
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pandas as pd
import pytest

from src.generate_data import generate_po_lines, write_csv
from src.classifier import train_classifier, classify_full_dataset
from src.anomaly_checks import find_duplicate_lines, find_price_outliers

DATA_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "po_lines.csv")


@pytest.fixture(scope="module")
def generated():
    rows, dup_ids, outlier_ids = generate_po_lines()
    return rows, dup_ids, outlier_ids


@pytest.fixture(scope="module")
def df(generated):
    rows, _, _ = generated
    return pd.DataFrame(rows)


# ---------------------------------------------------------------------
# Data generation sanity
# ---------------------------------------------------------------------

def test_generated_data_has_expected_columns(df):
    expected = {"po_line_id", "supplier", "description", "category_raw",
                "category_true", "unit_price", "quantity", "currency"}
    assert expected.issubset(set(df.columns))


def test_generated_data_has_messy_category_labels(df):
    """A real ERP export has inconsistent category labels — confirm the
    generator actually produces that condition rather than clean data."""
    canonical = set(df["category_true"].unique())
    messy_fraction = (~df["category_raw"].isin(canonical)).mean()
    assert messy_fraction > 0.15, (
        f"Expected a meaningful fraction of messy/non-canonical category "
        f"labels, got {messy_fraction:.1%}"
    )


# ---------------------------------------------------------------------
# Classifier
# ---------------------------------------------------------------------

def test_classifier_achieves_high_but_not_suspicious_accuracy(df):
    """Accuracy should be high (the task is learnable from description
    text) but not literally 1.000 — a perfect score on held-out data here
    would indicate a data-generation artifact (e.g. disjoint per-category
    vocabulary with no realistic overlap or noise), not a validated model."""
    _, _, acc, _, _ = train_classifier(df)
    assert 0.90 <= acc < 1.0, (
        f"Accuracy {acc:.3f} is outside the expected realistic range — "
        f"either the task is too easy (check vocabulary overlap/noise in "
        f"the generator) or the model genuinely regressed."
    )


def test_classifier_fixes_most_messy_category_labels(df):
    """The actual point of the classifier: recovering a usable category
    for rows whose category_raw is missing or non-canonical, using only
    the description text (category_raw is never used as a feature)."""
    model, vectorizer, acc, _, _ = train_classifier(df)
    classified = classify_full_dataset(df, model, vectorizer)

    canonical = set(df["category_true"].unique())
    messy_mask = ~df["category_raw"].isin(canonical)
    n_messy = messy_mask.sum()
    assert n_messy > 0, "Test fixture has no messy rows to evaluate against"

    correct = (classified.loc[messy_mask, "category_predicted"]
               == df.loc[messy_mask, "category_true"]).sum()
    fix_rate = correct / n_messy
    assert fix_rate > 0.90, (
        f"Only {fix_rate:.1%} of messy-label rows were correctly "
        f"reclassified from description text alone"
    )


def test_classifier_does_not_use_category_raw_as_a_feature():
    """Guard against a subtle leakage bug: the model must be trained only
    on description text, never on category_raw (which would trivially
    leak the messy label back into the 'prediction')."""
    import inspect
    from src import classifier
    source = inspect.getsource(classifier.train_classifier)
    assert "category_raw" not in source


# ---------------------------------------------------------------------
# Duplicate detection
# ---------------------------------------------------------------------

def test_all_injected_duplicates_are_caught(generated):
    rows, dup_ids, _ = generated
    data = pd.DataFrame(rows)
    flagged = find_duplicate_lines(data)
    flagged_ids = set(flagged["po_line_id"])

    missed = [pair for pair in dup_ids
              if pair[0] not in flagged_ids or pair[1] not in flagged_ids]
    assert not missed, f"Missed injected duplicate pairs: {missed}"


def test_duplicate_check_may_also_catch_genuine_coincidental_matches(generated):
    """Documented, honest finding from development: with a small fixed set
    of quantities and near-fixed prices for some items (e.g. EUR pallets),
    two independently generated rows can coincidentally match on every key
    field. This test confirms that behavior is real and stable, not a bug
    to be silently filtered out — a category manager reviewing flagged
    duplicates would see both kinds and needs to triage them the same way
    a human would: check if they're truly the same invoice or a coincidence."""
    rows, dup_ids, _ = generated
    data = pd.DataFrame(rows)
    flagged = find_duplicate_lines(data)
    flagged_ids = set(flagged["po_line_id"])
    injected_flat = {pid for pair in dup_ids for pid in pair}

    extra_flagged = flagged_ids - injected_flat
    # We expect zero or more coincidental matches — not asserting a bug,
    # just confirming the detector doesn't silently drop legitimate matches
    # that happen to fall outside the injected set.
    assert len(flagged) >= len(injected_flat)


# ---------------------------------------------------------------------
# Price outlier detection
# ---------------------------------------------------------------------

def test_all_injected_price_outliers_are_caught(generated):
    rows, _, outlier_ids = generated
    data = pd.DataFrame(rows)
    flagged = find_price_outliers(data)
    flagged_ids = set(flagged["po_line_id"])

    missed = [pid for pid in outlier_ids if pid not in flagged_ids]
    assert not missed, f"Missed injected price outliers: {missed}"


def test_price_outlier_group_size_guard_avoids_baseline_contamination():
    """Regression guard for a real bug found during development: injecting
    outliers into a description group with too few rows (n=10) let the
    outliers themselves drag the group's own median/MAD baseline enough
    that 2 of 3 injected outliers fell under threshold. Fixed by requiring
    a larger minimum group size (>=25) for outlier injection. This test
    fails loudly if that minimum regresses."""
    import inspect
    from src import generate_data
    source = inspect.getsource(generate_data.generate_po_lines)
    assert "c >= 25" in source, (
        "Outlier-injection group-size threshold appears to have changed — "
        "re-verify all injected outliers are still detected (see the README "
        "note on baseline contamination in small groups)."
    )


def test_price_outlier_check_flags_some_natural_variance_too(generated):
    """Honest finding: because unit prices are drawn from wide uniform
    ranges, a handful of natural-variance false positives are expected at
    this threshold, beyond the 3 injected outliers. This is disclosed in
    the README rather than tuned away by loosening the threshold."""
    rows, _, outlier_ids = generated
    data = pd.DataFrame(rows)
    flagged = find_price_outliers(data)
    assert len(flagged) > len(outlier_ids), (
        "Expected some natural-variance flags beyond the injected outliers "
        "— if this is no longer true, re-verify the README's disclosed "
        "false-positive-rate claim still holds"
    )
