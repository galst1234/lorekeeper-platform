import { useSuspenseQuery } from "@tanstack/react-query";
import { createFileRoute, Link, redirect } from "@tanstack/react-router";
import { campaignsQueryOptions } from "../api/campaigns";
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
    await context.queryClient.ensureQueryData(campaignsQueryOptions);
  },
  component: HomePage,
});

function HomePage() {
  const { data: me } = useSuspenseQuery(meQueryOptions);
  const { data: campaigns } = useSuspenseQuery(campaignsQueryOptions);

  return (
    <main style={{ padding: "2rem" }}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "1.5rem" }}>
        <h1>Welcome, {me.display_name}</h1>
        <Link to="/campaigns/new">
          <button type="button">New Campaign</button>
        </Link>
      </div>

      {campaigns.length === 0 ? (
        <div style={{ textAlign: "center", padding: "3rem 0", color: "#666" }}>
          <p>You don't have any campaigns yet.</p>
          <Link to="/campaigns/new">
            <button type="button">Create your first campaign</button>
          </Link>
        </div>
      ) : (
        <ul style={{ listStyle: "none", padding: 0, display: "grid", gap: "1rem" }}>
          {campaigns.map((campaign) => (
            <li key={campaign.id} style={{ border: "1px solid #ddd", borderRadius: "8px", padding: "1rem" }}>
              <Link to="/campaigns/$slug" params={{ slug: campaign.slug }}>
                <h2 style={{ margin: "0 0 0.5rem" }}>{campaign.name}</h2>
              </Link>
              {campaign.description && <p style={{ margin: "0 0 0.5rem", color: "#555" }}>{campaign.description}</p>}
              <small style={{ color: "#999" }}>Created {new Date(campaign.created_at).toLocaleDateString()}</small>
            </li>
          ))}
        </ul>
      )}

      <div style={{ marginTop: "2rem" }}>
        <Link to="/logout">Logout</Link>
      </div>
    </main>
  );
}
