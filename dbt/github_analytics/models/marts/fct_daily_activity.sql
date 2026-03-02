-- fct_daily_activity.sql
-- Daily aggregation of GitHub events by type

{{ config(
    materialized='table',
    partition_by={
        "field": "event_date",
        "data_type": "date",
        "granularity": "day"
    }
) }}

SELECT
    event_date,
    event_type,
    COUNT(*) AS event_count,
    COUNT(DISTINCT actor_login) AS unique_actors,
    COUNT(DISTINCT repo_name) AS unique_repos

FROM {{ ref('stg_github_events') }}

GROUP BY event_date, event_type
ORDER BY event_date, event_count DESC
