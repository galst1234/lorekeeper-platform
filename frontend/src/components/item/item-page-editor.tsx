import { zodResolver } from "@hookform/resolvers/zod";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { Link, useRouter } from "@tanstack/react-router";
import { useEffect, useMemo, useState } from "react";
import { useForm } from "react-hook-form";
import { z } from "zod";
import type { ItemResponse } from "@/api/generated";
import { createItem, patchItem } from "@/api/generated";
import { getItemQueryKey, listItemsQueryKey } from "@/api/generated/@tanstack/react-query.gen";
import { PageContainer } from "@/components/layout/page-container";
import { MarkdownEditor } from "@/components/markdown/markdown-editor";
import { Button } from "@/components/ui/button";
import { Form, FormControl, FormField, FormItem, FormLabel, FormMessage } from "@/components/ui/form";
import { Input } from "@/components/ui/input";
import { cn, getErrorMessage } from "@/lib/utils";

type ItemPageEditorProps =
  | { mode: "create"; campaignSlug: string }
  | { mode: "edit"; campaignSlug: string; item: ItemResponse };

function toItemSlug(name: string): string {
  return name
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, "-")
    .replace(/^-+|-+$/g, "");
}

const editorSchema = z.object({
  name: z.string().trim().min(1, "Name is required"),
  slug: z
    .string()
    .trim()
    .min(1, "Slug is required")
    .regex(/^[a-z0-9]+(-[a-z0-9]+)*$/, "Slug must be lowercase letters, numbers, and hyphens")
    .refine((value) => value !== "new", '"new" is a reserved slug'),
  description: z.string(),
});

type EditorFormValues = z.infer<typeof editorSchema>;

function createDefaultValues(): EditorFormValues {
  return { name: "", slug: "", description: "" };
}

function editDefaultValues(item: ItemResponse): EditorFormValues {
  return { name: item.name, slug: item.slug, description: item.description ?? "" };
}

export function ItemPageEditor(props: ItemPageEditorProps) {
  const { campaignSlug, mode } = props;
  const item = mode === "edit" ? props.item : null;
  const router = useRouter();
  const queryClient = useQueryClient();
  const [slugEdited, setSlugEdited] = useState(false);

  const defaultValues = useMemo(() => (item ? editDefaultValues(item) : createDefaultValues()), [item]);

  const form = useForm<EditorFormValues>({
    resolver: zodResolver(editorSchema),
    defaultValues,
  });

  const nameValue = form.watch("name");

  useEffect(() => {
    if (mode === "create" && !slugEdited) {
      form.setValue("slug", toItemSlug(nameValue), { shouldValidate: false });
    }
  }, [nameValue, slugEdited, form, mode]);

  const saveMutation = useMutation({
    mutationFn: async (values: EditorFormValues) => {
      if (item) {
        const { data } = await patchItem({
          path: { slug: campaignSlug, item_slug: item.slug },
          body: {
            name: values.name.trim(),
            description: values.description.trim() || null,
          },
          throwOnError: true,
        });
        return data;
      }

      const { data } = await createItem({
        path: { slug: campaignSlug },
        body: {
          name: values.name.trim(),
          slug: values.slug.trim(),
          description: values.description.trim() || undefined,
        },
        throwOnError: true,
      });
      return data;
    },
    onSuccess: async (savedItem) => {
      await queryClient.invalidateQueries({ queryKey: listItemsQueryKey({ path: { slug: campaignSlug } }) });
      if (item) {
        await queryClient.invalidateQueries({
          queryKey: getItemQueryKey({ path: { slug: campaignSlug, item_slug: item.slug } }),
        });
      }
      await router.navigate({
        to: "/campaigns/$slug/items/$itemSlug",
        params: { slug: campaignSlug, itemSlug: savedItem.slug },
      });
    },
  });

  const isEditing = mode === "edit";

  return (
    <PageContainer className="flex min-h-[calc(100vh-3.5rem)] w-full flex-col">
      {item ? (
        <Link
          to="/campaigns/$slug/items/$itemSlug"
          params={{ slug: campaignSlug, itemSlug: item.slug }}
          className="mb-6 inline-block text-sm text-muted-foreground hover:text-foreground"
        >
          ← Back to Item
        </Link>
      ) : (
        <Link
          to="/campaigns/$slug/items"
          params={{ slug: campaignSlug }}
          className="mb-6 inline-block text-sm text-muted-foreground hover:text-foreground"
        >
          ← Back to Items
        </Link>
      )}

      <div className="mb-6">
        <h1 className="text-3xl font-bold">{isEditing ? "Edit Item" : "Create Item"}</h1>
      </div>

      <Form {...form}>
        <form
          onSubmit={form.handleSubmit((values) => saveMutation.mutate(values))}
          className="flex min-h-0 flex-1 flex-col gap-6"
        >
          <div className={cn("grid grid-cols-1 gap-4", !isEditing && "md:grid-cols-2")}>
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
          </div>

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
                    campaignSlug={campaignSlug}
                    className="flex min-h-0 flex-1 flex-col"
                    textareaClassName="min-h-[16rem] flex-1 leading-7"
                  />
                </FormControl>
                <FormMessage />
              </FormItem>
            )}
          />

          {saveMutation.isError && (
            <p className="text-sm text-destructive">{getErrorMessage(saveMutation.error, "Failed to save item.")}</p>
          )}

          <div className="flex items-center justify-end gap-2">
            <Button type="button" variant="ghost" asChild>
              {item ? (
                <Link to="/campaigns/$slug/items/$itemSlug" params={{ slug: campaignSlug, itemSlug: item.slug }}>
                  Cancel
                </Link>
              ) : (
                <Link to="/campaigns/$slug/items" params={{ slug: campaignSlug }}>
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
