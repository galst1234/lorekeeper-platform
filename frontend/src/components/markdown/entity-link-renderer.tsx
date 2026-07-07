import { Link } from "@tanstack/react-router";
import type { EntityResolver } from "@/components/markdown/use-entity-resolver";

interface EntityLinkRendererProps {
  entityType?: string;
  slug?: string;
  label?: string;
  campaignSlug: string;
  resolver: EntityResolver;
}

export function EntityLinkRenderer({ entityType, slug, label, campaignSlug, resolver }: EntityLinkRendererProps) {
  const resolved = entityType && slug ? resolver.resolve(entityType, slug) : null;
  const displayText = label || resolved?.name || slug || "";

  if (!resolved || !campaignSlug) {
    return (
      <span className="border-b border-dashed border-destructive/60 text-destructive/80" title="Broken link">
        {displayText}
      </span>
    );
  }

  const linkClassName = "font-medium text-primary underline underline-offset-2 hover:no-underline";

  switch (resolved.type) {
    case "character":
      return (
        <Link
          to="/campaigns/$slug/characters/$characterSlug"
          params={{ slug: campaignSlug, characterSlug: resolved.slug }}
          className={linkClassName}
        >
          {displayText}
        </Link>
      );
    case "item":
      return (
        <Link
          to="/campaigns/$slug/items/$itemSlug"
          params={{ slug: campaignSlug, itemSlug: resolved.slug }}
          className={linkClassName}
        >
          {displayText}
        </Link>
      );
    case "entry":
      return (
        <Link
          to="/campaigns/$slug/chronicle/$entrySlug"
          params={{ slug: campaignSlug, entrySlug: resolved.slug }}
          className={linkClassName}
        >
          {displayText}
        </Link>
      );
    case "location":
      return (
        <Link
          to="/campaigns/$slug/locations/$locationSlug"
          params={{ slug: campaignSlug, locationSlug: resolved.slug }}
          className={linkClassName}
        >
          {displayText}
        </Link>
      );
  }
}
