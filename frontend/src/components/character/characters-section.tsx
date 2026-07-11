import { useSuspenseQuery } from "@tanstack/react-query";
import { Link } from "@tanstack/react-router";
import { ChevronRight, User } from "lucide-react";
import { listCharactersOptions } from "@/api/generated/@tanstack/react-query.gen";
import { Badge } from "@/components/ui/badge";
import { Card } from "@/components/ui/card";
import { matchesQuery } from "@/lib/search";

interface CharactersSectionProps {
  slug: string;
  characterType: "pc" | "npc";
  query?: string;
}

export function CharactersSection({ slug, characterType, query = "" }: CharactersSectionProps) {
  const { data: characters } = useSuspenseQuery(listCharactersOptions({ path: { slug } }));

  const ofType = characters.filter((character) => character.character_type === characterType);
  const filtered = ofType.filter((character) => matchesQuery(character.name, query));
  const title = characterType === "pc" ? "Player Characters" : "NPCs";
  const emptyText = characterType === "pc" ? "No player characters yet." : "No NPCs yet.";
  const noMatchText = `No matches for "${query}".`;

  return (
    <div>
      <h2 className="text-lg font-semibold mb-3">{title}</h2>

      {filtered.length === 0 ? (
        <p className="text-sm text-muted-foreground italic">{ofType.length === 0 ? emptyText : noMatchText}</p>
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
                <div className="flex flex-1 items-center justify-between min-w-0 gap-2">
                  <span className="flex items-center gap-2 min-w-0">
                    <span className="font-medium hover:underline truncate">{character.name}</span>
                    {character.restricted && <Badge variant="outline">Restricted</Badge>}
                  </span>
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
