WITH features_with_date AS (
  SELECT f.*, e.event_date
  FROM `analytics_453034732.user_features` AS f
  JOIN `analytics_453034732.events_*` AS e
  USING(user_pseudo_id)
  WHERE PARSE_DATE('%Y%m%d', e.event_date) BETWEEN {start_date} AND {end_date}
),

preds AS (
  SELECT 
    user_pseudo_id, 
    centroid_id
  FROM ML.PREDICT(
    MODEL `analytics_453034732.user_segmentation_model`,
    TABLE features_with_date  -- ✅ Use TABLE keyword here
  )
),

agg AS (
  SELECT 
    centroid_id,
    COUNT(DISTINCT user_pseudo_id) AS users
  FROM preds
  GROUP BY centroid_id
)

SELECT
  CASE centroid_id
    WHEN 0 THEN 'Explorers'
    WHEN 1 THEN 'Learners'
    WHEN 2 THEN 'Inactive Users'
    ELSE 'Occasional Visitors'
  END AS cluster_name,
  users,
  ROUND(users * 100.0 / SUM(users) OVER(), 2) AS pct_users
FROM agg
ORDER BY users DESC;