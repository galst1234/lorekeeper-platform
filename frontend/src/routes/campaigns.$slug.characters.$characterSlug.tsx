import { useSuspenseQuery } from "@tanstack/react-query";
import { createFileRoute, Link } from "@tanstack/react-router";
import { characterQueryOptions } from "@/api/characters";
import { CharacterInfo } from "@/components/character/character-info";
import { CharacterSidebarCard } from "@/components/character/character-sidebar-card";

export const Route = createFileRoute("/campaigns/$slug/characters/$characterSlug")({
  component: CharacterDetailPage,
});

function CharacterDetailPage() {
  const { slug, characterSlug } = Route.useParams();
  const { data: character } = useSuspenseQuery(characterQueryOptions(slug, characterSlug));

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
