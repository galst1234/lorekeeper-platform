import { zodResolver } from "@hookform/resolvers/zod";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { Link, useRouter } from "@tanstack/react-router";
import { useEffect, useState } from "react";
import { useForm } from "react-hook-form";
import { z } from "zod";
import { createCampaignMutation, listCampaignsQueryKey } from "@/api/generated/@tanstack/react-query.gen";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from "@/components/ui/card";
import { Form, FormControl, FormDescription, FormField, FormItem, FormLabel, FormMessage } from "@/components/ui/form";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { toSlugLabel } from "@/lib/utils";

const createSchema = z.object({
  name: z.string().trim().min(1, "Name is required"),
  slug_label: z
    .string()
    .trim()
    .min(1, "URL slug is required")
    .max(100, "URL slug must be 100 characters or fewer")
    .regex(
      /^[a-z0-9]+(-[a-z0-9]+)*$/,
      "Slug may only contain lowercase letters, numbers, and hyphens, and cannot start or end with a hyphen"
    ),
  description: z.string(),
});

type CreateFormValues = z.infer<typeof createSchema>;

export function CreateCampaignForm() {
  const router = useRouter();
  const queryClient = useQueryClient();
  const [slugEdited, setSlugEdited] = useState(false);

  const form = useForm<CreateFormValues>({
    resolver: zodResolver(createSchema),
    defaultValues: { name: "", slug_label: "", description: "" },
  });

  const nameValue = form.watch("name");

  useEffect(() => {
    if (!slugEdited) {
      form.setValue("slug_label", toSlugLabel(nameValue), { shouldValidate: false });
    }
  }, [nameValue, slugEdited, form]);

  const mutation = useMutation({
    ...createCampaignMutation(),
    onSuccess: async (campaign) => {
      await queryClient.invalidateQueries({ queryKey: listCampaignsQueryKey() });
      await router.navigate({ to: "/campaigns/$slug", params: { slug: campaign.slug } });
    },
  });

  return (
    <Card className="w-full max-w-lg">
      <CardHeader>
        <CardTitle>Create Campaign</CardTitle>
        <CardDescription>Set up a new campaign for your group.</CardDescription>
      </CardHeader>
      <Form {...form}>
        <form
          onSubmit={form.handleSubmit((v) =>
            mutation.mutate({
              body: {
                name: v.name.trim(),
                slug_label: v.slug_label.trim(),
                description: v.description.trim() || undefined,
              },
            })
          )}
        >
          <CardContent className="space-y-4">
            <FormField
              control={form.control}
              name="name"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Name</FormLabel>
                  <FormControl>
                    <Input {...field} />
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />
            <FormField
              control={form.control}
              name="slug_label"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>URL Slug</FormLabel>
                  <FormControl>
                    <Input
                      {...field}
                      onChange={(e) => {
                        setSlugEdited(true);
                        field.onChange(e);
                      }}
                    />
                  </FormControl>
                  <FormDescription>
                    A unique suffix will be appended — e.g. <code>{field.value || "my-campaign"}-xxxxxxxx</code>
                  </FormDescription>
                  <FormMessage />
                </FormItem>
              )}
            />
            <FormField
              control={form.control}
              name="description"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Description</FormLabel>
                  <FormControl>
                    <Textarea rows={3} {...field} />
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />
            {mutation.isError && <p className="text-sm text-destructive">Something went wrong. Please try again.</p>}
          </CardContent>
          <CardFooter className="flex gap-2 justify-end">
            <Button type="button" variant="ghost" asChild>
              <Link to="/">Cancel</Link>
            </Button>
            <Button type="submit" disabled={mutation.isPending}>
              {mutation.isPending ? "Creating…" : "Create Campaign"}
            </Button>
          </CardFooter>
        </form>
      </Form>
    </Card>
  );
}
