import { redirect } from "next/navigation";

// Landing on the workspace root auto-routes to the supply step.
// In I0-4+, this will read instance status from Supabase and route to the
// appropriate step based on progress (e.g. /review if T1 already submitted).
export default async function WorkspaceRootRedirect({
  params,
}: {
  params: Promise<{ campaignId: string; taskId: string }>;
}) {
  const { campaignId, taskId } = await params;
  redirect(`/workspace/${campaignId}/${taskId}/supply`);
}
