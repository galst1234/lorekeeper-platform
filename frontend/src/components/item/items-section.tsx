import { zodResolver } from "@hookform/resolvers/zod";
import { useMutation, useQueryClient, useSuspenseQuery } from "@tanstack/react-query";
import { Link } from "@tanstack/react-router";
import { ChevronRight, Plus } from "lucide-react";
import { useEffect, useState } from "react";
import { useForm } from "react-hook-form";
import { z } from "zod";
import { createItem, itemsQueryOptions } from "@/api/items";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Dialog, DialogContent, DialogFooter, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { Form, FormControl, FormField, FormItem, FormLabel, FormMessage } from "@/components/ui/form";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";

function toItemSlug(name: string): string {
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
  description: z.string(),
});

type AddFormValues = z.infer<typeof addSchema>;

interface ItemsSectionProps {
  slug: string;
}

export function ItemsSection({ slug }: ItemsSectionProps) {
  const queryClient = useQueryClient();
  const [addOpen, setAddOpen] = useState(false);
  const [slugEdited, setSlugEdited] = useState(false);
  const { data: items } = useSuspenseQuery(itemsQueryOptions(slug));

  const addForm = useForm<AddFormValues>({
    resolver: zodResolver(addSchema),
    defaultValues: { name: "", slug: "", description: "" },
  });

  const nameValue = addForm.watch("name");

  useEffect(() => {
    if (!slugEdited) {
      addForm.setValue("slug", toItemSlug(nameValue), { shouldValidate: false });
    }
  }, [nameValue, slugEdited, addForm]);

  const createMutation = useMutation({
    mutationFn: (values: AddFormValues) =>
      createItem(slug, {
        name: values.name.trim(),
        slug: values.slug.trim(),
        description: values.description.trim() || undefined,
      }),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ["items", slug] });
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
        <h2 className="text-lg font-semibold">Items</h2>
        <Button variant="ghost" size="icon" onClick={() => setAddOpen(true)} aria-label="Create Item" className="-my-1">
          <Plus className="h-4 w-4" />
        </Button>
      </div>

      {items.length === 0 ? (
        <p className="text-sm text-muted-foreground italic">No items yet.</p>
      ) : (
        <div className="space-y-2">
          {items.map((item) => (
            <Card key={item.id} className="px-4 py-3">
              <div className="flex items-center justify-between">
                <Link
                  to="/campaigns/$slug/items/$itemSlug"
                  params={{ slug, itemSlug: item.slug }}
                  className="font-medium hover:underline"
                >
                  {item.name}
                </Link>
                <ChevronRight className="h-4 w-4 text-muted-foreground" />
              </div>
            </Card>
          ))}
        </div>
      )}

      <Dialog open={addOpen} onOpenChange={(open) => (open ? setAddOpen(true) : closeAdd())}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Create Item</DialogTitle>
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
                  {createMutation.error instanceof Error ? createMutation.error.message : "Failed to create item."}
                </p>
              )}
              <DialogFooter>
                <Button type="button" variant="ghost" onClick={closeAdd} disabled={createMutation.isPending}>
                  Cancel
                </Button>
                <Button type="submit" variant="create" disabled={createMutation.isPending}>
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
