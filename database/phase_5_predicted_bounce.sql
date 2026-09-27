SELECT
    session_id,
    predicted_is_bounce AS bounce_prediction,
    predicted_is_bounce_probs[OFFSET(1)].prob AS bounce_probability,
    device_category,
    browser,
    source,
    medium,
    pages_per_session,
    session_duration,
    is_bounce
FROM ML.PREDICT(
    MODEL `analytics_453034732.bounce_prediction_model`,
    TABLE `analytics_453034732.session_features`
)
ORDER BY bounce_probability DESC
LIMIT 1000;