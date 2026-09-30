import pandas as pd

from core.load import load_csv, load_inbox


def write(tmp_path, name, text):
    path = tmp_path / name
    path.write_text(text)
    return path


def test_question_mark_and_blank_become_missing_but_none_is_kept(tmp_path):
    path = write(tmp_path, "a.csv", "kind,who\n?,None\n,Police\n")
    df = load_csv(path)
    assert df["kind"].isna().all()
    assert df["who"].tolist() == ["None", "Police"]


def test_date_columns_are_parsed(tmp_path):
    path = write(tmp_path, "a.csv", "incident_date,amount\n2015-01-25,100\n")
    df = load_csv(path)
    assert pd.api.types.is_datetime64_any_dtype(df["incident_date"])
    assert df["amount"].dtype == "int64"


def test_load_inbox_reads_every_csv(tmp_path):
    write(tmp_path, "a.csv", "x\n1\n")
    write(tmp_path, "b.csv", "y\n2\n")
    write(tmp_path, "notes.txt", "ignore me")
    assert set(load_inbox(tmp_path)) == {"a", "b"}
