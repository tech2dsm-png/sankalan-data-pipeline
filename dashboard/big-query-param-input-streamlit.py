import streamlit as st
from google.cloud import bigquery
from database.conn import get_bq_client
import datetime

# Initialize BigQuery client
client = get_bq_client()

# Set default dates
start_date = st.date_input("Start Date", value=datetime.date(2025, 9, 1))
end_date = st.date_input("End Date", value=datetime.date(2025, 9, 8))

# Convert dates to string suffixes
start_suffix = start_date.strftime('%Y%m%d')
end_suffix = end_date.strftime('%Y%m%d')

# Define your table pattern
table_pattern = "`brilliant-dryad-439810-q6.analytics_453034732.events_*`"

# Construct the query with specific columns and date filtering
query = f"""
SELECT 
  event_date,
  event_timestamp,
  event_name,
  user_id,
  user_pseudo_id
FROM {table_pattern}
WHERE _TABLE_SUFFIX BETWEEN @start_suffix AND @end_suffix
LIMIT 10
"""

# Set query parameters
job_config = bigquery.QueryJobConfig(
    query_parameters=[
        bigquery.ScalarQueryParameter("start_suffix", "STRING", start_suffix),
        bigquery.ScalarQueryParameter("end_suffix", "STRING", end_suffix),
    ]
)

# Run the query
query_job = client.query(query, job_config=job_config)
results = query_job.result()

# Convert results to DataFrame
import pandas as pd
df = results.to_dataframe()

# Display the DataFrame in Streamlit
st.dataframe(df)