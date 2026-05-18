-- Supply-Side User Signup Channel Breakdown
-- Target: AliCloud RDS MySQL (prod) — cfp_user
-- Last run: 2026-03-27

-- 1) Users by signup channel + device
SELECT
  COALESCE(JSON_UNQUOTE(JSON_EXTRACT(source, '$.channel')), 'null') AS channel,
  JSON_UNQUOTE(JSON_EXTRACT(source, '$.device')) AS device,
  count(*) AS user_count
FROM cfp_customer_user
WHERE status = 'NORMAL' AND deleted = 0 AND source IS NOT NULL
GROUP BY channel, device
ORDER BY user_count DESC;

-- 2) Users by wallet connector type
SELECT
  connector,
  count(DISTINCT user_id) AS user_count
FROM cfp_customer_user_account
WHERE deleted = 0
GROUP BY connector
ORDER BY user_count DESC;
