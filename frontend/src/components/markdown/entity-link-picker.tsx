import type { EntityDirectiveType, EntityResolver, ResolvedEntity } from "@/components/markdown/use-entity-resolver";

import {
  CommandDialog,
  CommandEmpty,
  CommandGroup,
  CommandInput,
  CommandItem,
  CommandList,
} from "@/components/ui/command";

interface EntityLinkPickerProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  resolver: EntityResolver;
  onSelect: (entity: ResolvedEntity) => void;
}

const GROUP_LABELS: Record<EntityDirectiveType, string> = {
  character: "Characters",
  item: "Items",
  entry: "Chronicle Entries",
};

const GROUP_ORDER: EntityDirectiveType[] = ["character", "item", "entry"];

export function EntityLinkPicker({ open, onOpenChange, resolver, onSelect }: EntityLinkPickerProps) {
  return (
    <CommandDialog
      open={open}
      onOpenChange={onOpenChange}
      title="Link an entity"
      description="Search characters, items, and chronicle entries to link."
    >
      <CommandInput placeholder="Search characters, items, chronicle entries…" />
      <CommandList>
        <CommandEmpty>No entities found.</CommandEmpty>
        {GROUP_ORDER.map((type) => {
          const entitiesOfType = resolver.entities.filter((entity) => entity.type === type);
          if (entitiesOfType.length === 0) return null;
          return (
            <CommandGroup key={type} heading={GROUP_LABELS[type]}>
              {entitiesOfType.map((entity) => (
                <CommandItem
                  key={`${entity.type}-${entity.slug}`}
                  value={`${entity.type}-${entity.slug}-${entity.name}`}
                  onSelect={() => {
                    onSelect(entity);
                    onOpenChange(false);
                  }}
                >
                  {entity.name}
                </CommandItem>
              ))}
            </CommandGroup>
          );
        })}
      </CommandList>
    </CommandDialog>
  );
}
