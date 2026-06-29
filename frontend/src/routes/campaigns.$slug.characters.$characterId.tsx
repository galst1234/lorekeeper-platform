import { createFileRoute } from "@tanstack/react-router";

export const Route = createFileRoute("/campaigns/$slug/characters/$characterId")({
  component: CharacterDetailPage,
});

function CharacterDetailPage() {
  return (
    <main style={{ padding: "2rem" }}>
      <p>Character content coming soon</p>
    </main>
  );
}
