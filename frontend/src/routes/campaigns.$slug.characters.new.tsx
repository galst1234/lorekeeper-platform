import { createFileRoute } from "@tanstack/react-router";
import { CharacterNewPage } from "@/pages/character-new-page";

export const Route = createFileRoute("/campaigns/$slug/characters/new")({
  component: CharacterNewPage,
});
