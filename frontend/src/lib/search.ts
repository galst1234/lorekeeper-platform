export function matchesQuery(haystack: string, query: string): boolean {
  const normalizedQuery = query.trim().toLowerCase();
  if (normalizedQuery === "") return true;
  return haystack.toLowerCase().includes(normalizedQuery);
}
