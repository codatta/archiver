// Shared mock task instances — used by the tasks page grid and by the
// in-workspace instance switcher drawer. Shape matches `task_instances`
// table (id, campaign_id, task_id, status, priority, pay, duration).

export type MockTaskInstance = {
  id: string;
  campaignId: string;
  campaign: string;
  type: "supply" | "labeling" | "validation";
  desc: string;
  time: string;
  pay: string;
  taskId: string;
  priority?: "resume" | "expiring" | "dispute";
};

export const MOCK_TASK_INSTANCES: MockTaskInstance[] = [
  // Resume (in progress)
  { id: "#inst-47", campaignId: "camp-k1m", campaign: "Kitchen Manipulation", type: "labeling", desc: "Review 12 clips from kitchen demo", time: "~45 min", pay: "$1.50", taskId: "t3-label-47", priority: "resume" },
  { id: "#inst-91", campaignId: "camp-rmnd", campaign: "RoboMIND Trajectories", type: "labeling", desc: "Classify task type for trajectory", time: "~30 min", pay: "royalty", taskId: "t2-label-91", priority: "resume" },
  { id: "#inst-33", campaignId: "camp-xp10", campaign: "Egocentric Experience", type: "supply", desc: "Record 15-min daily activity", time: "~20 min", pay: "$1.00", taskId: "t1-supply-33", priority: "resume" },
  // Expiring
  { id: "#inst-201", campaignId: "camp-bone", campaign: "Humanoid Motion", type: "labeling", desc: "Write motion description", time: "~20 min", pay: "bounty", taskId: "t3-label-201", priority: "expiring" },
  { id: "#inst-202", campaignId: "camp-bone", campaign: "Humanoid Motion", type: "labeling", desc: "Temporal segmentation", time: "~25 min", pay: "bounty", taskId: "t4-label-202", priority: "expiring" },
  { id: "#inst-203", campaignId: "camp-bone", campaign: "Humanoid Motion", type: "supply", desc: "Upload mocap recording", time: "~15 min", pay: "bounty", taskId: "t1-supply-203", priority: "expiring" },
  { id: "#inst-204", campaignId: "camp-k1m", campaign: "Kitchen Manipulation", type: "labeling", desc: "Add language instructions", time: "~30 min", pay: "$1.50", taskId: "t3-label-204", priority: "expiring" },
  { id: "#inst-205", campaignId: "camp-k1m", campaign: "Kitchen Manipulation", type: "supply", desc: "Upload kitchen task video", time: "~15 min", pay: "$2.50", taskId: "t1-supply-205", priority: "expiring" },
  // Dispute
  { id: "#inst-88", campaignId: "camp-k1m", campaign: "Kitchen Manipulation", type: "labeling", desc: "Disputed grade — respond to reviewer feedback", time: "~10 min", pay: "$1.50", taskId: "t3-dispute-88", priority: "dispute" },
  { id: "#inst-89", campaignId: "camp-rmnd", campaign: "RoboMIND Trajectories", type: "validation", desc: "Disputed validation — reviewer disagrees", time: "~15 min", pay: "royalty", taskId: "t3-dispute-89", priority: "dispute" },
  // Kitchen Manipulation — 5 available
  { id: "#inst-55", campaignId: "camp-k1m", campaign: "Kitchen Manipulation", type: "supply", desc: "Upload kitchen task video", time: "~15 min", pay: "$2.50", taskId: "t1-supply-55" },
  { id: "#inst-56", campaignId: "camp-k1m", campaign: "Kitchen Manipulation", type: "supply", desc: "Upload kitchen task video", time: "~15 min", pay: "$2.50", taskId: "t1-supply-56" },
  { id: "#inst-48", campaignId: "camp-k1m", campaign: "Kitchen Manipulation", type: "labeling", desc: "Annotate action segments", time: "~45 min", pay: "$1.50", taskId: "t3-label-48" },
  { id: "#inst-49", campaignId: "camp-k1m", campaign: "Kitchen Manipulation", type: "labeling", desc: "Review bounding boxes", time: "~40 min", pay: "$1.50", taskId: "t3-label-49" },
  { id: "#inst-50", campaignId: "camp-k1m", campaign: "Kitchen Manipulation", type: "labeling", desc: "Add language instructions", time: "~30 min", pay: "$1.50", taskId: "t3-label-50" },
  // RoboMIND — 4 available
  { id: "#inst-301", campaignId: "camp-rmnd", campaign: "RoboMIND Trajectories", type: "supply", desc: "Record humanoid demo", time: "~20 min", pay: "royalty", taskId: "t1-supply-301" },
  { id: "#inst-302", campaignId: "camp-rmnd", campaign: "RoboMIND Trajectories", type: "labeling", desc: "Classify task type", time: "~30 min", pay: "royalty", taskId: "t2-label-302" },
  { id: "#inst-303", campaignId: "camp-rmnd", campaign: "RoboMIND Trajectories", type: "labeling", desc: "Tag object classes", time: "~25 min", pay: "royalty", taskId: "t2-label-303" },
  { id: "#inst-304", campaignId: "camp-rmnd", campaign: "RoboMIND Trajectories", type: "validation", desc: "Verify trajectory label", time: "~15 min", pay: "royalty", taskId: "t3-val-304" },
  // Egocentric — 7 available
  { id: "#inst-401", campaignId: "camp-xp10", campaign: "Egocentric Experience", type: "supply", desc: "Record 15-min cooking activity", time: "~20 min", pay: "$1.00", taskId: "t1-supply-401" },
  { id: "#inst-402", campaignId: "camp-xp10", campaign: "Egocentric Experience", type: "supply", desc: "Record 15-min cleaning activity", time: "~20 min", pay: "$1.00", taskId: "t1-supply-402" },
  { id: "#inst-403", campaignId: "camp-xp10", campaign: "Egocentric Experience", type: "labeling", desc: "Hierarchical language annotation", time: "~35 min", pay: "$0.50", taskId: "t3-label-403" },
  { id: "#inst-404", campaignId: "camp-xp10", campaign: "Egocentric Experience", type: "labeling", desc: "Temporal segmentation boundaries", time: "~30 min", pay: "$0.75", taskId: "t4-label-404" },
  { id: "#inst-405", campaignId: "camp-xp10", campaign: "Egocentric Experience", type: "labeling", desc: "Activity segment annotation", time: "~25 min", pay: "$0.50", taskId: "t3-label-405" },
  { id: "#inst-406", campaignId: "camp-xp10", campaign: "Egocentric Experience", type: "validation", desc: "Verify language descriptions", time: "~15 min", pay: "$0.25", taskId: "t5-val-406" },
  { id: "#inst-407", campaignId: "camp-xp10", campaign: "Egocentric Experience", type: "validation", desc: "Check segment boundaries", time: "~15 min", pay: "$0.25", taskId: "t5-val-407" },
];

// Each task type enters the workspace pipeline at a different step.
// Keep in sync with the same map in contribute/tasks/page.tsx.
export const TYPE_TO_STEP: Record<MockTaskInstance["type"], "supply" | "review" | "annotate" | "export"> = {
  supply: "supply",
  labeling: "review",
  validation: "review",
};

export function workspaceHrefFor(inst: MockTaskInstance): string {
  return `/workspace/${inst.campaignId}/${inst.taskId}/${TYPE_TO_STEP[inst.type]}`;
}
