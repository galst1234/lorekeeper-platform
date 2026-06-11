import { createFileRoute } from "@tanstack/react-router";
import { EmailPasswordPreBuiltUI } from "supertokens-auth-react/recipe/emailpassword/prebuiltui";
import { ThirdPartyPreBuiltUI } from "supertokens-auth-react/recipe/thirdparty/prebuiltui";
import { getRoutingComponent } from "supertokens-auth-react/ui";

const preBuiltUIList = [ThirdPartyPreBuiltUI, EmailPasswordPreBuiltUI];

export const Route = createFileRoute("/login_/callback/$provider")({
  component: CallbackPage,
});

function CallbackPage() {
  return getRoutingComponent(preBuiltUIList);
}
