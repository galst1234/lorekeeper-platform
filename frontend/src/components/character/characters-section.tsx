import { useSuspenseQuery } from "@tanstack/react-query";
import { Link } from "@tanstack/react-router";
import { ChevronRight, User } from "lucide-react";
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
              <Link
                to="/campaigns/$slug/characters/$characterSlug"
                params={{ slug, characterSlug: character.slug }}
                className="flex items-center gap-3"
              >
                <div className="h-24 w-24 shrink-0 overflow-hidden rounded-md bg-muted flex items-center justify-center">
                  {character.image_url ? (
                    <img src={character.image_url} alt="" className="h-full w-full object-cover" />
                  ) : (
                    <User className="h-10 w-10 text-muted-foreground" />
                  )}
                </div>
                <div className="flex flex-1 items-center justify-between min-w-0">
                  <span className="font-medium hover:underline truncate">{character.name}</span>
                  <ChevronRight className="h-4 w-4 text-muted-foreground shrink-0" />
                </div>
              </Link>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
}
