import { zodResolver } from "@hookform/resolvers/zod";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { useRouter } from "@tanstack/react-router";
import { useForm } from "react-hook-form";
import { z } from "zod";
import { patchMe } from "@/api/me";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Form, FormControl, FormField, FormItem, FormLabel, FormMessage } from "@/components/ui/form";
import { Input } from "@/components/ui/input";

const onboardingSchema = z.object({
  display_name: z
    .string()
    .trim()
    .min(1, "Display name cannot be empty")
    .max(50, "Display name cannot exceed 50 characters"),
});

type OnboardingFormValues = z.infer<typeof onboardingSchema>;

interface OnboardingFormProps {
  redirectToPath?: string;
}

export function OnboardingForm({ redirectToPath }: OnboardingFormProps) {
  const router = useRouter();
  const queryClient = useQueryClient();

  const form = useForm<OnboardingFormValues>({
    resolver: zodResolver(onboardingSchema),
    defaultValues: { display_name: "" },
  });

  const mutation = useMutation({
    mutationFn: (values: OnboardingFormValues) => patchMe(values.display_name.trim()),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ["me"] });
      const safePath = redirectToPath?.startsWith("/") && !redirectToPath.startsWith("//") ? redirectToPath : "/";
      await router.navigate({ to: safePath });
    },
  });

  return (
    <Card className="w-full max-w-sm">
      <CardHeader>
        <CardTitle>Choose your display name</CardTitle>
      </CardHeader>
      <CardContent>
        <Form {...form}>
          <form onSubmit={form.handleSubmit((v) => mutation.mutate(v))} className="space-y-4">
            <FormField
              control={form.control}
              name="display_name"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Display name</FormLabel>
                  <FormControl>
                    <Input placeholder="Display name" maxLength={50} {...field} />
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />
            {mutation.isError && <p className="text-sm text-destructive">Something went wrong. Please try again.</p>}
            <Button type="submit" className="w-full" disabled={mutation.isPending}>
              {mutation.isPending ? "Saving…" : "Continue"}
            </Button>
          </form>
        </Form>
      </CardContent>
    </Card>
  );
}
