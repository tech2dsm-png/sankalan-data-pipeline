import streamlit as st
import pandas as pd
import altair as alt
import os
import sys
import datetime

# Add parent directory to system path for imports from the 'database' folder
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from database.conn import get_bq_client

# --- SQL query file paths ---
query_kpis_file = os.path.join(os.path.dirname(__file__), '..', 'database', 'phase_3_kpis.sql')
query_trends_file = os.path.join(os.path.dirname(__file__), '..', 'database', 'phase_4_trends.sql')
query_top_pages_file = os.path.join(os.path.dirname(__file__), '..', 'database', 'phase_4_top_pages.sql')
query_device_file = os.path.join(os.path.dirname(__file__), '..', 'database', 'phase_4_device_breakdown.sql')
query_browser_file = os.path.join(os.path.dirname(__file__), '..', 'database', 'phase_4_browser_breakdown.sql')
query_traffic_file = os.path.join(os.path.dirname(__file__), '..', 'database', 'phase_4_traffic_source.sql')  # fixed typo
query_user_clusters_file = os.path.join(os.path.dirname(__file__), '..', 'database', 'phase_5_user_clusters.sql')
query_bounce_file = os.path.join(os.path.dirname(__file__), '..', 'database', 'phase_5_predicted_bounce.sql')

# --- Streamlit caching ---
@st.cache_data
def get_data_from_bigquery(query_file_path, start_date, end_date):
    try:
        with open(query_file_path, 'r') as f:
            query_template = f.read()

        start_date_str = start_date.strftime('%Y-%m-%d')
        end_date_str = end_date.strftime('%Y-%m-%d')

        query = query_template.format(
            start_date=f"DATE('{start_date_str}')",
            end_date=f"DATE('{end_date_str}')"
        )

        client = get_bq_client()
        if client is None:
            st.error("Failed to connect to BigQuery. Check your credentials.")
            return pd.DataFrame()

        df = client.query(query).to_dataframe()
        return df
    except Exception as e:
        st.error(f"Error fetching data: {e}")
        return pd.DataFrame()

# --- Streamlit Layout ---
st.set_page_config(page_title="Sankalan Analytics Dashboard", layout="wide")
st.title("📊 Website Analytics Dashboard")
st.markdown("Interactive dashboard showing KPIs, trends, top pages, device breakdown, user segments, and bounce predictions.")
st.markdown("---")

# --- Sidebar Filters ---
st.sidebar.header("Filters")
start_date = st.sidebar.date_input("Start Date")
end_date = st.sidebar.date_input("End Date")

if start_date > end_date:
    st.sidebar.error("Start Date cannot be after End Date")

# --- Tabs ---
tab1, tab2, tab3, tab4, tab5, tab6, tab7, tab8 = st.tabs(
    ["KPIs", "Traffic Trends", "Top Pages", "Devices", "Browser", "Traffic Sources", "User Segments", "Bounce Prediction"]
)

# -------------------------------
# Tab 1: KPIs
# -------------------------------
with tab1:
    df_kpis = get_data_from_bigquery(query_kpis_file, start_date, end_date)
    if not df_kpis.empty:
        col1, col2, col3, col4, col5, col6 = st.columns(6)
        col1.metric("Total Sessions", int(df_kpis['total_sessions'].fillna(0)[0]))
        col2.metric("Page Views", int(df_kpis['total_page_views'].fillna(0)[0]))

        seconds = int(df_kpis['avg_session_duration'].fillna(0)[0])
        formatted_duration = str(datetime.timedelta(seconds=seconds))
        col3.metric("Avg Session Duration", formatted_duration)

        col4.metric("Avg Engagement Rate (%)", round(df_kpis['avg_engagement_rate'].fillna(0)[0]*100, 2))
        col5.metric("Avg Bounce Rate (%)", round(df_kpis['avg_bounce_rate'].fillna(0)[0]*100, 2))
        col6.metric("Unique Visitors", int(df_kpis['unique_visitors'].fillna(0)[0]))  # new KPI

        # Narrative
        bounce_rate = round(df_kpis['avg_bounce_rate'].fillna(0)[0]*100, 2)
        if bounce_rate > 70:
            st.info("⚠️ Many visitors are leaving quickly (high bounce rate). Check page speed or content relevance.")
        else:
            st.success("✅ Bounce rate looks fine. Visitors are engaging with your site.")
    else:
        st.warning("No KPI data available.")

