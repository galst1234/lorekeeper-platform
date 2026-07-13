import { zodResolver } from "@hookform/resolvers/zod";
import { useMutation, useQueryClient, useSuspenseQuery } from "@tanstack/react-query";
import { Link, useRouter } from "@tanstack/react-router";
import { useEffect, useMemo, useState } from "react";
import { useForm } from "react-hook-form";
import { z } from "zod";
import type { ChronicleEntryDetailResponse } from "@/api/generated";
import { createChronicleEntry, patchChronicleEntry } from "@/api/generated";
import {
  getCampaignOptions,
  getChronicleEntryQueryKey,
  listCampaignTagsOptions,
  listChronicleEntriesQueryKey,
} from "@/api/generated/@tanstack/react-query.gen";
import { PageContainer } from "@/components/layout/page-container";
import { MarkdownEditor } from "@/components/markdown/markdown-editor";
import { Button } from "@/components/ui/button";
import { DateTimePicker } from "@/components/ui/datetime-picker";
import { Form, FormControl, FormField, FormItem, FormLabel, FormMessage } from "@/components/ui/form";
import { Input } from "@/components/ui/input";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { TagInput } from "@/components/ui/tag-input";
import { datetimeLocalToIso, toDatetimeLocalValue } from "@/lib/datetime";
import { getErrorMessage } from "@/lib/utils";

type ChronicleEntryPageEditorProps =
  | {
      mode: "create";
      campaignSlug: string;
    }
  | {
      mode: "edit";
      campaignSlug: string;
      entry: ChronicleEntryDetailResponse;
    };

function toEntrySlug(title: string): string {
  return title
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, "-")
    .replace(/^-+|-+$/g, "");
}

const editorSchema = z.object({
  title: z.string().trim().min(1, "Title is required"),
  slug: z
    .string()
    .trim()
    .min(1, "Slug is required")
    .regex(/^[a-z0-9]+(-[a-z0-9]+)*$/, "Slug must be lowercase letters, numbers, and hyphens")
    .refine((value) => value !== "new", '"new" is a reserved slug'),
  occurredAt: z.string().min(1, "Session date is required"),
  body: z.string(),
  access: z.enum(["everyone", "gm_only"]),
  tags: z.array(z.string()),
});

type EditorFormValues = z.infer<typeof editorSchema>;

function createDefaultValues(): EditorFormValues {
  return {
    title: "",
    slug: "",
    occurredAt: toDatetimeLocalValue(new Date()),
    body: "",
    access: "everyone",
    tags: [],
  };
}

function editDefaultValues(entry: ChronicleEntryDetailResponse): EditorFormValues {
  return {
    title: entry.title,
    slug: entry.slug,
    occurredAt: toDatetimeLocalValue(new Date(entry.occurred_at)),
    body: entry.body ?? "",
    access: entry.restricted ? "gm_only" : "everyone",
    tags: entry.tags,
  };
}

