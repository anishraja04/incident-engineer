from importer.loader import read_records


def test_all_records_loaded():
    records = read_records("data/orders.csv")
    assert len(records) == 5


def test_customer_names_with_accents_preserved():
    """Accented names from the legacy export must survive the import."""
    records = {r["order_id"]: r["customer_name"] for r in read_records("data/orders.csv")}
    assert records["ORD-0001"] == "José Almeida"
    assert records["ORD-0002"] == "Müller & Söhne"
    assert records["ORD-0003"] == "Anna López"
    assert records["ORD-0004"] == "Björn Åkesson"
    assert records["ORD-0005"] == "Stéphane Girard"


def test_quantities_are_ints():
    for r in read_records("data/orders.csv"):
        assert isinstance(r["quantity"], int)