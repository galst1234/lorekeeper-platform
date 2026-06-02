import SuperTokens from "supertokens-auth-react";
import EmailPassword from "supertokens-auth-react/recipe/emailpassword";
import Session from "supertokens-auth-react/recipe/session";
import ThirdParty from "supertokens-auth-react/recipe/thirdparty";

export function initSuperTokens() {
  SuperTokens.init({
    appInfo: {
      appName: "Lorekeeper Platform",
      apiDomain: window.location.origin,
      websiteDomain: window.location.origin,
      apiBasePath: "/auth",
      websiteBasePath: "/login",
    },
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
