import { getRouteApi } from "@tanstack/react-router";
import { CharacterPageEditor } from "@/components/character/character-page-editor";

const Route = getRouteApi("/campaigns/$slug/characters/new");

export function CharacterNewPage() {
  const { slug } = Route.useParams();
  return <CharacterPageEditor mode="create" campaignSlug={slug} />;
}
