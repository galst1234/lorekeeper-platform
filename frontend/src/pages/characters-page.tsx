import { getRouteApi } from "@tanstack/react-router";
import { CharactersSection } from "@/components/character/characters-section";

const Route = getRouteApi("/campaigns/$slug/characters/");

export function CharactersPage() {
  const { slug } = Route.useParams();

  return (
    <div className="max-w-4xl mx-auto px-6 py-8 space-y-8">
      <CharactersSection slug={slug} characterType="pc" />
      <CharactersSection slug={slug} characterType="npc" />
    </div>
  );
}
