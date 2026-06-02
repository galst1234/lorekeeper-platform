import { useSuspenseQuery } from "@tanstack/react-query";
import { createFileRoute, redirect } from "@tanstack/react-router";
import { meQueryOptions } from "../api/me";
import { doesSessionExist } from "../lib/auth";

export const Route = createFileRoute("/")({
  beforeLoad: async ({ context }) => {
    if (!(await doesSessionExist())) {
      throw redirect({ to: "/login" });
    }
    const me = await context.queryClient.ensureQueryData(meQueryOptions);
    if (me.display_name === null) {
      throw redirect({ to: "/onboarding" });
    }
  },
  component: HomePage,
});

function HomePage() {
  const { data: me } = useSuspenseQuery(meQueryOptions);

  return (
    <main style={{ padding: "2rem" }}>
      <h1>Welcome, {me.display_name}</h1>
      <p>{me.email}</p>
    </main>
  );
}
