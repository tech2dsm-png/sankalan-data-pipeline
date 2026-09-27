CREATE OR REPLACE TABLE `brilliant-dryad-439810-q6.analytics_453034732.cleaned_events` AS
SELECT
  event_timestamp,
  TIMESTAMP_MICROS(event_timestamp) AS event_datetime,
  event_name,
  user_pseudo_id,
  (SELECT value.int_value FROM UNNEST(event_params) WHERE key = 'ga_session_id') AS session_id,
  (SELECT value.string_value FROM UNNEST(event_params) WHERE key = 'page_location') AS page_url,
  (SELECT value.string_value FROM UNNEST(event_params) WHERE key = 'page_title') AS page_title,
  (SELECT value.string_value FROM UNNEST(event_params) WHERE key = 'browser') AS browser,
  (SELECT value.string_value FROM UNNEST(event_params) WHERE key = 'device_category') AS device_category,
  (SELECT value.string_value FROM UNNEST(event_params) WHERE key = 'source') AS source
FROM
  `brilliant-dryad-439810-q6.analytics_453034732.events_*`
WHERE
  _TABLE_SUFFIX BETWEEN FORMAT_DATE('%Y%m%d', DATE_SUB(CURRENT_DATE(), INTERVAL 30 DAY))
  AND FORMAT_DATE('%Y%m%d', CURRENT_DATE());