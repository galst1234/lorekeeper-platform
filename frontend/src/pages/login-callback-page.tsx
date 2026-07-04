import { EmailPasswordPreBuiltUI } from "supertokens-auth-react/recipe/emailpassword/prebuiltui";
import { ThirdPartyPreBuiltUI } from "supertokens-auth-react/recipe/thirdparty/prebuiltui";
import { getRoutingComponent } from "supertokens-auth-react/ui";

const preBuiltUIList = [ThirdPartyPreBuiltUI, EmailPasswordPreBuiltUI];

export function LoginCallbackPage() {
  return getRoutingComponent(preBuiltUIList);
}
