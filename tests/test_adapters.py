import json

from src.adapters.csv_adapter import CsvAdapter
from src.adapters.email_text_adapter import EmailTextAdapter
from src.adapters.json_adapter import JsonAdapter
from src.adapters.text_adapter import TextAdapter
from src.models.enums import SourceType


def test_text_adapter_supports_pasted_text() -> None:
    adapter = TextAdapter()
    record = adapter.load("Please update the booking allocation.")

    assert record.source_type == SourceType.PASTED_TEXT.value
    assert "booking allocation" in record.raw_content


def test_csv_adapter_loads_each_row_as_record(tmp_path) -> None:
    csv_path = tmp_path / "requests.csv"
    csv_path.write_text("request,priority\nUpdate booking,high\nReview catering,medium\n", encoding="utf-8")

    records = CsvAdapter().load_many(csv_path)

    assert len(records) == 2
    assert records[0].source_type == SourceType.CSV.value


def test_json_adapter_loads_list_payload(tmp_path) -> None:
    json_path = tmp_path / "requests.json"
    json_path.write_text(json.dumps([{"content": "Need a summary."}, {"message": "Urgent issue."}]), encoding="utf-8")

    records = JsonAdapter().load_many(json_path)

    assert len(records) == 2
    assert records[1].source_type == SourceType.JSON.value


def test_email_adapter_detects_email_text() -> None:
    adapter = EmailTextAdapter()

    assert adapter.can_handle("Subject: Update needed\nPlease revise the booking details.")
