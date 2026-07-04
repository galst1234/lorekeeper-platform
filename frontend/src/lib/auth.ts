import { type QueryClient, queryOptions, useQueryClient, useSuspenseQuery } from "@tanstack/react-query";
import SuperTokens from "supertokens-auth-react";
import EmailPassword from "supertokens-auth-react/recipe/emailpassword";
import Session from "supertokens-auth-react/recipe/session";
import ThirdParty from "supertokens-auth-react/recipe/thirdparty";
import { getMe, type MeResponse } from "@/api/generated";
import { getMeQueryKey } from "@/api/generated/@tanstack/react-query.gen";
import { reconcileCurrentUser } from "./current-user-cache";
import { SUPERTOKENS_DARK_THEME_STYLE } from "./supertokens-theme";

export function initSuperTokens() {
  SuperTokens.init({
    appInfo: {
      appName: "Lorekeeper Platform",
      apiDomain: window.location.origin,
      websiteDomain: window.location.origin,
      apiBasePath: "/auth",
      websiteBasePath: "/login",
    },
    style: SUPERTOKENS_DARK_THEME_STYLE,
    // Shadow DOM would isolate the widget from our `.dark` ancestor class, which the
    // style override above depends on to detect the app's theme.
    useShadowDom: false,
    recipeList: [
      EmailPassword.init({
        signInAndUpFeature: {
          signUpForm: {
            formFields: [
              {
                id: "display_name",
                label: "Display name",
                placeholder: "Choose your display name",
              },
            ],
          },
        },
      }),
      ThirdParty.init({
        signInAndUpFeature: {
          providers: [
            { id: "google", name: "Google" },
            { id: "discord", name: "Discord" },
          ],
        },
      }),
      Session.init(),
    ],
  });
}

export async function doesSessionExist(): Promise<boolean> {
  return Session.doesSessionExist();
}

export async function signOut(): Promise<void> {
  await Session.signOut();
}

export function getCurrentUserOptions(queryClient: QueryClient) {
  const meKey = getMeQueryKey();
  return queryOptions({
    queryKey: meKey,
    queryFn: async ({ signal }) => {
      const previousUserId = queryClient.getQueryData<MeResponse>(meKey)?.id;
      const { data: me } = await getMe({ signal, throwOnError: true });
      return reconcileCurrentUser(previousUserId, me);
    },
  });
}

export function useCurrentUser(): MeResponse {
  const queryClient = useQueryClient();
  return useSuspenseQuery(getCurrentUserOptions(queryClient)).data;
}
