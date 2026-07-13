import { zodResolver } from "@hookform/resolvers/zod";
import { useMutation, useQueryClient, useSuspenseQuery } from "@tanstack/react-query";
import { Link, useRouter } from "@tanstack/react-router";
import { User } from "lucide-react";
import { useEffect, useMemo, useState } from "react";
import { useForm } from "react-hook-form";
import { z } from "zod";
import type { CharacterResponse } from "@/api/generated";
import { createCharacter, deleteCharacterImage, patchCharacter, uploadCharacterImage } from "@/api/generated";
import {
  getCampaignOptions,
  getCharacterQueryKey,
  listCampaignTagsOptions,
  listCharactersQueryKey,
} from "@/api/generated/@tanstack/react-query.gen";
import { EntityImageField } from "@/components/image/entity-image-field";
import { PageContainer } from "@/components/layout/page-container";
import { MarkdownEditor } from "@/components/markdown/markdown-editor";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Form, FormControl, FormField, FormItem, FormLabel, FormMessage } from "@/components/ui/form";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { TagInput } from "@/components/ui/tag-input";
import { cn, getErrorMessage } from "@/lib/utils";

type CharacterPageEditorProps =
  | { mode: "create"; campaignSlug: string }
  | { mode: "edit"; campaignSlug: string; character: CharacterResponse };

function toCharacterSlug(name: string): string {
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
  character_type: z.enum(["pc", "npc"]),
  description: z.string(),
  access: z.enum(["everyone", "gm_only"]),
  tags: z.array(z.string()),
});

type EditorFormValues = z.infer<typeof editorSchema>;

function createDefaultValues(): EditorFormValues {
  return { name: "", slug: "", character_type: "npc", description: "", access: "everyone", tags: [] };
}

function editDefaultValues(character: CharacterResponse): EditorFormValues {
  return {
    name: character.name,
    slug: character.slug,
    character_type: character.character_type,
    description: character.description ?? "",
    access: character.restricted ? "gm_only" : "everyone",
    tags: character.tags,
  };
}

