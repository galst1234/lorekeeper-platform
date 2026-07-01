import { createFileRoute } from "@tanstack/react-router";
import { CharactersSection } from "@/components/campaign/characters-section";

export const Route = createFileRoute("/campaigns/$slug/characters/")({
  component: CharactersPage,
});

function CharactersPage() {
  const { slug } = Route.useParams();

  return (
    <div className="max-w-4xl mx-auto px-6 py-8 space-y-8">
      <CharactersSection slug={slug} characterType="pc" />
      <CharactersSection slug={slug} characterType="npc" />
    </div>
  );
}
