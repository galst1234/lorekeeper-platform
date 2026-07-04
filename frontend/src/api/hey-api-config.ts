import type { CreateClientConfig } from "./generated/client.gen";

export const createClientConfig: CreateClientConfig = (config) => ({
  ...config,
  fetch: (input, init) => fetch(input, { ...init, credentials: "include" }),
});
