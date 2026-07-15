import { Link } from "@tanstack/react-router";
import { ENTITY_KINDS } from "@/components/markdown/entity-registry";
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

  const kind = ENTITY_KINDS.find((candidate) => candidate.type === resolved.type);
  if (!kind) return null;

  return (
    <Link to={kind.routeTo} params={kind.buildParams(campaignSlug, resolved.slug)} className={linkClassName}>
      {displayText}
    </Link>
  );
}
