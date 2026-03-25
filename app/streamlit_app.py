"""Streamlit interface for reviewing processed records and flagged items."""

from __future__ import annotations

import streamlit as st

from src.config.settings import Settings
from src.services.reporting import ReportingService
from src.services.storage import StorageService


def build_services() -> ReportingService:
    settings = Settings.from_env()
    storage_service = StorageService(settings)
    storage_service.init_db()
    return ReportingService(storage_service)


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
    processed = reporting_service.get_processed_requests()
    if processed.empty:
        st.info("No processed requests available.")
        return

    request_id = st.selectbox("Request ID", processed["request_id"].drop_duplicates().tolist())
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
