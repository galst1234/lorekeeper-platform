import { useQuery } from "@tanstack/react-query";
import {
  listCharactersOptions,
  listChronicleEntriesOptions,
  listItemsOptions,
  listLocationsOptions,
} from "@/api/generated/@tanstack/react-query.gen";

export type EntityDirectiveType = "character" | "item" | "entry" | "location";

export interface ResolvedEntity {
  type: EntityDirectiveType;
  slug: string;
  name: string;
}

export interface EntityResolver {
  resolve(type: string, slug: string): ResolvedEntity | null;
  entities: ResolvedEntity[];
}

export function useEntityResolver(campaignSlug: string | undefined): EntityResolver {
  const enabled = Boolean(campaignSlug);
  const slug = campaignSlug ?? "";

  const { data: characters } = useQuery({ ...listCharactersOptions({ path: { slug } }), enabled });
  const { data: items } = useQuery({ ...listItemsOptions({ path: { slug } }), enabled });
  const { data: entries } = useQuery({ ...listChronicleEntriesOptions({ path: { slug } }), enabled });
  const { data: locations } = useQuery({ ...listLocationsOptions({ path: { slug } }), enabled });

  const entities: ResolvedEntity[] = [
    ...(characters ?? []).map((character) => ({
      type: "character" as const,
      slug: character.slug,
      name: character.name,
    })),
    ...(items ?? []).map((item) => ({ type: "item" as const, slug: item.slug, name: item.name })),
    ...(entries ?? []).map((entry) => ({ type: "entry" as const, slug: entry.slug, name: entry.title })),
    ...(locations ?? []).map((location) => ({
      type: "location" as const,
      slug: location.slug,
      name: location.name,
    })),
  ];

  function resolve(type: string, targetSlug: string): ResolvedEntity | null {
    return entities.find((entity) => entity.type === type && entity.slug === targetSlug) ?? null;
  }

  return { resolve, entities };
}
