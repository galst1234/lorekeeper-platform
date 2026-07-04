import { createFileRoute } from "@tanstack/react-router";
import { CharactersPage } from "@/pages/characters-page";

export const Route = createFileRoute("/campaigns/$slug/characters/")({
  component: CharactersPage,
});
