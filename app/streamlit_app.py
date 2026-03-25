"""Streamlit interface for reviewing processed records and flagged items."""

from __future__ import annotations

from pathlib import Path

import streamlit as st

from src.config.settings import Settings
from src.main import process_input
from src.services.reporting import ReportingService
from src.services.storage import StorageService
from src.utils.timestamps import utc_now_iso


def build_services() -> ReportingService:
    settings = Settings.from_env()
    storage_service = StorageService(settings)
    storage_service.init_db()
    return ReportingService(storage_service)


def infer_source_type(file_name: str) -> str:
    suffix = Path(file_name).suffix.lower()
    if suffix == ".txt":
        return "text_file"
    if suffix == ".csv":
        return "csv"
    if suffix == ".json":
        return "json"
    raise ValueError(f"unsupported file type: {suffix}")


def save_uploaded_file(uploaded_file) -> Path:
    upload_dir = Path("data/raw/uploads")
    upload_dir.mkdir(parents=True, exist_ok=True)
    timestamp = utc_now_iso().replace(":", "-")
    safe_name = f"{timestamp}_{uploaded_file.name}"
    target_path = upload_dir / safe_name
    target_path.write_bytes(uploaded_file.getbuffer())
    return target_path


def render_ingestion() -> None:
    st.title("Ingest Data")
    st.write("Submit pasted text or upload a supported file to process it into the platform.")

    business_domain = st.selectbox(
        "Business Domain Hint",
        ["", "architecture", "hospitality", "operations"],
        index=0,
    )
    effective_domain = business_domain or None

    with st.form("text_ingestion_form"):
        st.subheader("Paste Text")
        source_type = st.selectbox(
            "Text Source Type",
            ["pasted_text", "email_text"],
            index=0,
        )
        text_input = st.text_area("Request Content", height=220)
        submitted_text = st.form_submit_button("Process Text")

    if submitted_text:
        if not text_input.strip():
            st.error("Enter some text before processing.")
        else:
            try:
                with st.spinner("Processing text..."):
                    results = process_input(
                        text_input,
                        source_type=source_type,
                        business_domain_hint=effective_domain,
                    )
                st.success("Text processed successfully.")
                st.dataframe(
                    [
                        {
                            "request_id": result.request_id,
                            "status": result.status,
                            "message": result.message,
                        }
                        for result in results
                    ],
                    use_container_width=True,
                )
            except Exception as exc:
                st.error(str(exc))

    st.divider()

    uploaded_file = st.file_uploader("Upload `.txt`, `.csv`, or `.json`", type=["txt", "csv", "json"])
    if uploaded_file is not None:
        if st.button("Process Uploaded File"):
            try:
                source_type = infer_source_type(uploaded_file.name)
                saved_path = save_uploaded_file(uploaded_file)
                with st.spinner(f"Processing {uploaded_file.name}..."):
                    results = process_input(
                        str(saved_path),
                        source_type=source_type,
                        business_domain_hint=effective_domain,
                    )
                st.success(f"Processed {uploaded_file.name}.")
                st.dataframe(
                    [
                        {
                            "request_id": result.request_id,
                            "status": result.status,
                            "message": result.message,
                        }
                        for result in results
                    ],
                    use_container_width=True,
                )
            except Exception as exc:
                st.error(str(exc))


def render_dashboard(reporting_service: ReportingService) -> None:
    metrics = reporting_service.get_dashboard_metrics()
    st.title("AI Workflow Dashboard")
    st.metric("Total Requests", metrics["total_requests"])
    st.metric("Validated Requests", metrics["validated_requests"])
    st.metric("Review Queue Items", metrics["review_queue_items"])
    st.metric("Average Processing Time (ms)", metrics["average_processing_time_ms"] or "N/A")

    st.subheader("Request Type Breakdown")
    st.json(metrics["request_type_breakdown"])
    st.subheader("Source Type Breakdown")
    st.json(metrics["source_type_breakdown"])


def render_processed_requests(reporting_service: ReportingService) -> None:
    st.title("Processed Requests")
    frame = reporting_service.get_processed_requests()
    if frame.empty:
        st.info("No processed requests found yet.")
        return
    st.dataframe(frame, use_container_width=True)


def render_review_queue(reporting_service: ReportingService) -> None:
    st.title("Review Queue")
    frame = reporting_service.get_review_queue()
    if frame.empty:
        st.info("No review items found yet.")
        return
    st.dataframe(frame, use_container_width=True)


def render_request_detail(reporting_service: ReportingService) -> None:
    st.title("Request Detail")
    requests_index = reporting_service.get_requests_index()
    if requests_index.empty:
        st.info("No requests available yet.")
        return

    request_id = st.selectbox("Request ID", requests_index["request_id"].drop_duplicates().tolist())
    detail = reporting_service.get_request_detail(request_id)
    if detail is None:
        st.warning("Request not found.")
        return

    st.subheader("Source")
    st.json(
        {
            "request_id": detail["request_id"],
            "source_type": detail["source_type"],
            "source_name": detail["source_name"],
            "business_domain_hint": detail["business_domain_hint"],
            "metadata": detail["metadata"],
        }
    )
    st.subheader("Raw Content")
    st.code(detail["raw_content"])
    st.subheader("Outputs")
    st.json(detail["outputs"])
    st.subheader("Review Items")
    st.json(detail["review_items"])


def render_export(reporting_service: ReportingService) -> None:
    st.title("Export")
    frame = reporting_service.export_validated_records()
    if frame.empty:
        st.info("No validated records available for export.")
        return

    csv_bytes = frame.to_csv(index=False).encode("utf-8")
    st.download_button(
        label="Download validated records as CSV",
        data=csv_bytes,
        file_name="validated_records.csv",
        mime="text/csv",
    )
    st.dataframe(frame, use_container_width=True)


def main() -> None:
    st.set_page_config(page_title="AI Workflow Dashboard", layout="wide")
    reporting_service = build_services()
    pages = {
        "Ingest Data": lambda _: render_ingestion(),
        "Dashboard": render_dashboard,
        "Processed Requests": render_processed_requests,
        "Review Queue": render_review_queue,
        "Request Detail": render_request_detail,
        "Export": render_export,
    }
    page_name = st.sidebar.radio("View", list(pages.keys()))
    pages[page_name](reporting_service)


if __name__ == "__main__":
    main()
