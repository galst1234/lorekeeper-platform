import { useSuspenseQuery } from "@tanstack/react-query";
import { getRouteApi } from "@tanstack/react-router";
import { getCharacterOptions } from "@/api/generated/@tanstack/react-query.gen";
import { CharacterPageEditor } from "@/components/character/character-page-editor";

const Route = getRouteApi("/campaigns/$slug/characters/$characterSlug_/edit");

export function CharacterEditPage() {
  const { slug, characterSlug } = Route.useParams();
  const { data: character } = useSuspenseQuery(getCharacterOptions({ path: { slug, character_slug: characterSlug } }));

  return <CharacterPageEditor mode="edit" campaignSlug={slug} character={character} />;
}
