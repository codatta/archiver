// Matches public.delivery_items
export type DeliveryItem = {
  id: string;
  delivery_id: string | null;
  vertical_id: string;
  topic_id: string | null;
  payload: Record<string, unknown>;
  quality_score: number;
  quality_method: string;
  validator_count: number;
  consensus_ratio: number;
  unit_price_usd: number;
  task_id: string | null;
  cf_id: string | null;
  created_at: string;
  org_id?: string;
  environment?: string;
  underfunded?: boolean;
};

// Keep the frontend-friendly alias
export type AnnotationItem = DeliveryItem & {
  // Frontend-enriched fields (joined from verticals/topics)
  vertical_slug?: string;
  vertical_name?: string;
  topic_name?: string;
  status?: "pending" | "adopted" | "disputed" | "refunded" | "accepted" | "rejected";
};

export type OrgRole = "owner" | "admin" | "member";
export type ApiKeyStatus = "active" | "expired" | "revoked";
export type SubscriptionStatus = "active" | "paused" | "cancelled";
export type DeliveryMode = "pull" | "push";
export type DeliveryStatus = "pending" | "accepted" | "rejected";
export type ChargeStatus = "frozen" | "settled" | "refunded";
export type TransactionType = "topup" | "freeze" | "settle" | "refund";

// Live data (AliCloud RDS MySQL)
export type FrontierStatus = "ONLINE" | "PREPARING" | "OFFLINE" | "PAUSED";

export type FrontierSummary = {
  frontier_id: string;
  title: string;
  status: FrontierStatus;
  task_count: number;
  total_submissions: number;
};

export type TaskSummary = {
  task_id: string;
  frontier_id: string;
  name: string;
  task_type: string;
  status: string;
  submission_count: number;
};

export type LiveSubmission = {
  submission_id: string;
  task_id: string;
  frontier_id: string;
  data: Record<string, unknown>;
  quality_score: number;
  quality_grade: string;
  source: string;
  created_at: string;
  consumer_feedback: "adopt" | "dispute" | null;
};
