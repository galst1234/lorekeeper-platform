import { createFileRoute, redirect } from "@tanstack/react-router";
import { EmailPasswordPreBuiltUI } from "supertokens-auth-react/recipe/emailpassword/prebuiltui";
import { ThirdPartyPreBuiltUI } from "supertokens-auth-react/recipe/thirdparty/prebuiltui";
import { AuthPage } from "supertokens-auth-react/ui";
import { doesSessionExist } from "@/lib/auth";

export const Route = createFileRoute("/login")({
  beforeLoad: async () => {
    if (await doesSessionExist()) {
      throw redirect({ to: "/" });
    }
  },
  component: LoginPage,
});

function LoginPage() {
  return (
    <div className="min-h-screen bg-background flex flex-col items-center justify-center p-4">
      <div className="mb-8 text-2xl font-bold text-foreground">Lorekeeper</div>
      <AuthPage preBuiltUIList={[EmailPasswordPreBuiltUI, ThirdPartyPreBuiltUI]} />
    </div>
  );
}
