import { createFileRoute } from "@tanstack/react-router";
import { EmailPasswordPreBuiltUI } from "supertokens-auth-react/recipe/emailpassword/prebuiltui";
import { ThirdPartyPreBuiltUI } from "supertokens-auth-react/recipe/thirdparty/prebuiltui";
import { getRoutingComponent } from "supertokens-auth-react/ui";

const preBuiltUIList = [EmailPasswordPreBuiltUI, ThirdPartyPreBuiltUI];

export const Route = createFileRoute("/login_/reset-password")({
  component: ResetPasswordPage,
});

function ResetPasswordPage() {
  return getRoutingComponent(preBuiltUIList);
}
