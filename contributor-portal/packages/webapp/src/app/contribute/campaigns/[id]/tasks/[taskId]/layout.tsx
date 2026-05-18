export default function WorkspaceLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  // Full-screen layout — no sidebar, no topbar
  return <>{children}</>;
}
