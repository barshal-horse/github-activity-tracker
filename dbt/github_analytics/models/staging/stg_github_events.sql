-- stg_github_events.sql
-- Staging model: clean and type-cast raw GitHub events

{{ config(
    materialized='view'
) }}

SELECT
    event_id,
    event_type,
    CAST(created_at AS TIMESTAMP) AS created_at,
    DATE(CAST(created_at AS TIMESTAMP)) AS event_date,
    EXTRACT(HOUR FROM CAST(created_at AS TIMESTAMP)) AS event_hour,

    -- Actor
    CAST(actor_id AS INT64) AS actor_id,
    actor_login,
    actor_display_login,

    -- Repository
    CAST(repo_id AS INT64) AS repo_id,
    repo_name,

    -- Organization
    CAST(org_id AS INT64) AS org_id,
    org_login,

    -- Derived fields
    SPLIT(repo_name, '/')[SAFE_OFFSET(0)] AS repo_owner,
    SPLIT(repo_name, '/')[SAFE_OFFSET(1)] AS repo_short_name

FROM {{ source('github_raw', 'external_github_events') }}

-- Filter out bot accounts
WHERE actor_login NOT LIKE '%[bot]%'
  AND actor_login NOT LIKE '%bot'
  AND event_id IS NOT NULL
