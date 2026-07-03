import SuperTokens from "supertokens-auth-react";
import EmailPassword from "supertokens-auth-react/recipe/emailpassword";
import Session from "supertokens-auth-react/recipe/session";
import ThirdParty from "supertokens-auth-react/recipe/thirdparty";
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
