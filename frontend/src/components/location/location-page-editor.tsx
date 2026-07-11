import { zodResolver } from "@hookform/resolvers/zod";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { Link, useRouter } from "@tanstack/react-router";
import { MapPin } from "lucide-react";
import { useEffect, useMemo, useState } from "react";
import { useForm } from "react-hook-form";
import { z } from "zod";
import type { LocationResponse } from "@/api/generated";
import { createLocation, deleteLocationImage, patchLocation, uploadLocationImage } from "@/api/generated";
import { getLocationQueryKey, listLocationsQueryKey } from "@/api/generated/@tanstack/react-query.gen";
import { EntityImageField } from "@/components/image/entity-image-field";
import { PageContainer } from "@/components/layout/page-container";
import { MarkdownEditor } from "@/components/markdown/markdown-editor";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Form, FormControl, FormField, FormItem, FormLabel, FormMessage } from "@/components/ui/form";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { cn, getErrorDetail, getErrorMessage } from "@/lib/utils";

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
});

type EditorFormValues = z.infer<typeof editorSchema>;

function createDefaultValues(): EditorFormValues {
  return { name: "", slug: "", description: "" };
}

function isSlugConflictError(error: unknown): boolean {
  const detail = getErrorDetail(error);
  return detail?.toLowerCase().includes("slug") ?? false;
}

function editDefaultValues(location: LocationResponse): EditorFormValues {
  return {
    name: location.name,
    slug: location.slug,
    description: location.description ?? "",
  };
}

export function LocationPageEditor(props: LocationPageEditorProps) {
  const { campaignSlug, mode } = props;
  const location = mode === "edit" ? props.location : null;
  const router = useRouter();
  const queryClient = useQueryClient();
  const [slugEdited, setSlugEdited] = useState(false);
  const [pendingImageFile, setPendingImageFile] = useState<File | null>(null);
  const [imageRemoved, setImageRemoved] = useState(false);

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
      const savedLocation = location
        ? (
            await patchLocation({
              path: { slug: campaignSlug, location_slug: location.slug },
              body: {
                name: values.name.trim(),
                description: values.description.trim() || null,
              },
              throwOnError: true,
            })
          ).data
        : (
            await createLocation({
              path: { slug: campaignSlug },
              body: {
                name: values.name.trim(),
                slug: values.slug.trim(),
                description: values.description.trim() || undefined,
              },
              throwOnError: true,
            })
          ).data;

      try {
        if (pendingImageFile) {
          await uploadLocationImage({
            path: { slug: campaignSlug, location_slug: savedLocation.slug },
            body: { file: pendingImageFile },
            throwOnError: true,
          });
        } else if (imageRemoved) {
          await deleteLocationImage({
            path: { slug: campaignSlug, location_slug: savedLocation.slug },
            throwOnError: true,
          });
        }
        return { savedLocation, imageUploadFailed: false };
      } catch {
        return { savedLocation, imageUploadFailed: true };
      }
    },
    onSuccess: async ({ savedLocation, imageUploadFailed }) => {
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
        state: imageUploadFailed ? { imageUploadFailed: true } : undefined,
      });
    },
    onError: (error) => {
      if (mode === "create" && isSlugConflictError(error)) {
        form.setError("slug", {
          message: getErrorDetail(error) ?? "This slug is already in use",
        });
      }
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
          <div className="grid min-h-0 flex-1 grid-cols-1 gap-8 md:grid-cols-3">
            <div className="flex min-h-0 flex-col gap-6 md:col-span-2">
              <div className={cn("grid grid-cols-1 gap-4 content-start", !isEditing && "md:grid-cols-2")}>
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
            </div>

            <div className="sticky top-6 space-y-2">
              <Label>Image</Label>
              <Card>
                <CardContent className="pt-6 space-y-4">
                  <EntityImageField
                    imageUrl={imageRemoved ? null : (location?.image_url ?? null)}
                    placeholderIcon={MapPin}
                    onFileSelected={(file) => {
                      setPendingImageFile(file);
                      setImageRemoved(false);
                    }}
                    onRemove={() => {
                      setPendingImageFile(null);
                      setImageRemoved(true);
                    }}
                  />
                </CardContent>
              </Card>
            </div>
          </div>

          {saveMutation.isError && !form.formState.errors.slug && (
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
