-- KPIs for website overview
-- This query aggregates key website performance metrics,
-- including sessions, page views, engagement, and conversions,
-- for the specified date range.

WITH session_durations AS (
SELECT
session_id,
TIMESTAMP_DIFF(MAX(event_datetime), MIN(event_datetime), SECOND) AS session_duration,
COUNTIF(event_name = 'page_view') AS page_views_per_session,
-- A bounce is a session with only one page view.
CASE WHEN COUNTIF(event_name = 'page_view') = 1 THEN 1 ELSE 0 END AS is_bounce
FROM
analytics_453034732.cleaned_events
WHERE
DATE(event_datetime) BETWEEN {start_date} AND {end_date}
GROUP BY
session_id
)

SELECT
COUNT(DISTINCT e.session_id) AS total_sessions,
SUM(s.page_views_per_session) AS total_page_views,
AVG(s.session_duration) AS avg_session_duration,
-- Engagement rate is the inverse of the bounce rate.
1 - AVG(s.is_bounce) AS avg_engagement_rate,
AVG(s.is_bounce) AS avg_bounce_rate,
COUNT(DISTINCT e.user_pseudo_id) AS unique_visitors,
COUNTIF(e.event_name = 'conversion') AS total_conversions
FROM
analytics_453034732.cleaned_events e
LEFT JOIN
session_durations s ON e.session_id = s.session_id
WHERE
DATE(e.event_datetime) BETWEEN {start_date} AND {end_date};