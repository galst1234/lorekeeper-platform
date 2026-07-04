import { zodResolver } from "@hookform/resolvers/zod";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { createFileRoute, Link, useRouter } from "@tanstack/react-router";
import { useEffect, useState } from "react";
import { useForm } from "react-hook-form";
import { z } from "zod";
import { createChronicleEntry } from "@/api/chronicle";
import { Button } from "@/components/ui/button";
import { DateTimePicker } from "@/components/ui/datetime-picker";
import { Form, FormControl, FormField, FormItem, FormLabel, FormMessage } from "@/components/ui/form";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { datetimeLocalToIso, toDatetimeLocalValue } from "@/lib/datetime";

export const Route = createFileRoute("/campaigns/$slug/chronicle/new")({
  component: NewChronicleEntryPage,
});

function toEntrySlug(title: string): string {
  return title
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, "-")
    .replace(/^-+|-+$/g, "");
}

const createSchema = z.object({
  title: z.string().trim().min(1, "Title is required"),
  slug: z
    .string()
    .trim()
    .min(1, "Slug is required")
    .regex(/^[a-z0-9]+(-[a-z0-9]+)*$/, "Slug must be lowercase letters, numbers, and hyphens"),
  occurredAt: z.string().min(1, "Session date is required"),
  body: z.string(),
});

type CreateFormValues = z.infer<typeof createSchema>;

function defaultCreateValues(): CreateFormValues {
  return { title: "", slug: "", occurredAt: toDatetimeLocalValue(new Date()), body: "" };
}

function NewChronicleEntryPage() {
  const { slug } = Route.useParams();
  const router = useRouter();
  const queryClient = useQueryClient();
  const [slugEdited, setSlugEdited] = useState(false);

  const form = useForm<CreateFormValues>({
    resolver: zodResolver(createSchema),
    defaultValues: defaultCreateValues(),
  });

  const titleValue = form.watch("title");

  useEffect(() => {
    if (!slugEdited) {
      form.setValue("slug", toEntrySlug(titleValue), { shouldValidate: false });
    }
  }, [titleValue, slugEdited, form]);

  const createMutation = useMutation({
    mutationFn: (values: CreateFormValues) =>
      createChronicleEntry(slug, {
        title: values.title.trim(),
        slug: values.slug.trim(),
        occurred_at: datetimeLocalToIso(values.occurredAt),
        body: values.body.trim() || undefined,
      }),
    onSuccess: async (entry) => {
      await queryClient.invalidateQueries({ queryKey: ["chronicle-entries", slug] });
      await router.navigate({
        to: "/campaigns/$slug/chronicle/$entrySlug",
        params: { slug, entrySlug: entry.slug },
      });
    },
  });

  return (
    <div className="mx-auto flex min-h-[calc(100vh-3.5rem)] w-full max-w-5xl flex-col px-6 py-8">
      <Link
        to="/campaigns/$slug/chronicle"
        params={{ slug }}
        className="text-sm text-muted-foreground hover:text-foreground inline-block mb-6"
      >
        ← Back to Chronicle
      </Link>

      <div className="mb-6">
        <h1 className="text-3xl font-bold">Create Chronicle Entry</h1>
        <p className="text-sm text-muted-foreground mt-1">
          Draft a full session write-up with room for long-form notes.
        </p>
      </div>

      <Form {...form}>
        <form
          onSubmit={form.handleSubmit((values) => createMutation.mutate(values))}
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

          <FormField
            control={form.control}
            name="body"
            render={({ field }) => (
              <FormItem className="flex min-h-0 flex-1 flex-col gap-2 space-y-0">
                <FormLabel>Content</FormLabel>
                <FormControl>
                  <Textarea className="min-h-[16rem] flex-1 leading-7" {...field} />
                </FormControl>
                <FormMessage />
              </FormItem>
            )}
          />

          {createMutation.isError && (
            <p className="text-sm text-destructive">
              {createMutation.error instanceof Error ? createMutation.error.message : "Failed to create entry."}
            </p>
          )}

          <div className="flex items-center justify-end gap-2">
            <Button type="button" variant="ghost" asChild>
              <Link to="/campaigns/$slug/chronicle" params={{ slug }}>
                Cancel
              </Link>
            </Button>
            <Button type="submit" variant="create" disabled={createMutation.isPending}>
              {createMutation.isPending ? "Creating..." : "Create"}
            </Button>
          </div>
        </form>
      </Form>
    </div>
  );
}
