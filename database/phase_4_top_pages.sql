-- Top performing pages
SELECT 
  page_url,
  COUNT(*) AS page_views,
  COUNT(DISTINCT session_id) AS sessions,
  COUNT(DISTINCT user_pseudo_id) AS unique_users
FROM
  `brilliant-dryad-439810-q6.analytics_453034732.cleaned_events`
WHERE
  event_name = 'page_view'
  AND page_url IS NOT NULL
GROUP BY
  page_url
ORDER BY
  page_views DESC
LIMIT 20;