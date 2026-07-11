import { createFileRoute } from "@tanstack/react-router";
import { ChroniclePage } from "@/pages/chronicle-page";

export const Route = createFileRoute("/campaigns/$slug/chronicle/")({
  validateSearch: (search: Record<string, unknown>): { q?: string } => ({
    ...(typeof search.q === "string" && search.q.trim() !== "" ? { q: search.q } : {}),
  }),
  component: ChroniclePage,
});
