-- Supply-Side User Activity Summary
-- Target: AliCloud RDS MySQL — codatta-test.rwlb.singapore.rds.aliyuncs.com:3306
-- Database: cfp_user
-- Tables: cfp_customer_user, cfp_customer_user_account, cfp_user_qualification, cfp_login_log
-- Last run: 2026-03-27

-- ============================================================
-- 1) Login activity windows + KYC status
-- ============================================================
SELECT
  count(DISTINCT u.user_id)                     AS total_users,

  count(DISTINCT CASE
    WHEN l7.user_id IS NOT NULL THEN u.user_id
  END)                                           AS login_7d,

  count(DISTINCT CASE
    WHEN l30.user_id IS NOT NULL THEN u.user_id
  END)                                           AS login_30d,

  count(DISTINCT CASE
    WHEN l90.user_id IS NOT NULL THEN u.user_id
  END)                                           AS login_90d,

  count(DISTINCT CASE
    WHEN l180.user_id IS NOT NULL THEN u.user_id
  END)                                           AS login_180d,

  count(DISTINCT CASE
    WHEN q.user_id IS NOT NULL
     AND JSON_UNQUOTE(JSON_EXTRACT(q.content, '$.education_background.audit_status')) = 'VERIFIED'
    THEN u.user_id
  END)                                           AS kyc_verified

FROM cfp_customer_user u

LEFT JOIN (
  SELECT DISTINCT user_id FROM cfp_login_log
  WHERE deleted = 0 AND gmt_create >= DATE_SUB(NOW(), INTERVAL 7 DAY)
) l7 ON l7.user_id = u.user_id

LEFT JOIN (
  SELECT DISTINCT user_id FROM cfp_login_log
  WHERE deleted = 0 AND gmt_create >= DATE_SUB(NOW(), INTERVAL 30 DAY)
) l30 ON l30.user_id = u.user_id

LEFT JOIN (
  SELECT DISTINCT user_id FROM cfp_login_log
  WHERE deleted = 0 AND gmt_create >= DATE_SUB(NOW(), INTERVAL 90 DAY)
) l90 ON l90.user_id = u.user_id

LEFT JOIN (
  SELECT DISTINCT user_id FROM cfp_login_log
  WHERE deleted = 0 AND gmt_create >= DATE_SUB(NOW(), INTERVAL 180 DAY)
) l180 ON l180.user_id = u.user_id

LEFT JOIN cfp_user_qualification q
  ON q.user_id = u.user_id AND q.deleted = 0

WHERE u.status = 'NORMAL' AND u.deleted = 0;


-- ============================================================
-- 2) Account type breakdown (wallet / email / KYC cross-tab)
-- ============================================================
SELECT
  CASE WHEN wa.user_id IS NOT NULL THEN 'yes' ELSE 'no' END   AS has_wallet,
  CASE WHEN ea.user_id IS NOT NULL THEN 'yes' ELSE 'no' END   AS has_email,
  CASE
    WHEN q.user_id IS NOT NULL
     AND JSON_UNQUOTE(JSON_EXTRACT(q.content, '$.education_background.audit_status')) = 'VERIFIED'
    THEN 'yes' ELSE 'no'
  END                                                           AS kyc_verified,
  count(DISTINCT u.user_id)                                     AS user_count

FROM cfp_customer_user u

LEFT JOIN (
  SELECT DISTINCT user_id
  FROM cfp_customer_user_account
  WHERE account_type = 'block_chain' AND deleted = 0
) wa ON wa.user_id = u.user_id

LEFT JOIN (
  SELECT DISTINCT user_id
  FROM cfp_customer_user_account
  WHERE account_type = 'email' AND deleted = 0
) ea ON ea.user_id = u.user_id

LEFT JOIN cfp_user_qualification q
  ON q.user_id = u.user_id AND q.deleted = 0

WHERE u.status = 'NORMAL' AND u.deleted = 0
GROUP BY has_wallet, has_email, kyc_verified
ORDER BY user_count DESC;
