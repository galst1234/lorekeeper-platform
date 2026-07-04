import { createFileRoute } from "@tanstack/react-router";
import { ChroniclePage } from "@/pages/chronicle-page";

export const Route = createFileRoute("/campaigns/$slug/chronicle/")({
  component: ChroniclePage,
});
