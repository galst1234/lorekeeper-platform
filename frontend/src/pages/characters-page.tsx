import { getRouteApi, Link } from "@tanstack/react-router";
import { Plus } from "lucide-react";
import { CharactersSection } from "@/components/character/characters-section";
import { PageContainer } from "@/components/layout/page-container";
import { Button } from "@/components/ui/button";

const Route = getRouteApi("/campaigns/$slug/characters/");

export function CharactersPage() {
  const { slug } = Route.useParams();

  return (
    <PageContainer className="space-y-8">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold">Characters</h1>
        <Button asChild size="sm">
          <Link to="/campaigns/$slug/characters/new" params={{ slug }}>
            <Plus className="h-4 w-4" />
            New Character
          </Link>
        </Button>
      </div>
      <CharactersSection slug={slug} characterType="pc" />
      <CharactersSection slug={slug} characterType="npc" />
    </PageContainer>
  );
}
