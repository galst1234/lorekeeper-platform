import { AtSign, Bold, Code, Heading2, Italic, Link as LinkIcon, List, ListOrdered, Quote } from "lucide-react";
import { useRef, useState } from "react";
import { EntityLinkPicker } from "@/components/markdown/entity-link-picker";
import { MarkdownContent } from "@/components/markdown/markdown-content";
import {
  buildEntityDirective,
  buildLinkMarkdown,
  numberedListLines,
  prefixLines,
  replaceSelection,
  type Selection,
  wrapSelection,
} from "@/components/markdown/markdown-editor-utils";
import type { ResolvedEntity } from "@/components/markdown/use-entity-resolver";
import { useEntityResolver } from "@/components/markdown/use-entity-resolver";
import { Button } from "@/components/ui/button";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Textarea } from "@/components/ui/textarea";
import { cn } from "@/lib/utils";

interface MarkdownEditorProps {
  value: string;
  onChange: (value: string) => void;
  campaignSlug: string | undefined;
  onBlur?: () => void;
  name?: string;
  id?: string;
  "aria-describedby"?: string;
  "aria-invalid"?: boolean;
  className?: string;
  textareaClassName?: string;
}

export function MarkdownEditor({
  value,
  onChange,
  campaignSlug,
  onBlur,
  name,
  id,
  "aria-describedby": ariaDescribedby,
  "aria-invalid": ariaInvalid,
  className,
  textareaClassName,
}: MarkdownEditorProps) {
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const [pickerOpen, setPickerOpen] = useState(false);
  const resolver = useEntityResolver(campaignSlug);

  function getSelection(): Selection {
    const el = textareaRef.current;
    return { start: el?.selectionStart ?? value.length, end: el?.selectionEnd ?? value.length };
  }

  function applyEdit(edit: { value: string; selectionStart: number; selectionEnd: number }) {
    const scrollTop = textareaRef.current?.scrollTop;
    onChange(edit.value);
    requestAnimationFrame(() => {
      const el = textareaRef.current;
      if (!el) return;
      el.focus();
      el.setSelectionRange(edit.selectionStart, edit.selectionEnd);
      if (scrollTop !== undefined) el.scrollTop = scrollTop;
    });
  }

  function handleWrap(before: string, after: string, placeholder: string) {
    applyEdit(wrapSelection(value, getSelection(), before, after, placeholder));
  }

  function handlePrefixLines(prefix: string) {
    applyEdit(prefixLines(value, getSelection(), prefix));
  }

  function handleNumberedList() {
    applyEdit(numberedListLines(value, getSelection()));
  }

  function handleLink() {
    const selection = getSelection();
    const selectedText = value.slice(selection.start, selection.end);
    applyEdit(replaceSelection(value, selection, buildLinkMarkdown(selectedText)));
  }

  function handleEntitySelect(entity: ResolvedEntity) {
    const selection = getSelection();
    const selectedText = value.slice(selection.start, selection.end);
    applyEdit(replaceSelection(value, selection, buildEntityDirective(entity.type, entity.slug, selectedText)));
  }

  const toolbarButtonClassName = "h-8 w-8";

  return (
    <div className={cn("flex flex-col rounded-md border border-input", className)}>
      <Tabs defaultValue="write" className="flex min-h-0 flex-1 flex-col">
        <div className="flex items-center justify-between border-b border-input px-2 py-1">
          <div className="flex flex-wrap items-center gap-1">
            <Button
              type="button"
              variant="ghost"
              size="icon"
              className={toolbarButtonClassName}
              onClick={() => handleWrap("**", "**", "bold text")}
              aria-label="Bold"
            >
              <Bold className="h-4 w-4" />
            </Button>
            <Button
              type="button"
              variant="ghost"
              size="icon"
              className={toolbarButtonClassName}
              onClick={() => handleWrap("_", "_", "italic text")}
              aria-label="Italic"
            >
              <Italic className="h-4 w-4" />
            </Button>
            <Button
              type="button"
              variant="ghost"
              size="icon"
              className={toolbarButtonClassName}
              onClick={() => handlePrefixLines("## ")}
              aria-label="Heading"
            >
              <Heading2 className="h-4 w-4" />
            </Button>
            <Button
              type="button"
              variant="ghost"
              size="icon"
              className={toolbarButtonClassName}
              onClick={() => handlePrefixLines("- ")}
              aria-label="Bulleted list"
            >
              <List className="h-4 w-4" />
            </Button>
            <Button
              type="button"
              variant="ghost"
              size="icon"
              className={toolbarButtonClassName}
              onClick={handleNumberedList}
              aria-label="Numbered list"
            >
              <ListOrdered className="h-4 w-4" />
            </Button>
            <Button
              type="button"
              variant="ghost"
              size="icon"
              className={toolbarButtonClassName}
              onClick={() => handlePrefixLines("> ")}
              aria-label="Quote"
            >
              <Quote className="h-4 w-4" />
            </Button>
            <Button
              type="button"
              variant="ghost"
              size="icon"
              className={toolbarButtonClassName}
              onClick={() => handleWrap("`", "`", "code")}
              aria-label="Code"
            >
              <Code className="h-4 w-4" />
            </Button>
            <Button
              type="button"
              variant="ghost"
              size="icon"
              className={toolbarButtonClassName}
              onClick={handleLink}
              aria-label="Link"
            >
              <LinkIcon className="h-4 w-4" />
            </Button>
            <Button
              type="button"
              variant="ghost"
              size="icon"
              className={toolbarButtonClassName}
              onClick={() => setPickerOpen(true)}
              aria-label="Link entity"
            >
              <AtSign className="h-4 w-4" />
            </Button>
          </div>
          <TabsList className="h-8">
            <TabsTrigger value="write" className="text-xs">
              Write
            </TabsTrigger>
            <TabsTrigger value="preview" className="text-xs">
              Preview
            </TabsTrigger>
          </TabsList>
        </div>
        <TabsContent value="write" className="m-0 flex min-h-0 flex-1 flex-col">
          <Textarea
            ref={textareaRef}
            name={name}
            id={id}
            aria-describedby={ariaDescribedby}
            aria-invalid={ariaInvalid}
            value={value}
            onChange={(e) => onChange(e.target.value)}
            onBlur={onBlur}
            rows={6}
            className={cn(
              "resize-y rounded-none border-0 focus-visible:ring-0 focus-visible:ring-offset-0",
              textareaClassName
            )}
          />
        </TabsContent>
        <TabsContent value="preview" className="m-0 min-h-[8rem] p-3">
          {value.trim() ? (
            <MarkdownContent content={value} campaignSlug={campaignSlug ?? ""} />
          ) : (
            <p className="text-sm italic text-muted-foreground">Nothing to preview yet.</p>
          )}
        </TabsContent>
      </Tabs>

      <EntityLinkPicker
        open={pickerOpen}
        onOpenChange={setPickerOpen}
        resolver={resolver}
        onSelect={handleEntitySelect}
      />
    </div>
  );
}
