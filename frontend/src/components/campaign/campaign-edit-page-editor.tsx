import { zodResolver } from "@hookform/resolvers/zod";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { Link, useRouter } from "@tanstack/react-router";
import { useForm } from "react-hook-form";
import { z } from "zod";
import type { CampaignResponse } from "@/api/generated";
import { patchCampaign } from "@/api/generated";
import { getCampaignQueryKey, listCampaignsQueryKey } from "@/api/generated/@tanstack/react-query.gen";
import { PageContainer } from "@/components/layout/page-container";
import { MarkdownEditor } from "@/components/markdown/markdown-editor";
import { Button } from "@/components/ui/button";
import { Form, FormControl, FormField, FormItem, FormLabel, FormMessage } from "@/components/ui/form";
import { Input } from "@/components/ui/input";
import { getErrorMessage } from "@/lib/utils";

const editorSchema = z.object({
  name: z.string().trim().min(1, "Name is required"),
  description: z.string(),
});

type EditorFormValues = z.infer<typeof editorSchema>;

interface CampaignEditPageEditorProps {
  campaign: CampaignResponse;
}

export function CampaignEditPageEditor({ campaign }: CampaignEditPageEditorProps) {
  const router = useRouter();
  const queryClient = useQueryClient();

  const form = useForm<EditorFormValues>({
    resolver: zodResolver(editorSchema),
    defaultValues: { name: campaign.name, description: campaign.description ?? "" },
  });

  const saveMutation = useMutation({
    mutationFn: async (values: EditorFormValues) => {
      const { data } = await patchCampaign({
        path: { slug: campaign.slug },
        body: {
          name: values.name.trim(),
          description: values.description.trim() || null,
        },
        throwOnError: true,
      });
      return data;
    },
    onSuccess: async (updated) => {
      await queryClient.invalidateQueries({ queryKey: listCampaignsQueryKey() });
      await queryClient.invalidateQueries({ queryKey: getCampaignQueryKey({ path: { slug: campaign.slug } }) });
      await router.navigate({ to: "/campaigns/$slug", params: { slug: updated.slug } });
    },
  });

  return (
    <PageContainer className="flex min-h-[calc(100vh-3.5rem)] w-full flex-col">
      <Link
        to="/campaigns/$slug"
        params={{ slug: campaign.slug }}
        className="mb-6 inline-block text-sm text-muted-foreground hover:text-foreground"
      >
        ← Back to Campaign
      </Link>

      <div className="mb-6">
        <h1 className="text-3xl font-bold">Edit Campaign</h1>
      </div>

      <Form {...form}>
        <form
          onSubmit={form.handleSubmit((values) => saveMutation.mutate(values))}
          className="flex min-h-0 flex-1 flex-col gap-6"
        >
          <FormField
            control={form.control}
            name="name"
            render={({ field }) => (
              <FormItem>
                <FormLabel>Name</FormLabel>
                <FormControl>
                  <Input {...field} autoFocus />
                </FormControl>
                <FormMessage />
              </FormItem>
            )}
          />

          <FormField
            control={form.control}
            name="description"
            render={({ field }) => (
              <FormItem className="flex min-h-0 flex-1 flex-col gap-2 space-y-0">
                <FormLabel>Description</FormLabel>
                <FormControl>
                  <MarkdownEditor
                    value={field.value}
                    onChange={field.onChange}
                    campaignSlug={campaign.slug}
                    className="flex min-h-0 flex-1 flex-col"
                    textareaClassName="min-h-[16rem] flex-1 leading-7"
                  />
                </FormControl>
                <FormMessage />
              </FormItem>
            )}
          />

          {saveMutation.isError && (
            <p className="text-sm text-destructive">
              {getErrorMessage(saveMutation.error, "Failed to save campaign.")}
            </p>
          )}

          <div className="flex items-center justify-end gap-2">
            <Button type="button" variant="ghost" asChild>
              <Link to="/campaigns/$slug" params={{ slug: campaign.slug }}>
                Cancel
              </Link>
            </Button>
            <Button type="submit" disabled={saveMutation.isPending}>
              {saveMutation.isPending ? "Saving…" : "Save"}
            </Button>
          </div>
        </form>
      </Form>
    </PageContainer>
  );
}