export function ChronicleEntryPageEditor(props: ChronicleEntryPageEditorProps) {
  const { campaignSlug, mode } = props;
  const entry = mode === "edit" ? props.entry : null;
  const router = useRouter();
  const queryClient = useQueryClient();
  const [slugEdited, setSlugEdited] = useState(false);
  const { data: campaign } = useSuspenseQuery(getCampaignOptions({ path: { slug: campaignSlug } }));
  const { data: campaignTags } = useSuspenseQuery(listCampaignTagsOptions({ path: { slug: campaignSlug } }));
  const isGm = campaign.role === "gm";

  const defaultValues = useMemo(() => (entry ? editDefaultValues(entry) : createDefaultValues()), [entry]);

  const form = useForm<EditorFormValues>({
    resolver: zodResolver(editorSchema),
    defaultValues,
  });

  const titleValue = form.watch("title");

  useEffect(() => {
    if (mode === "create" && !slugEdited) {
      form.setValue("slug", toEntrySlug(titleValue), { shouldValidate: false });
    }
  }, [titleValue, slugEdited, form, mode]);

  const saveMutation = useMutation({
    mutationFn: async (values: EditorFormValues) => {
      if (entry) {
        const { data } = await patchChronicleEntry({
          path: { slug: campaignSlug, entry_slug: entry.slug },
          body: {
            title: values.title.trim(),
            occurred_at: datetimeLocalToIso(values.occurredAt),
            body: values.body.trim() || null,
            restricted: values.access === "gm_only",
            tags: values.tags,
          },
          throwOnError: true,
        });
        return data;
      }

      const { data } = await createChronicleEntry({
        path: { slug: campaignSlug },
        body: {
          title: values.title.trim(),
          slug: values.slug.trim(),
          occurred_at: datetimeLocalToIso(values.occurredAt),
          body: values.body.trim() || undefined,
          restricted: values.access === "gm_only",
          tags: values.tags,
        },
        throwOnError: true,
      });
      return data;
    },
    onSuccess: async (savedEntry) => {
      await queryClient.invalidateQueries({ queryKey: listChronicleEntriesQueryKey({ path: { slug: campaignSlug } }) });
      if (entry) {
        await queryClient.invalidateQueries({
          queryKey: getChronicleEntryQueryKey({ path: { slug: campaignSlug, entry_slug: entry.slug } }),
        });
      }
      await router.navigate({
        to: "/campaigns/$slug/chronicle/$entrySlug",
        params: { slug: campaignSlug, entrySlug: savedEntry.slug },
      });
    },
  });

  const isEditing = mode === "edit";

  return (
    <PageContainer className="flex min-h-[calc(100vh-3.5rem)] w-full flex-col">
      {entry ? (
        <Link
          to="/campaigns/$slug/chronicle/$entrySlug"
          params={{ slug: campaignSlug, entrySlug: entry.slug }}
          className="mb-6 inline-block text-sm text-muted-foreground hover:text-foreground"
        >
          ← Back to Entry
        </Link>
      ) : (
        <Link
          to="/campaigns/$slug/chronicle"
          params={{ slug: campaignSlug }}
          className="mb-6 inline-block text-sm text-muted-foreground hover:text-foreground"
        >
          ← Back to Chronicle
        </Link>
      )}

      <div className="mb-6">
        <h1 className="text-3xl font-bold">{isEditing ? "Edit Chronicle Entry" : "Create Chronicle Entry"}</h1>
      </div>

      <Form {...form}>
        <form
          onSubmit={form.handleSubmit((values) => saveMutation.mutate(values))}
          className="flex min-h-0 flex-1 flex-col gap-6"
        >
          <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
            <FormField
              control={form.control}
              name="title"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Title</FormLabel>
                  <FormControl>
                    <Input {...field} autoFocus />
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />
            <FormField
              control={form.control}
              name="occurredAt"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Session date and time</FormLabel>
                  <FormControl>
                    <DateTimePicker {...field} />
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />
          </div>

          {isGm && (
            <FormField
              control={form.control}
              name="access"
              render={({ field }) => (
                <FormItem className="md:w-1/3">
                  <FormLabel>Access</FormLabel>
                  <Select onValueChange={field.onChange} value={field.value}>
                    <FormControl>
                      <SelectTrigger>
                        <SelectValue />
                      </SelectTrigger>
                    </FormControl>
                    <SelectContent>
                      <SelectItem value="everyone">Everyone</SelectItem>
                      <SelectItem value="gm_only">GM Only</SelectItem>
                    </SelectContent>
                  </Select>
                  <FormMessage />
                </FormItem>
              )}
            />
          )}

          {!isEditing && (
            <FormField
              control={form.control}
              name="slug"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Slug</FormLabel>
                  <FormControl>
                    <Input
                      {...field}
                      onChange={(event) => {
                        setSlugEdited(true);
                        field.onChange(event);
                      }}
                    />
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />
          )}

          <FormField
            control={form.control}
            name="body"
            render={({ field }) => (
              <FormItem className="flex min-h-0 flex-1 flex-col gap-2 space-y-0">
                <FormLabel>Content</FormLabel>
                <FormControl>
                  <MarkdownEditor
                    value={field.value}
                    onChange={field.onChange}
                    campaignSlug={campaignSlug}
                    className="flex min-h-0 flex-1 flex-col"
                    textareaClassName="min-h-[16rem] flex-1 leading-7"
                  />
                </FormControl>
                <FormMessage />
              </FormItem>
            )}
          />

          <FormField
            control={form.control}
            name="tags"
            render={({ field }) => (
              <FormItem>
                <FormLabel>Tags</FormLabel>
                <FormControl>
                  <TagInput
                    value={field.value}
                    onChange={field.onChange}
                    suggestions={campaignTags.tags}
                    placeholder="Add a tag…"
                    aria-label="Tags"
                  />
                </FormControl>
                <FormMessage />
              </FormItem>
            )}
          />

          {saveMutation.isError && (
            <p className="text-sm text-destructive">{getErrorMessage(saveMutation.error, "Failed to save entry.")}</p>
          )}

          <div className="flex items-center justify-end gap-2">
            <Button type="button" variant="ghost" asChild>
              {entry ? (
                <Link to="/campaigns/$slug/chronicle/$entrySlug" params={{ slug: campaignSlug, entrySlug: entry.slug }}>
                  Cancel
                </Link>
              ) : (
                <Link to="/campaigns/$slug/chronicle" params={{ slug: campaignSlug }}>
                  Cancel
                </Link>
              )}
            </Button>
            <Button type="submit" variant="create" disabled={saveMutation.isPending}>
              {saveMutation.isPending ? "Saving..." : isEditing ? "Save" : "Create"}
            </Button>
          </div>
        </form>
      </Form>
    </PageContainer>
  );
}
