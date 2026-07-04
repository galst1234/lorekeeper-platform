import { EmailPasswordPreBuiltUI } from "supertokens-auth-react/recipe/emailpassword/prebuiltui";
import { ThirdPartyPreBuiltUI } from "supertokens-auth-react/recipe/thirdparty/prebuiltui";
import { AuthPage } from "supertokens-auth-react/ui";

export function LoginPage() {
  return (
    <div className="min-h-screen bg-background flex flex-col items-center justify-center p-4">
      <div className="mb-8 text-2xl font-bold text-foreground">Lorekeeper</div>
      <AuthPage preBuiltUIList={[EmailPasswordPreBuiltUI, ThirdPartyPreBuiltUI]} />
      <a
        href="/legacy-agent"
        className="mt-4 text-sm text-muted-foreground hover:text-foreground underline underline-offset-4"
      >
        Looking for the legacy agent? Go there
      </a>
    </div>
  );
}