export function CharacterPageEditor(props: CharacterPageEditorProps) {
  const { campaignSlug, mode } = props;
  const character = mode === "edit" ? props.character : null;
  const router = useRouter();
  const queryClient = useQueryClient();
  const [slugEdited, setSlugEdited] = useState(false);
  const [pendingImageFile, setPendingImageFile] = useState<File | null>(null);
  const [imageRemoved, setImageRemoved] = useState(false);
  const { data: campaign } = useSuspenseQuery(getCampaignOptions({ path: { slug: campaignSlug } }));
  const { data: campaignTags } = useSuspenseQuery(listCampaignTagsOptions({ path: { slug: campaignSlug } }));
  const isGm = campaign.role === "gm";

  const defaultValues = useMemo(() => (character ? editDefaultValues(character) : createDefaultValues()), [character]);

  const form = useForm<EditorFormValues>({
    resolver: zodResolver(editorSchema),
    defaultValues,
  });

  const nameValue = form.watch("name");

  useEffect(() => {
    if (mode === "create" && !slugEdited) {
      form.setValue("slug", toCharacterSlug(nameValue), { shouldValidate: false });
    }
  }, [nameValue, slugEdited, form, mode]);

  const saveMutation = useMutation({
    mutationFn: async (values: EditorFormValues) => {
      const savedCharacter = character
        ? (
            await patchCharacter({
              path: { slug: campaignSlug, character_slug: character.slug },
              body: {
                name: values.name.trim(),
                character_type: values.character_type,
                description: values.description.trim() || null,
                restricted: values.access === "gm_only",
                tags: values.tags,
              },
              throwOnError: true,
            })
          ).data
        : (
            await createCharacter({
              path: { slug: campaignSlug },
              body: {
                name: values.name.trim(),
                slug: values.slug.trim(),
                character_type: values.character_type,
                description: values.description.trim() || undefined,
                restricted: values.access === "gm_only",
                tags: values.tags,
              },
              throwOnError: true,
            })
          ).data;

      try {
        if (pendingImageFile) {
          await uploadCharacterImage({
            path: { slug: campaignSlug, character_slug: savedCharacter.slug },
            body: { file: pendingImageFile },
            throwOnError: true,
          });
        } else if (imageRemoved) {
          await deleteCharacterImage({
            path: { slug: campaignSlug, character_slug: savedCharacter.slug },
            throwOnError: true,
          });
        }
        return { savedCharacter, imageUploadFailed: false };
      } catch {
        return { savedCharacter, imageUploadFailed: true };
      }
    },
    onSuccess: async ({ savedCharacter, imageUploadFailed }) => {
      await queryClient.invalidateQueries({ queryKey: listCharactersQueryKey({ path: { slug: campaignSlug } }) });
      if (character) {
        await queryClient.invalidateQueries({
          queryKey: getCharacterQueryKey({ path: { slug: campaignSlug, character_slug: character.slug } }),
        });
      }
      await router.navigate({
        to: "/campaigns/$slug/characters/$characterSlug",
        params: { slug: campaignSlug, characterSlug: savedCharacter.slug },
        state: imageUploadFailed ? { imageUploadFailed: true } : undefined,
      });
    },
  });

  const isEditing = mode === "edit";

  return (
    <PageContainer className="flex min-h-[calc(100vh-3.5rem)] w-full flex-col">
      {character ? (
        <Link
          to="/campaigns/$slug/characters/$characterSlug"
          params={{ slug: campaignSlug, characterSlug: character.slug }}
          className="mb-6 inline-block text-sm text-muted-foreground hover:text-foreground"
        >
          ← Back to Character
        </Link>
      ) : (
        <Link
          to="/campaigns/$slug/characters"
          params={{ slug: campaignSlug }}
          className="mb-6 inline-block text-sm text-muted-foreground hover:text-foreground"
        >
          ← Back to Characters
        </Link>
      )}

      <div className="mb-6">
        <h1 className="text-3xl font-bold">{isEditing ? "Edit Character" : "Create Character"}</h1>
      </div>

      <Form {...form}>
        <form
          onSubmit={form.handleSubmit((values) => saveMutation.mutate(values))}
          className="flex min-h-0 flex-1 flex-col gap-6"
        >
          <div className="grid min-h-0 flex-1 grid-cols-1 gap-8 md:grid-cols-3">
            <div className="flex min-h-0 flex-col gap-6 md:col-span-2">
              <div
                className={cn("grid grid-cols-1 gap-4 content-start", isEditing ? "md:grid-cols-2" : "md:grid-cols-3")}
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
                  name="character_type"
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel>Type</FormLabel>
                      <Select onValueChange={field.onChange} value={field.value}>
                        <FormControl>
                          <SelectTrigger>
                            <SelectValue />
                          </SelectTrigger>
                        </FormControl>
                        <SelectContent>
                          <SelectItem value="pc">PC</SelectItem>
                          <SelectItem value="npc">NPC</SelectItem>
                        </SelectContent>
                      </Select>
                      <FormMessage />
                    </FormItem>
                  )}
                />
                {isGm && (
                  <FormField
                    control={form.control}
                    name="access"
                    render={({ field }) => (
                      <FormItem>
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
            </div>

            <div className="sticky top-6 space-y-2">
              <Label>Image</Label>
              <Card>
                <CardContent className="pt-6 space-y-4">
                  <EntityImageField
                    imageUrl={imageRemoved ? null : (character?.image_url ?? null)}
                    placeholderIcon={User}
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

          {saveMutation.isError && (
            <p className="text-sm text-destructive">
              {getErrorMessage(saveMutation.error, "Failed to save character.")}
            </p>
          )}

          <div className="flex items-center justify-end gap-2">
            <Button type="button" variant="ghost" asChild>
              {character ? (
                <Link
                  to="/campaigns/$slug/characters/$characterSlug"
                  params={{ slug: campaignSlug, characterSlug: character.slug }}
                >
                  Cancel
                </Link>
              ) : (
                <Link to="/campaigns/$slug/characters" params={{ slug: campaignSlug }}>
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
