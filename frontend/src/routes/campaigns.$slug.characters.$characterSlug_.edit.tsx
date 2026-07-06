import { createFileRoute } from "@tanstack/react-router";
import { CharacterEditPage } from "@/pages/character-edit-page";

export const Route = createFileRoute("/campaigns/$slug/characters/$characterSlug_/edit")({
  component: CharacterEditPage,
});
