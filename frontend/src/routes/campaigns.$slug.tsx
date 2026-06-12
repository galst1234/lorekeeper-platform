import { createFileRoute } from "@tanstack/react-router";

export const Route = createFileRoute("/campaigns/$slug")({
  component: () => <div>Campaign Detail (Task 11)</div>,
});
