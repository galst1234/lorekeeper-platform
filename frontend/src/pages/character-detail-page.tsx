import { useSuspenseQuery } from "@tanstack/react-query";
import { getRouteApi, Link } from "@tanstack/react-router";
import { getCharacterOptions } from "@/api/generated/@tanstack/react-query.gen";
import { CharacterInfo } from "@/components/character/character-info";
import { CharacterSidebarCard } from "@/components/character/character-sidebar-card";

const Route = getRouteApi("/campaigns/$slug/characters/$characterSlug");

export function CharacterDetailPage() {
  const { slug, characterSlug } = Route.useParams();
  const { data: character } = useSuspenseQuery(getCharacterOptions({ path: { slug, character_slug: characterSlug } }));

  return (
    <div className="max-w-4xl mx-auto px-6 py-8">
      <Link
        to="/campaigns/$slug/characters"
        params={{ slug }}
        className="text-sm text-muted-foreground hover:text-foreground inline-block mb-6"
      >
        ← Back to Characters
      </Link>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
        <div className="md:col-span-2">
          <CharacterInfo character={character} campaignSlug={slug} />
        </div>
        <div>
          <CharacterSidebarCard character={character} />
        </div>
      </div>
    </div>
  );
}
