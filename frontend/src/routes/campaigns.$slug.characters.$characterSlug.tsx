import { createFileRoute } from "@tanstack/react-router";
import { CharacterDetailPage } from "@/pages/character-detail-page";

export const Route = createFileRoute("/campaigns/$slug/characters/$characterSlug")({
  component: CharacterDetailPage,
});