# -------------------------------
# Tab 2: Traffic Trends
# -------------------------------
with tab2:
    df_trends = get_data_from_bigquery(query_trends_file, start_date, end_date)
    if not df_trends.empty:
        chart = alt.Chart(df_trends).mark_line().encode(
            x=alt.X('event_date:T', axis=alt.Axis(title='Date', format='%b %d')),
            y=alt.Y('daily_page_views:Q', axis=alt.Axis(title='Page Views')),
            tooltip=[
                alt.Tooltip('event_date:T', title='Date', format='%Y-%m-%d'),
                alt.Tooltip('daily_page_views:Q', title='Page Views', format=',')
            ]
        ).properties(title="Daily Page Views Over Time").interactive()
        st.altair_chart(chart, use_container_width=True)

        latest_views = df_trends['daily_page_views'].iloc[-1]
        st.write(f"📈 On the last recorded day, your site had **{latest_views} page views**.")
    else:
        st.warning("No traffic trend data available.")

# -------------------------------
# Tab 3: Top Pages
# -------------------------------
with tab3:
    df_pages = get_data_from_bigquery(query_top_pages_file, start_date, end_date)
    if not df_pages.empty:
        df_pages['page_views'] = df_pages['page_views'].fillna(0).astype(int)
        chart_pages = alt.Chart(df_pages).mark_bar().encode(
            x='page_views:Q',
            y=alt.Y('page_url:N', sort='-x'),
            tooltip=['page_url', 'page_views', 'sessions', 'unique_users']
        )
        st.altair_chart(chart_pages, use_container_width=True)
        st.subheader("📋 Top Pages Data")
        st.dataframe(df_pages)

        top_page = df_pages.loc[df_pages['page_views'].idxmax()]
        st.write(f"🔥 Your most visited page is **{top_page['page_url']}** with **{top_page['page_views']} views**.")
    else:
        st.warning("No top pages data available.")

# -------------------------------
# Tab 4: Devices
# -------------------------------
with tab4:
    df_device = get_data_from_bigquery(query_device_file, start_date, end_date)
    if not df_device.empty:
        df_device['sessions'] = df_device['sessions'].fillna(0).astype(int)
        df_device['percentage'] = (df_device['sessions'] / df_device['sessions'].sum()) * 100

        chart_device = alt.Chart(df_device).mark_arc(innerRadius=50).encode(
            theta='sessions:Q',
            color='device_category:N',
            tooltip=['device_category', 'sessions', 'percentage']
        )
        st.altair_chart(chart_device, use_container_width=True)

        top_device = df_device.loc[df_device['sessions'].idxmax()]
        st.write(f"📱 Most users are on **{top_device['device_category']}** ({top_device['percentage']:.1f}%).")
    else:
        st.warning("No device data available.")

# -------------------------------
# Tab 5: Browser
# -------------------------------
with tab5:
    df_browser = get_data_from_bigquery(query_browser_file, start_date, end_date)
    if not df_browser.empty:
        df_browser['sessions'] = df_browser['sessions'].fillna(0).astype(int)
        df_browser['percentage'] = (df_browser['sessions'] / df_browser['sessions'].sum()) * 100

        chart_browser = alt.Chart(df_browser).mark_bar().encode(
            x='sessions:Q',
            y=alt.Y('browser:N', sort='-x'),
            color='browser:N',
            tooltip=['browser', 'sessions', 'percentage']
        )
        st.altair_chart(chart_browser, use_container_width=True)
        st.subheader("📋 Browser Data")
        st.dataframe(df_browser)

        top_browser = df_browser.loc[df_browser['sessions'].idxmax()]
        st.write(f"🌐 Most visitors use **{top_browser['browser']}** ({top_browser['percentage']:.1f}% of sessions).")
    else:
        st.warning("No browser data available.")

