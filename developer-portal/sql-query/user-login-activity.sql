-- User Login Activity Summary
-- Counts users with at least 1 login in 7d, 30d, 90d windows + total users
-- Source: auth.users.last_sign_in_at (Supabase Auth)
-- Run against: Supabase project uxafdddzhgdhsabkwmgw

SELECT
  count(*)
    AS total_users,
  count(*) FILTER (WHERE last_sign_in_at >= now() - interval '7 days')
    AS login_7d,
  count(*) FILTER (WHERE last_sign_in_at >= now() - interval '30 days')
    AS login_30d,
  count(*) FILTER (WHERE last_sign_in_at >= now() - interval '90 days')
    AS login_90d
FROM auth.users
WHERE deleted_at IS NULL;
