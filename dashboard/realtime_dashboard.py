"""
Sankalan Real-Time Analytics Dashboard
Streamlit Dashboard for Real-Time Website Analytics
"""

import streamlit as st
import pandas as pd
import psycopg2
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import time

# Page Configuration
st.set_page_config(
    page_title="Sankalan Real-Time Analytics",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for Professional Styling
st.markdown(
    """
    <style>
        .main { background-color: #f8f9fa; }
        .stMetric { background-color: #ffffff; padding: 15px; border-radius: 8px; box-shadow: 0 1px 3px rgba(0,0,0,0.1); }
    </style>
    """,
    unsafe_allow_html=True
)

# ============================================================
# DATABASE CONNECTION
# ============================================================


def get_connection():
    """Create and return a database connection"""
    try:
        conn = psycopg2.connect(
            host="localhost",
            database="analytics",
            user="sankalan",
            password="sankalan123",
            port="5432"
        )
        return conn
    except Exception as e:
        st.error(f"Failed to connect to database: {e}")
        st.info("Make sure PostgreSQL is running: docker-compose up -d")
        return None

# ============================================================
# DATA FETCHING FUNCTIONS (SAFE FOR EXISTING SCHEMA)
# ============================================================

@st.cache_data(ttl=10)
def fetch_kpi_metrics():
    """Fetch real-time GA4-style and operational KPI metrics safely"""
    conn = get_connection()
    if conn is None:
        return None
    
    try:
        with conn.cursor() as cur:
            # Active sessions (last 5 minutes)
            cur.execute("""
                SELECT COUNT(DISTINCT session_id) 
                FROM fact_page_views
                WHERE event_timestamp > NOW() - INTERVAL '5 minutes'
            """)
            active_sessions = cur.fetchone()[0] or 0
            
            # Events in last 5 minutes
            cur.execute("""
                SELECT COUNT(*) 
                FROM fact_page_views
                WHERE event_timestamp > NOW() - INTERVAL '5 minutes'
            """)
            events_5min = cur.fetchone()[0] or 0
            
            # Events in last minute
            cur.execute("""
                SELECT COUNT(*) 
                FROM fact_page_views
                WHERE event_timestamp > NOW() - INTERVAL '1 minute'
            """)
            events_1min = cur.fetchone()[0] or 0
            
            # Active users (last 15 minutes)
            cur.execute("""
                SELECT COUNT(DISTINCT user_id) 
                FROM fact_page_views
                WHERE event_timestamp > NOW() - INTERVAL '15 minutes'
            """)
            active_users = cur.fetchone()[0] or 0
            
            # Total events lifetime
            cur.execute("SELECT COUNT(*) FROM fact_page_views")
            total_events = cur.fetchone()[0] or 0
            
            # Bounce rate (last 15 minutes)
            cur.execute("""
                SELECT 
                    COUNT(DISTINCT CASE WHEN is_bounce = TRUE THEN session_id END) * 100.0 / 
                    NULLIF(COUNT(DISTINCT session_id), 0) as bounce_rate
                FROM fact_page_views
                WHERE event_timestamp > NOW() - INTERVAL '15 minutes'
            """)
            bounce_rate = cur.fetchone()[0] or 0
            
            # Conversion rate (last hour)
            cur.execute("""
                SELECT 
                    COUNT(CASE WHEN is_conversion = TRUE THEN 1 END) * 100.0 / 
                    NULLIF(COUNT(*), 0) as conversion_rate
                FROM fact_page_views
                WHERE event_timestamp > NOW() - INTERVAL '1 hour'
            """)
            conversion_rate = cur.fetchone()[0] or 0

            # Engagement Rate (Sessions with multiple events or conversions in last 15 mins)
            cur.execute("""
                SELECT 
                    COUNT(DISTINCT CASE WHEN event_cnt > 1 OR has_conv = 1 THEN session_id END) * 100.0 /
                    NULLIF(COUNT(DISTINCT session_id), 0) as engagement_rate
                FROM (
                    SELECT session_id, COUNT(*) as event_cnt, MAX(CASE WHEN is_conversion = TRUE THEN 1 ELSE 0 END) as has_conv
                    FROM fact_page_views
                    WHERE event_timestamp > NOW() - INTERVAL '15 minutes'
                    GROUP BY session_id
                ) sub
            """)
            res = cur.fetchone()
            engagement_rate = res[0] if res and res[0] is not None else 0.0

            # New Real-Time KPI: Peak Events Per Minute (last hour)
            cur.execute("""
                SELECT COALESCE(MAX(minute_count), 0) FROM (
                    SELECT COUNT(*) as minute_count
                    FROM fact_page_views
                    WHERE event_timestamp > NOW() - INTERVAL '1 hour'
                    GROUP BY DATE_TRUNC('minute', event_timestamp)
                ) sub
            """)
            peak_events_min = cur.fetchone()[0] or 0

        return {
            'active_sessions': active_sessions,
            'events_5min': events_5min,
            'events_1min': events_1min,
            'active_users': active_users,
            'total_events': total_events,
            'bounce_rate': bounce_rate,
            'conversion_rate': conversion_rate,
            'engagement_rate': engagement_rate,
            'peak_events_min': peak_events_min
        }
    except Exception as e:
        st.error(f"Error fetching KPI: {e}")
        return None
    finally:
        if conn:
            conn.close()

@st.cache_data(ttl=10)
def fetch_event_timeline():
    """Fetch event timeline for chart"""
    conn = get_connection()
    if conn is None:
        return None
    
    try:
        df = pd.read_sql_query("""
            SELECT 
                DATE_TRUNC('minute', event_timestamp) as minute,
                COUNT(*) as events,
                COUNT(DISTINCT user_id) as active_users
            FROM fact_page_views
            WHERE event_timestamp > NOW() - INTERVAL '1 hour'
            GROUP BY DATE_TRUNC('minute', event_timestamp)
            ORDER BY minute ASC
        """, conn)
        return df
    except Exception as e:
        return None
    finally:
        if conn:
            conn.close()

@st.cache_data(ttl=10)
def fetch_top_pages():
    """Fetch top pages"""
    conn = get_connection()
    if conn is None:
        return None
    
    try:
        df = pd.read_sql_query("""
            SELECT 
                p.page_url,
                COUNT(*) as views
            FROM fact_page_views f
            JOIN dim_page p ON f.page_id = p.page_id
            WHERE f.event_timestamp > NOW() - INTERVAL '1 hour'
            GROUP BY p.page_url
            ORDER BY views DESC
            LIMIT 10
        """, conn)
        return df
    except Exception as e:
        return None
    finally:
        if conn:
            conn.close()

@st.cache_data(ttl=10)
def fetch_device_breakdown():
    """Fetch device breakdown"""
    conn = get_connection()
    if conn is None:
        return None
    
    try:
        df = pd.read_sql_query("""
            SELECT 
                d.device_type,
                COUNT(*) as events
            FROM fact_page_views f
            JOIN dim_device d ON f.device_id = d.device_id
            WHERE f.event_timestamp > NOW() - INTERVAL '1 hour'
            GROUP BY d.device_type
            ORDER BY events DESC
        """, conn)
        return df
    except Exception as e:
        return None
    finally:
        if conn:
            conn.close()

@st.cache_data(ttl=10)
def fetch_traffic_sources():
    """Fetch traffic source breakdown"""
    conn = get_connection()
    if conn is None:
        return None
    
    try:
        df = pd.read_sql_query("""
            SELECT 
                traffic_source,
                COUNT(*) as visits
            FROM fact_page_views
            WHERE event_timestamp > NOW() - INTERVAL '1 hour'
            AND traffic_source IS NOT NULL
            GROUP BY traffic_source
            ORDER BY visits DESC
        """, conn)
        return df
    except Exception as e:
        return None
    finally:
        if conn:
            conn.close()

@st.cache_data(ttl=10)
def fetch_recent_events():
    """Fetch recent events"""
    conn = get_connection()
    if conn is None:
        return None
    
    try:
        df = pd.read_sql_query("""
            SELECT 
                f.event_type,
                p.page_url,
                f.user_id,
                f.event_timestamp,
                f.traffic_source,
                COALESCE(f.is_conversion, FALSE) as is_conversion,
                COALESCE(f.is_bounce, FALSE) as is_bounce
            FROM fact_page_views f
            JOIN dim_page p ON f.page_id = p.page_id
            WHERE f.event_timestamp > NOW() - INTERVAL '5 minutes'
            ORDER BY f.event_timestamp DESC
            LIMIT 20
        """, conn)
        return df
    except Exception as e:
        return None
    finally:
        if conn:
            conn.close()

# ============================================================
# DASHBOARD UI
# ============================================================

st.title("Sankalan Real-Time Analytics Dashboard")
st.markdown("Live streaming website traffic telemetry and GA4-style operational metrics.")
st.caption(f"Auto-refreshes every 10 seconds | Current Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

# Sidebar Controls
with st.sidebar:
    st.header("Pipeline Controls")
    refresh_rate = st.selectbox("Refresh Rate (Seconds)", [5, 10, 15, 30, 60], index=1)
    
    if st.button("Manual Refresh", use_container_width=True):
        st.cache_data.clear()
        st.rerun()
    
    st.divider()
    st.markdown("### Architecture Flow")
    st.info("Website ➔ FastAPI ➔ Kafka ➔ Spark ➔ PostgreSQL")

# KPI Metric Banner (Enhanced Real-Time KPIs)
kpi = fetch_kpi_metrics()

if kpi:
    col1, col2, col3, col4, col5, col6, col7, col8 = st.columns(8)
    
    with col1:
        st.metric("Active Users (15m)", kpi['active_users'])
    with col2:
        st.metric("Active Sessions", kpi['active_sessions'])
    with col3:
        st.metric("Events / Min", kpi['events_1min'])
    with col4:
        st.metric("Peak Events/Min", kpi['peak_events_min'])
    with col5:
        st.metric("Engagement", f"{kpi['engagement_rate']:.1f}%")
    with col6:
        st.metric("Conversion", f"{kpi['conversion_rate']:.1f}%")
    with col7:
        st.metric("Bounce Rate", f"{kpi['bounce_rate']:.1f}%")
    with col8:
        st.metric("Total Events", f"{kpi['total_events']:,}")
else:
    st.warning("Connecting to database or awaiting live pipeline event stream...")

st.divider()

# Section 1: Real-Time Traffic Velocity & Concurrent Users Dual-Axis Chart
st.subheader("Real-Time Traffic Velocity & User Momentum")
timeline_df = fetch_event_timeline()

if timeline_df is not None and not timeline_df.empty:
    fig = px.bar(
        timeline_df,
        x='minute',
        y='events',
        title="Minute-by-Minute Event Ingestion & Active Users Stream",
        labels={'minute': 'Timeline (Minute)', 'events': 'Events Volume'},
        color_discrete_sequence=['#2b5c8f']
    )
    # Add active user trend line on secondary trace
    fig.add_trace(
        go.Scatter(
            x=timeline_df['minute'],
            y=timeline_df['active_users'],
            mode='lines+markers',
            name='Active Users',
            yaxis='y2',
            line=dict(color='#ff7f0e', width=3)
        )
    )
    fig.update_layout(
        height=380,
        margin=dict(l=20, r=20, t=40, b=20),
        yaxis=dict(title='Events Count'),
        yaxis2=dict(title='Active Users', overlaying='y', side='right', showgrid=False),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )
    st.plotly_chart(fig, use_container_width=True)
else:
    st.info("Waiting for streaming time-series metrics from Kafka/Spark...")

st.divider()

# Section 2: Content Performance & Traffic Source Mix
col1, col2 = st.columns(2)

with col1:
    st.subheader("Top Viewed Pages (Last Hour)")
    pages_df = fetch_top_pages()
    if pages_df is not None and not pages_df.empty:
        fig = px.bar(
            pages_df,
            x='views',
            y='page_url',
            orientation='h',
            title="Most Popular Live Pages",
            color='views',
            color_continuous_scale='Blues'
        )
        fig.update_layout(height=380, yaxis={'categoryorder':'total ascending'}, margin=dict(l=20, r=20, t=40, b=20))
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No page view data available.")

with col2:
    st.subheader("Traffic Acquisition Channels")
    traffic_df = fetch_traffic_sources()
    if traffic_df is not None and not traffic_df.empty:
        fig = px.pie(
            traffic_df,
            values='visits',
            names='traffic_source',
            title="Live Traffic Source Breakdown",
            hole=0.45
        )
        fig.update_layout(height=380, margin=dict(l=20, r=20, t=40, b=20))
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No traffic source data available.")

st.divider()

# Section 3: Technology Environment Breakdowns
st.subheader("Environment & Device Telemetry")
device_df = fetch_device_breakdown()
if device_df is not None and not device_df.empty:
    fig = px.bar(
        device_df,
        x='device_type',
        y='events',
        color='device_type',
        title="Real-Time Events by Device Category",
        text_auto=True
    )
    fig.update_layout(height=320, showlegend=False, margin=dict(l=20, r=20, t=40, b=20))
    st.plotly_chart(fig, use_container_width=True)
else:
    st.info("No device category data available.")

st.divider()

# Section 4: Live Event Stream Feed
st.subheader("Live Event Stream Feed (Last 5 Minutes)")
recent_df = fetch_recent_events()

if recent_df is not None and not recent_df.empty:
    for _, row in recent_df.iterrows():
        if row.get('is_conversion', False):
            badge_html = "<span style='background-color: #d4edda; color: #155724; padding: 3px 8px; border-radius: 4px; font-weight: bold;'>Conversion</span>"
        elif row.get('is_bounce', False):
            badge_html = "<span style='background-color: #e2e3e5; color: #383d41; padding: 3px 8px; border-radius: 4px; font-weight: bold;'>Bounce / Exit</span>"
        else:
            badge_html = "<span style='background-color: #cce5ff; color: #004085; padding: 3px 8px; border-radius: 4px; font-weight: bold;'>Page View</span>"
        
        cols = st.columns([1.5, 2.5, 1.5, 1.5, 2])
        with cols[0]:
            st.markdown(badge_html, unsafe_allow_html=True)
        with cols[1]:
            st.text(f"URL: {row['page_url']}")
        with cols[2]:
            st.text(f"User: {row['user_id']}")
        with cols[3]:
            st.text(f"Source: {row['traffic_source'] or 'Direct'}")
        with cols[4]:
            st.text(f"Time: {row['event_timestamp']}")
        st.divider()
else:
    st.info("No incoming real-time events recorded in the last 5 minutes.")

# Automatic Stream Refresh Loop
time.sleep(refresh_rate)
st.rerun()