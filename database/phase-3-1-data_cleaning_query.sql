/*
This query cleans and aggregates raw GA4 event data for dashboard visualization.
It's designed to be a template you can use to pull key metrics like:

Total Sessions

Unique Visitors

Event Counts (like page views)
*/

-- Use a Common Table Expression (CTE) to select the raw data and extract key parameters.
WITH RawEvents AS (
  SELECT
    user_pseudo_id,
    TIMESTAMP_MICROS(event_timestamp) AS event_datetime,
    event_name,
    (SELECT value.string_value FROM UNNEST(event_params) WHERE key = 'page_location') AS page_location,
    (SELECT value.string_value FROM UNNEST(event_params) WHERE key = 'page_title') AS page_title,
    (SELECT value.int_value FROM UNNEST(event_params) WHERE key = 'ga_session_id') AS ga_session_id
  FROM
    `brilliant-dryad-439810-q6.analytics_453034732.events_*`
  WHERE
    _TABLE_SUFFIX BETWEEN FORMAT_DATE('%Y%m%d', DATE_SUB(CURRENT_DATE(), INTERVAL 30 DAY))
                     AND FORMAT_DATE('%Y%m%d', CURRENT_DATE())
    AND event_name NOT IN ('scroll', 'user_engagement', 'session_start', 'first_visit')
)

SELECT
  DATE(event_datetime) AS event_date,
  event_name,
  COUNT(*) AS event_count,
  COUNT(DISTINCT user_pseudo_id) AS user_count,
  COUNT(DISTINCT ga_session_id) AS session_count
FROM
  RawEvents
GROUP BY
  event_date, event_name
ORDER BY
  event_date DESC, event_count DESC LIMIT 5;