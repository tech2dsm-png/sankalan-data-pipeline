import os
import streamlit as st
from google.cloud import bigquery
from google.oauth2 import service_account
import json

def get_bq_client():
    """
    Returns a BigQuery client.
    - On Streamlit Cloud: reads credentials from st.secrets
    - Locally: reads credentials from local JSON file (service-account.json)
    """
    try:
        # --- Local environment ---
        if os.path.exists("service-account.json"):
            credentials = service_account.Credentials.from_service_account_file("service-account.json")
            project_id = "brilliant-dryad-439810-q6"  # Your GCP project ID
            client = bigquery.Client(credentials=credentials, project=project_id)
            return client

        # --- Streamlit Cloud ---
        service_account_info = st.secrets.get("gcp_service_account")
        if service_account_info:
            credentials = service_account.Credentials.from_service_account_info(service_account_info)
            project_id = service_account_info.get("project_id")
            client = bigquery.Client(credentials=credentials, project=project_id)
            return client

        st.error("No BigQuery credentials found! Add 'service-account.json' locally or 'gcp_service_account' secret in Streamlit.")
        return None

    except Exception as e:
        st.error(f"Failed to create BigQuery client: {e}")
        return None