import { useQuery } from "@tanstack/react-query";
import type { CampaignEntityResponse } from "@/api/generated";
import {
  listCharactersOptions,
  listChronicleEntriesOptions,
  listItemsOptions,
  listLocationsOptions,
} from "@/api/generated/@tanstack/react-query.gen";
import type { EntityDirectiveType } from "@/components/markdown/entity-registry";

export interface ResolvedEntity {
  type: EntityDirectiveType;
  slug: string;
  name: string;
}

export interface EntityResolver {
  resolve(type: string, slug: string): ResolvedEntity | null;
  entities: ResolvedEntity[];
}

function toResolvedEntities<T extends CampaignEntityResponse>(
  type: EntityDirectiveType,
  items: T[] | undefined,
  getName: (item: T) => string
): ResolvedEntity[] {
  return (items ?? []).map((item) => ({ type, slug: item.slug, name: getName(item) }));
}

export function useEntityResolver(campaignSlug: string | undefined): EntityResolver {
  const enabled = Boolean(campaignSlug);
  const slug = campaignSlug ?? "";

  const { data: characters } = useQuery({ ...listCharactersOptions({ path: { slug } }), enabled });
  const { data: items } = useQuery({ ...listItemsOptions({ path: { slug } }), enabled });
  const { data: entries } = useQuery({ ...listChronicleEntriesOptions({ path: { slug } }), enabled });
  const { data: locations } = useQuery({ ...listLocationsOptions({ path: { slug } }), enabled });

  const entities: ResolvedEntity[] = [
    ...toResolvedEntities("character", characters, (character) => character.name),
    ...toResolvedEntities("item", items, (item) => item.name),
    ...toResolvedEntities("entry", entries, (entry) => entry.title),
    ...toResolvedEntities("location", locations, (location) => location.name),
  ];

  function resolve(type: string, targetSlug: string): ResolvedEntity | null {
    return entities.find((entity) => entity.type === type && entity.slug === targetSlug) ?? null;
  }

  return { resolve, entities };
}
