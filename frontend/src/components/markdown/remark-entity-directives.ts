import { visit } from "unist-util-visit";
import { readDirectiveNode } from "@/components/markdown/directive-node";

const ENTITY_DIRECTIVE_NAMES = new Set(["character", "item", "entry", "location"]);

export function remarkEntityDirectives() {
  // biome-ignore lint/suspicious/noExplicitAny: mdast tree shape comes from remark-directive, which has no exported node type
  return (tree: any) => {
    // biome-ignore lint/suspicious/noExplicitAny: mdast tree shape comes from remark-directive, which has no exported node type
    visit(tree, ["textDirective", "leafDirective"], (node: any) => {
      const info = readDirectiveNode(node);
      node.data = node.data ?? {};
      const data = node.data;
      data.hName = "entity-link";
      data.hProperties = {
        entityType: ENTITY_DIRECTIVE_NAMES.has(info.entityType) ? info.entityType : "unknown",
        slug: info.slug,
        label: info.label,
      };
      node.children = [];
    });
  };
}
