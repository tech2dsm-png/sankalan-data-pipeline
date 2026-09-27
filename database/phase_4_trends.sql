-- Daily traffic trends
-- This query aggregates daily sessions, page views, and new users to
-- show how website traffic changes over time.

SELECT
-- We extract the date from the event_datetime column.
DATE(event_datetime) AS event_date,
COUNT(DISTINCT session_id) AS daily_sessions,
COUNT(DISTINCT user_pseudo_id) AS daily_users,
COUNTIF(event_name = 'page_view') AS daily_page_views
FROM
analytics_453034732.cleaned_events
WHERE
-- The date filter ensures we only query a specific range.
DATE(event_datetime) BETWEEN {start_date} AND {end_date}
GROUP BY
event_date
ORDER BY
event_date;