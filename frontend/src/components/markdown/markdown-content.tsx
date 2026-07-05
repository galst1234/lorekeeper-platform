import ReactMarkdown, { type Components } from "react-markdown";
import remarkBreaks from "remark-breaks";
import remarkDirective from "remark-directive";
import remarkGfm from "remark-gfm";
import { EntityLinkRenderer } from "@/components/markdown/entity-link-renderer";
import { remarkEntityDirectives } from "@/components/markdown/remark-entity-directives";
import { useEntityResolver } from "@/components/markdown/use-entity-resolver";

interface MarkdownContentProps {
  content: string;
  campaignSlug: string;
  className?: string;
}

export function MarkdownContent({ content, campaignSlug, className }: MarkdownContentProps) {
  const resolver = useEntityResolver(campaignSlug);

  const components: Components = {
    p: ({ children }) => <p className="mb-4 leading-7 last:mb-0">{children}</p>,
    h1: ({ children }) => <h1 className="mb-4 mt-6 text-2xl font-bold first:mt-0">{children}</h1>,
    h2: ({ children }) => <h2 className="mb-3 mt-6 text-xl font-bold first:mt-0">{children}</h2>,
    h3: ({ children }) => <h3 className="mb-2 mt-4 text-lg font-semibold first:mt-0">{children}</h3>,
    ul: ({ children }) => <ul className="mb-4 list-disc space-y-1 pl-6">{children}</ul>,
    ol: ({ children }) => <ol className="mb-4 list-decimal space-y-1 pl-6">{children}</ol>,
    li: ({ children }) => <li>{children}</li>,
    blockquote: ({ children }) => (
      <blockquote className="mb-4 border-l-2 border-border pl-4 italic text-muted-foreground">{children}</blockquote>
    ),
    code: ({ children }) => <code className="rounded bg-muted px-1 py-0.5 font-mono text-sm">{children}</code>,
    pre: ({ children }) => <pre className="mb-4 overflow-x-auto rounded-md bg-muted p-3 text-sm">{children}</pre>,
    a: ({ children, href }) => (
      <a
        href={href}
        target="_blank"
        rel="noreferrer"
        className="text-primary underline underline-offset-2 hover:no-underline"
      >
        {children}
      </a>
    ),
    // Render as a click-through link instead of an <img>: there's no image upload yet, so any
    // src is an arbitrary external URL that would otherwise auto-fetch for every viewer.
    img: ({ src, alt }) => (
      <a
        href={typeof src === "string" ? src : undefined}
        target="_blank"
        rel="noreferrer"
        className="text-primary underline underline-offset-2 hover:no-underline"
      >
        {alt || src}
      </a>
    ),
    table: ({ children }) => <table className="mb-4 w-full border-collapse text-sm">{children}</table>,
    th: ({ children }) => (
      <th className="border border-border bg-muted px-2 py-1 text-left font-semibold">{children}</th>
    ),
    td: ({ children }) => <td className="border border-border px-2 py-1">{children}</td>,
    // biome-ignore lint/suspicious/noExplicitAny: "entity-link" is a synthetic tag name from remarkEntityDirectives, not part of react-markdown's typed Components map
    "entity-link": (props: any) => (
      <EntityLinkRenderer
        entityType={props.entityType}
        slug={props.slug}
        label={props.label}
        campaignSlug={campaignSlug}
        resolver={resolver}
      />
    ),
  } as Components;

  return (
    <div className={className}>
      <ReactMarkdown
        remarkPlugins={[remarkGfm, remarkBreaks, remarkDirective, remarkEntityDirectives]}
        components={components}
      >
        {content}
      </ReactMarkdown>
    </div>
  );
}
