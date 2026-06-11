import { createFileRoute } from "@tanstack/react-router";
import { EmailPasswordPreBuiltUI } from "supertokens-auth-react/recipe/emailpassword/prebuiltui";
import { ThirdPartyPreBuiltUI } from "supertokens-auth-react/recipe/thirdparty/prebuiltui";
import { AuthPage } from "supertokens-auth-react/ui";

export const Route = createFileRoute("/login_/callback/$provider")({
  component: CallbackPage,
});

function CallbackPage() {
  return <AuthPage preBuiltUIList={[ThirdPartyPreBuiltUI, EmailPasswordPreBuiltUI]} />;
}
