-- fct_event_distribution.sql
-- Overall distribution of event types for dashboard pie/bar chart

{{ config(
    materialized='table'
) }}

SELECT
    event_type,
    COUNT(*) AS event_count,
    COUNT(DISTINCT actor_login) AS unique_actors,
    COUNT(DISTINCT repo_name) AS unique_repos,
    ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER (), 2) AS percentage

FROM {{ ref('stg_github_events') }}

GROUP BY event_type
ORDER BY event_count DESC
