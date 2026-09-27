-- Device and browser breakdown
SELECT
    device_category,
        COUNT(DISTINCT session_id) AS sessions,
    COUNTIF(event_name='page_view') AS page_views
FROM analytics_453034732.cleaned_events
WHERE DATE(event_datetime) BETWEEN {start_date} AND {end_date}
GROUP BY device_category
ORDER BY sessions DESC;