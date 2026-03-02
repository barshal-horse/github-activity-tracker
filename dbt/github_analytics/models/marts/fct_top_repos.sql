-- fct_top_repos.sql
-- Top repositories ranked by total activity

{{ config(
    materialized='table',
    cluster_by=['event_type']
) }}

WITH repo_activity AS (
    SELECT
        repo_name,
        repo_owner,
        repo_short_name,
        event_type,
        COUNT(*) AS event_count,
        COUNT(DISTINCT actor_login) AS unique_contributors,
        MIN(event_date) AS first_seen,
        MAX(event_date) AS last_seen
    FROM {{ ref('stg_github_events') }}
    GROUP BY repo_name, repo_owner, repo_short_name, event_type
),

repo_totals AS (
    SELECT
        repo_name,
        repo_owner,
        repo_short_name,
        SUM(event_count) AS total_events,
        SUM(unique_contributors) AS total_contributors,
        MIN(first_seen) AS first_activity,
        MAX(last_seen) AS last_activity,

        -- Event type breakdowns
        SUM(CASE WHEN event_type = 'PushEvent' THEN event_count ELSE 0 END) AS push_count,
        SUM(CASE WHEN event_type = 'WatchEvent' THEN event_count ELSE 0 END) AS star_count,
        SUM(CASE WHEN event_type = 'ForkEvent' THEN event_count ELSE 0 END) AS fork_count,
        SUM(CASE WHEN event_type = 'PullRequestEvent' THEN event_count ELSE 0 END) AS pr_count,
        SUM(CASE WHEN event_type = 'IssuesEvent' THEN event_count ELSE 0 END) AS issue_count

    FROM repo_activity
    GROUP BY repo_name, repo_owner, repo_short_name
)

SELECT
    *,
    ROW_NUMBER() OVER (ORDER BY total_events DESC) AS activity_rank

FROM repo_totals
ORDER BY total_events DESC
LIMIT 1000
