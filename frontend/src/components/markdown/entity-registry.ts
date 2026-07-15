export const ENTITY_KINDS = [
  {
    type: "character",
    label: "Characters",
    routeTo: "/campaigns/$slug/characters/$characterSlug",
    buildParams: (campaignSlug: string, entitySlug: string) => ({ slug: campaignSlug, characterSlug: entitySlug }),
  },
  {
    type: "item",
    label: "Items",
    routeTo: "/campaigns/$slug/items/$itemSlug",
    buildParams: (campaignSlug: string, entitySlug: string) => ({ slug: campaignSlug, itemSlug: entitySlug }),
  },
  {
    type: "entry",
    label: "Chronicle Entries",
    routeTo: "/campaigns/$slug/chronicle/$entrySlug",
    buildParams: (campaignSlug: string, entitySlug: string) => ({ slug: campaignSlug, entrySlug: entitySlug }),
  },
  {
    type: "location",
    label: "Locations",
    routeTo: "/campaigns/$slug/locations/$locationSlug",
    buildParams: (campaignSlug: string, entitySlug: string) => ({ slug: campaignSlug, locationSlug: entitySlug }),
  },
] as const satisfies ReadonlyArray<{
  type: string;
  label: string;
  routeTo: string;
  buildParams: (campaignSlug: string, entitySlug: string) => Record<string, string>;
}>;

export type EntityKindMeta = (typeof ENTITY_KINDS)[number];
export type EntityDirectiveType = EntityKindMeta["type"];

export const ENTITY_DIRECTIVE_NAMES: ReadonlySet<string> = new Set(ENTITY_KINDS.map((kind) => kind.type));
