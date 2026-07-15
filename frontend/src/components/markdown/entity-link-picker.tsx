import { ENTITY_KINDS } from "@/components/markdown/entity-registry";
import type { EntityResolver, ResolvedEntity } from "@/components/markdown/use-entity-resolver";

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

export function EntityLinkPicker({ open, onOpenChange, resolver, onSelect }: EntityLinkPickerProps) {
  return (
    <CommandDialog
      open={open}
      onOpenChange={onOpenChange}
      title="Link an entity"
      description="Search characters, items, chronicle entries, etc. to link."
    >
      <CommandInput placeholder="Search characters, items, chronicle entries, etc." />
      <CommandList>
        <CommandEmpty>No entities found.</CommandEmpty>
        {ENTITY_KINDS.map(({ type, label }) => {
          const entitiesOfType = resolver.entities.filter((entity) => entity.type === type);
          if (entitiesOfType.length === 0) return null;
          return (
            <CommandGroup key={type} heading={label}>
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
