export interface DirectiveNodeInfo {
  entityType: string;
  slug: string;
  label?: string;
}

// biome-ignore lint/suspicious/noExplicitAny: mdast directive node shape comes from remark-directive, which has no exported node type
export function readDirectiveNode(node: any): DirectiveNodeInfo {
  const firstChild = node.children?.[0];
  const slug = firstChild?.type === "text" ? firstChild.value : "";
  const label = typeof node.attributes?.label === "string" ? node.attributes.label : undefined;
  return { entityType: node.name, slug, label };
}
