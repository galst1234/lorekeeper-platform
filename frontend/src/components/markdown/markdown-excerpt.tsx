import { useMemo } from "react";
import remarkDirective from "remark-directive";
import remarkGfm from "remark-gfm";
import remarkParse from "remark-parse";
import { unified } from "unified";
import { SKIP, visit } from "unist-util-visit";
import { readDirectiveNode } from "@/components/markdown/directive-node";
import { useEntityResolver } from "@/components/markdown/use-entity-resolver";

const EXCERPT_MAX_LENGTH = 200;

function toPlainText(
  // biome-ignore lint/suspicious/noExplicitAny: mdast tree shape comes from remark-parse, which has no exported node type
  tree: any,
  resolve: (type: string, slug: string) => { name: string } | null
): string {
  const parts: string[] = [];
  // biome-ignore lint/suspicious/noExplicitAny: see above
  visit(tree, (node: any) => {
    if (node.type === "text") {
      parts.push(node.value);
      return;
    }
    if (node.type === "textDirective" || node.type === "leafDirective") {
      const info = readDirectiveNode(node);
      const resolved = resolve(info.entityType, info.slug);
      parts.push(info.label || resolved?.name || info.slug);
      return SKIP;
    }
  });
  return parts.join("");
}

function truncate(text: string, maxLength: number): string {
  const collapsed = text.replace(/\s+/g, " ").trim();
  if (collapsed.length <= maxLength) return collapsed;
  return `${collapsed.slice(0, maxLength).trimEnd()}…`;
}

interface MarkdownExcerptProps {
  content: string;
  campaignSlug: string;
  className?: string;
}

export function MarkdownExcerpt({ content, campaignSlug, className }: MarkdownExcerptProps) {
  const resolver = useEntityResolver(campaignSlug);

  const excerpt = useMemo(() => {
    const tree = unified().use(remarkParse).use(remarkGfm).use(remarkDirective).parse(content);
    const plainText = toPlainText(tree, resolver.resolve);
    return truncate(plainText, EXCERPT_MAX_LENGTH);
  }, [content, resolver]);

  return <p className={className}>{excerpt}</p>;
}
