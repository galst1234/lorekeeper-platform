import { zodResolver } from "@hookform/resolvers/zod";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { Link, useRouter } from "@tanstack/react-router";
import { useEffect, useMemo, useState } from "react";
import { useForm } from "react-hook-form";
import { z } from "zod";
import type { LocationResponse } from "@/api/generated";
import { createLocation, patchLocation } from "@/api/generated";
import { getLocationQueryKey, listLocationsQueryKey } from "@/api/generated/@tanstack/react-query.gen";
import { PageContainer } from "@/components/layout/page-container";
import { MarkdownEditor } from "@/components/markdown/markdown-editor";
import { Button } from "@/components/ui/button";
import { Form, FormControl, FormField, FormItem, FormLabel, FormMessage } from "@/components/ui/form";
import { Input } from "@/components/ui/input";
import { Switch } from "@/components/ui/switch";
import { Textarea } from "@/components/ui/textarea";
import { cn, getErrorMessage } from "@/lib/utils";

type LocationPageEditorProps =
  | { mode: "create"; campaignSlug: string }
  | { mode: "edit"; campaignSlug: string; location: LocationResponse };

function toLocationSlug(name: string): string {
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
    .max(100, "Slug must be at most 100 characters")
    .regex(/^[a-z0-9]+(-[a-z0-9]+)*$/, "Slug must be lowercase letters, numbers, and hyphens")
    .refine((value) => value !== "new", '"new" is a reserved slug'),
  description: z.string(),
  notes: z.string(),
  is_active: z.boolean(),
});

type EditorFormValues = z.infer<typeof editorSchema>;

function createDefaultValues(): EditorFormValues {
  return { name: "", slug: "", description: "", notes: "", is_active: true };
}

function editDefaultValues(location: LocationResponse): EditorFormValues {
  return {
    name: location.name,
    slug: location.slug,
    description: location.description ?? "",
    notes: location.notes ?? "",
    is_active: location.is_active,
  };
}

export function LocationPageEditor(props: LocationPageEditorProps) {
  const { campaignSlug, mode } = props;
  const location = mode === "edit" ? props.location : null;
  const router = useRouter();
  const queryClient = useQueryClient();
  const [slugEdited, setSlugEdited] = useState(false);

  const defaultValues = useMemo(() => (location ? editDefaultValues(location) : createDefaultValues()), [location]);

  const form = useForm<EditorFormValues>({
    resolver: zodResolver(editorSchema),
    defaultValues,
  });

  const nameValue = form.watch("name");

  useEffect(() => {
    if (mode === "create" && !slugEdited) {
      form.setValue("slug", toLocationSlug(nameValue), { shouldValidate: false });
    }
  }, [nameValue, slugEdited, form, mode]);

  const saveMutation = useMutation({
    mutationFn: async (values: EditorFormValues) => {
      if (location) {
        const { data } = await patchLocation({
          path: { slug: campaignSlug, location_slug: location.slug },
          body: {
            name: values.name.trim(),
            description: values.description.trim() || null,
            notes: values.notes.trim() || null,
            is_active: values.is_active,
          },
          throwOnError: true,
        });
        return data;
      }

      const { data } = await createLocation({
        path: { slug: campaignSlug },
        body: {
          name: values.name.trim(),
          slug: values.slug.trim(),
          description: values.description.trim() || undefined,
          notes: values.notes.trim() || undefined,
          is_active: values.is_active,
        },
        throwOnError: true,
      });
      return data;
    },
    onSuccess: async (savedLocation) => {
      await queryClient.invalidateQueries({
        queryKey: listLocationsQueryKey({ path: { slug: campaignSlug } }),
      });
      if (location) {
        await queryClient.invalidateQueries({
          queryKey: getLocationQueryKey({
            path: { slug: campaignSlug, location_slug: location.slug },
          }),
        });
      }
      await router.navigate({
        to: "/campaigns/$slug/locations/$locationSlug",
        params: { slug: campaignSlug, locationSlug: savedLocation.slug },
      });
    },
  });

  const isEditing = mode === "edit";

  return (
    <PageContainer className="flex min-h-[calc(100vh-3.5rem)] w-full flex-col">
      {location ? (
        <Link
          to="/campaigns/$slug/locations/$locationSlug"
          params={{ slug: campaignSlug, locationSlug: location.slug }}
          className="mb-6 inline-block text-sm text-muted-foreground hover:text-foreground"
        >
          ← Back to Location
        </Link>
      ) : (
        <Link
          to="/campaigns/$slug/locations"
          params={{ slug: campaignSlug }}
          className="mb-6 inline-block text-sm text-muted-foreground hover:text-foreground"
        >
          ← Back to Locations
        </Link>
      )}

      <div className="mb-6">
        <h1 className="text-3xl font-bold">{isEditing ? "Edit Location" : "Create Location"}</h1>
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

          <FormField
            control={form.control}
            name="notes"
            render={({ field }) => (
              <FormItem>
                <FormLabel>Notes</FormLabel>
                <FormControl>
                  <Textarea {...field} rows={4} placeholder="Private notes (plain text only)" />
                </FormControl>
                <FormMessage />
              </FormItem>
            )}
          />

          <FormField
            control={form.control}
            name="is_active"
            render={({ field }) => (
              <FormItem className="flex items-center gap-3">
                <FormControl>
                  <Switch checked={field.value} onCheckedChange={field.onChange} />
                </FormControl>
                <FormLabel className="!mt-0">Active</FormLabel>
                <FormMessage />
              </FormItem>
            )}
          />

          {saveMutation.isError && (
            <p className="text-sm text-destructive">
              {getErrorMessage(saveMutation.error, "Failed to save location.")}
            </p>
          )}

          <div className="flex items-center justify-end gap-2">
            <Button type="button" variant="ghost" asChild>
              {location ? (
                <Link
                  to="/campaigns/$slug/locations/$locationSlug"
                  params={{ slug: campaignSlug, locationSlug: location.slug }}
                >
                  Cancel
                </Link>
              ) : (
                <Link to="/campaigns/$slug/locations" params={{ slug: campaignSlug }}>
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
