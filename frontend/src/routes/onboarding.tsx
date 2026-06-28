import { useMutation, useQueryClient } from "@tanstack/react-query";
import { createFileRoute, redirect, useRouter } from "@tanstack/react-router";
import { type SyntheticEvent, useState } from "react";
import { meQueryOptions, patchMe } from "../api/me";
import { doesSessionExist } from "../lib/auth";

export const Route = createFileRoute("/onboarding")({
  validateSearch: (search: Record<string, unknown>) => ({
    redirectToPath: typeof search.redirectToPath === "string" ? search.redirectToPath : undefined,
  }),
  beforeLoad: async ({ context }) => {
    if (!(await doesSessionExist())) {
      throw redirect({ to: "/login" });
    }
    const me = await context.queryClient.ensureQueryData(meQueryOptions);
    if (me.display_name !== null) {
      throw redirect({ to: "/" });
    }
  },
  component: OnboardingPage,
});

function OnboardingPage() {
  const router = useRouter();
  const queryClient = useQueryClient();
  const { redirectToPath } = Route.useSearch();
  const [name, setName] = useState("");
  const [error, setError] = useState("");

  const mutation = useMutation({
    mutationFn: patchMe,
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ["me"] });
      const safePath = redirectToPath?.startsWith("/") && !redirectToPath.startsWith("//") ? redirectToPath : "/";
      await router.navigate({ to: safePath });
    },
    onError: () => setError("Something went wrong. Please try again."),
  });

  function handleSubmit(e: SyntheticEvent<HTMLFormElement>) {
    e.preventDefault();
    const trimmed = name.trim();
    if (!trimmed) {
      setError("Display name cannot be empty.");
      return;
    }
    if (trimmed.length > 50) {
      setError("Display name cannot exceed 50 characters.");
      return;
    }
    setError("");
    mutation.mutate(trimmed);
  }

  return (
    <main style={{ padding: "2rem", maxWidth: 400 }}>
      <h1>Choose your display name</h1>
      <p>This is how other players will see you.</p>
      <form onSubmit={handleSubmit}>
        <input
          type="text"
          value={name}
          onChange={(e) => setName(e.target.value)}
          placeholder="Display name"
          maxLength={50}
          style={{ display: "block", marginBottom: "0.5rem", width: "100%" }}
        />
        {error && <p style={{ color: "red" }}>{error}</p>}
        <button type="submit" disabled={mutation.isPending}>
          {mutation.isPending ? "Saving…" : "Continue"}
        </button>
      </form>
    </main>
  );
}