# -------------------------------
# Tab 6: Traffic Sources
# -------------------------------
with tab6:
    df_traffic = get_data_from_bigquery(query_traffic_file, start_date, end_date)
    if not df_traffic.empty:
        df_traffic = df_traffic.rename(columns={'session_count': 'sessions'})
        df_traffic['sessions'] = df_traffic['sessions'].fillna(0).astype(int)
        df_traffic['percentage'] = (df_traffic['sessions'] / df_traffic['sessions'].sum()) * 100

        chart_traffic = alt.Chart(df_traffic).mark_bar().encode(
            x='sessions:Q',
            y=alt.Y('source:N', sort='-x'),
            color='source:N',
            tooltip=['source', 'sessions', 'percentage']
        )
        st.altair_chart(chart_traffic, use_container_width=True)
        st.subheader("📋 Traffic Sources Data")
        st.dataframe(df_traffic)

        top_source = df_traffic.loc[df_traffic['sessions'].idxmax()]
        st.write(f"🚀 Most traffic comes from **{top_source['source']}** with {top_source['sessions']} sessions.")
    else:
        st.warning("No traffic source data available.")

# -------------------------------
# Tab 7: User Segments
# -------------------------------
with tab7:
    df_clusters = get_data_from_bigquery(query_user_clusters_file, start_date, end_date)
    if not df_clusters.empty:
        st.subheader("📊 User Segmentation")
        st.dataframe(df_clusters)

        chart_clusters = alt.Chart(df_clusters).mark_arc(innerRadius=80).encode(
            theta=alt.Theta(field='users', type='quantitative'),
            color=alt.Color(field='cluster_name', type='nominal', legend=alt.Legend(title="User Segment")),
            tooltip=[
                alt.Tooltip('cluster_name:N', title='Segment'),
                alt.Tooltip('users:Q', title='Users'),
                alt.Tooltip('pct_users:Q', title='Percentage', format='.2f')
            ]
        ).properties(title="User Segments Distribution", width=700, height=400)

        st.altair_chart(chart_clusters, use_container_width=True)

        top_cluster = df_clusters.loc[df_clusters['users'].idxmax()]
        st.write(f"🚀 Largest segment: **{top_cluster['cluster_name']}** with {top_cluster['users']} users ({top_cluster['pct_users']}%).")
    else:
        st.warning("No user segment data available for the selected date range.")

# -------------------------------
# Tab 8: Bounce Prediction
# -------------------------------
with tab8:
    df_bounce = get_data_from_bigquery(query_bounce_file, start_date, end_date)
    if not df_bounce.empty:
        if 'bounce_prediction' in df_bounce.columns:
            df_bounce = df_bounce.rename(columns={'bounce_prediction': 'predicted_is_bounce'})
        df_bounce = df_bounce.dropna(subset=['predicted_is_bounce'])

        chart_bounce = alt.Chart(df_bounce).mark_bar().encode(
            x=alt.X('predicted_is_bounce:N', title='Bounce Prediction'),
            y=alt.Y('count()', title='Number of Sessions'),
            color='predicted_is_bounce:N'
        ).properties(title='Bounce Prediction Distribution')
        st.altair_chart(chart_bounce, use_container_width=True)

        bounce_count = (df_bounce['predicted_is_bounce'] == 1).sum()
        st.write(f"🔮 About **{bounce_count} sessions** are predicted to bounce soon.")

        st.subheader("Top Sessions Likely to Bounce")
        if 'predicted_is_bounce' in df_bounce.columns:
            df_top_bounce = df_bounce.sort_values(by='predicted_is_bounce', ascending=False).head(10)
            st.dataframe(df_top_bounce)
        else:
            st.warning("Bounce prediction column not found.")
    else:
        st.warning("No bounce prediction data available.")