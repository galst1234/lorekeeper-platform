import { zodResolver } from "@hookform/resolvers/zod";
import { useMutation, useQueryClient, useSuspenseQuery } from "@tanstack/react-query";
import { Link } from "@tanstack/react-router";
import { ChevronRight } from "lucide-react";
import { useEffect, useState } from "react";
import { useForm } from "react-hook-form";
import { z } from "zod";
import { charactersQueryOptions, createCharacter } from "@/api/characters";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Dialog, DialogContent, DialogFooter, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { Form, FormControl, FormField, FormItem, FormLabel, FormMessage } from "@/components/ui/form";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";

function toCharacterSlug(name: string): string {
  return name
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, "-")
    .replace(/^-+|-+$/g, "");
}

const addSchema = z.object({
  name: z.string().trim().min(1, "Name is required"),
  slug: z
    .string()
    .trim()
    .min(1, "Slug is required")
    .regex(/^[a-z0-9]+(-[a-z0-9]+)*$/, "Slug must be lowercase letters, numbers, and hyphens"),
  character_type: z.enum(["pc", "npc"]),
  description: z.string(),
});

type AddFormValues = z.infer<typeof addSchema>;

interface CharactersSectionProps {
  slug: string;
  characterType: "pc" | "npc";
}

export function CharactersSection({ slug, characterType }: CharactersSectionProps) {
  const queryClient = useQueryClient();
  const [addOpen, setAddOpen] = useState(false);
  const [slugEdited, setSlugEdited] = useState(false);
  const { data: characters } = useSuspenseQuery(charactersQueryOptions(slug));

  const filtered = characters.filter((c) => c.character_type === characterType);
  const title = characterType === "pc" ? "Player Characters" : "NPCs";
  const emptyText = characterType === "pc" ? "No player characters yet." : "No NPCs yet.";

  const addForm = useForm<AddFormValues>({
    resolver: zodResolver(addSchema),
    defaultValues: { name: "", slug: "", character_type: characterType, description: "" },
  });

  const nameValue = addForm.watch("name");

  useEffect(() => {
    if (!slugEdited) {
      addForm.setValue("slug", toCharacterSlug(nameValue), { shouldValidate: false });
    }
  }, [nameValue, slugEdited, addForm]);

  const createMutation = useMutation({
    mutationFn: (values: AddFormValues) =>
      createCharacter(slug, {
        name: values.name.trim(),
        slug: values.slug.trim(),
        character_type: values.character_type,
        description: values.description.trim() || undefined,
      }),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ["characters", slug] });
      setAddOpen(false);
      setSlugEdited(false);
      addForm.reset();
    },
  });

  function closeAdd() {
    setAddOpen(false);
    setSlugEdited(false);
    addForm.reset();
  }

  return (
    <div>
      <div className="flex items-center justify-between mb-3">
        <h2 className="text-lg font-semibold">{title}</h2>
        <Button size="sm" onClick={() => setAddOpen(true)}>
          + Create {characterType === "pc" ? "Player Character" : "NPC"}
        </Button>
      </div>

      {filtered.length === 0 ? (
        <p className="text-sm text-muted-foreground italic">{emptyText}</p>
      ) : (
        <div className="space-y-2">
          {filtered.map((character) => (
            <Card key={character.id} className="px-4 py-3">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <Link
                    to="/campaigns/$slug/characters/$characterSlug"
                    params={{ slug, characterSlug: character.slug }}
                    className="font-medium hover:underline"
                  >
                    {character.name}
                  </Link>
                  <Badge variant="secondary" className="text-xs">
                    {character.character_type.toUpperCase()}
                  </Badge>
                </div>
                <ChevronRight className="h-4 w-4 text-muted-foreground" />
              </div>
            </Card>
          ))}
        </div>
      )}

      <Dialog open={addOpen} onOpenChange={(open) => (open ? setAddOpen(true) : closeAdd())}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Create {characterType === "pc" ? "Player Character" : "NPC"}</DialogTitle>
          </DialogHeader>
          <Form {...addForm}>
            <form
              onSubmit={addForm.handleSubmit((v) => createMutation.mutate(v))}
              onKeyDown={(e) => {
                if (e.key === "Enter" && e.ctrlKey) {
                  e.preventDefault();
                  addForm.handleSubmit((v) => createMutation.mutate(v))();
                }
              }}
              className="space-y-4"
            >
              <FormField
                control={addForm.control}
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
                control={addForm.control}
                name="slug"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Slug</FormLabel>
                    <FormControl>
                      <Input
                        {...field}
                        onChange={(e) => {
                          setSlugEdited(true);
                          field.onChange(e);
                        }}
                      />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />
              <FormField
                control={addForm.control}
                name="description"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Description</FormLabel>
                    <FormControl>
                      <Textarea rows={2} {...field} />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />
              {createMutation.isError && (
                <p className="text-sm text-destructive">
                  {createMutation.error instanceof Error ? createMutation.error.message : "Failed to create character."}
                </p>
              )}
              <DialogFooter>
                <Button type="button" variant="ghost" onClick={closeAdd} disabled={createMutation.isPending}>
                  Cancel
                </Button>
                <Button type="submit" disabled={createMutation.isPending}>
                  {createMutation.isPending ? "Creating…" : "Create"}
                </Button>
              </DialogFooter>
            </form>
          </Form>
        </DialogContent>
      </Dialog>
    </div>
  );
}
