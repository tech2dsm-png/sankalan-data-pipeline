-- Browser breakdown with date filter
SELECT
    browser,
    COUNT(DISTINCT session_id) AS sessions,
    COUNTIF(event_name='page_view') AS page_views
FROM analytics_453034732.cleaned_events
WHERE event_datetime BETWEEN TIMESTAMP({start_date}) AND TIMESTAMP({end_date})
GROUP BY browser
ORDER BY sessions DESC;