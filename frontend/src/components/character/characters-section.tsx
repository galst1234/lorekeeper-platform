import { useSuspenseQuery } from "@tanstack/react-query";
import { Link } from "@tanstack/react-router";
import { ChevronRight } from "lucide-react";
import { listCharactersOptions } from "@/api/generated/@tanstack/react-query.gen";
import { Card } from "@/components/ui/card";

interface CharactersSectionProps {
  slug: string;
  characterType: "pc" | "npc";
}

export function CharactersSection({ slug, characterType }: CharactersSectionProps) {
  const { data: characters } = useSuspenseQuery(listCharactersOptions({ path: { slug } }));

  const filtered = characters.filter((c) => c.character_type === characterType);
  const title = characterType === "pc" ? "Player Characters" : "NPCs";
  const emptyText = characterType === "pc" ? "No player characters yet." : "No NPCs yet.";

  return (
    <div>
      <h2 className="text-lg font-semibold mb-3">{title}</h2>

      {filtered.length === 0 ? (
        <p className="text-sm text-muted-foreground italic">{emptyText}</p>
      ) : (
        <div className="space-y-2">
          {filtered.map((character) => (
            <Card key={character.id} className="px-4 py-3">
              <div className="flex items-center justify-between">
                <Link
                  to="/campaigns/$slug/characters/$characterSlug"
                  params={{ slug, characterSlug: character.slug }}
                  className="font-medium hover:underline"
                >
                  {character.name}
                </Link>
                <ChevronRight className="h-4 w-4 text-muted-foreground" />
              </div>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
}
