"""CSV loader for legacy mainframe exports.

The mainframe writes ISO-8859-1 (latin-1). Records are rows of
`order_id,customer_name,item,quantity` where customer names may contain
accented characters (e.g. "José", "Müller").
"""
import csv


def read_records(path):
    """Return a list of dicts with keys order_id, customer_name, item, quantity."""
    records = []
    with open(path, "r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            row["quantity"] = int(row["quantity"])
            records.append(row)
    return records