import { Command as CommandPrimitive } from "cmdk";
import { X } from "lucide-react";
import { useEffect, useId, useRef, useState } from "react";
import { Badge } from "@/components/ui/badge";
import { Command, CommandItem, CommandList } from "@/components/ui/command";
import { Popover, PopoverAnchor, PopoverContent } from "@/components/ui/popover";
import { cn } from "@/lib/utils";

interface TagInputProps {
  value: string[];
  onChange: (next: string[]) => void;
  suggestions: string[];
  placeholder?: string;
  "aria-label"?: string;
}

const MAX_TAGS = 20;
const MAX_SUGGESTIONS = 8;

export function TagInput({ value, onChange, suggestions, placeholder, ...rest }: TagInputProps) {
  const [draft, setDraft] = useState("");
  const [open, setOpen] = useState(false);
  const [focusedTagIndex, setFocusedTagIndex] = useState<number | null>(null);
  const [canScrollLeft, setCanScrollLeft] = useState(false);
  const [canScrollRight, setCanScrollRight] = useState(false);
  const containerRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);
  const baseId = useId();

  function scrollToInput() {
    const container = containerRef.current;
    if (container) container.scrollLeft = container.scrollWidth;
  }

  useEffect(() => {
    const container = containerRef.current;
    if (container && value.length > 0 && focusedTagIndex === null) container.scrollLeft = container.scrollWidth;
  }, [value, focusedTagIndex]);

  useEffect(() => {
    const container = containerRef.current;
    if (!container) return;
    if (value.length === 0) {
      setCanScrollLeft(false);
      setCanScrollRight(false);
      return;
    }
    setCanScrollLeft(container.scrollLeft > 1);
    setCanScrollRight(container.scrollLeft < container.scrollWidth - container.clientWidth - 1);
  }, [value]);

  useEffect(() => {
    const container = containerRef.current;
    if (!container) return;
    function handleScroll() {
      if (!container) return;
      setCanScrollLeft(container.scrollLeft > 1);
      setCanScrollRight(container.scrollLeft < container.scrollWidth - container.clientWidth - 1);
    }
    handleScroll();
    container.addEventListener("scroll", handleScroll, { passive: true });
    return () => container.removeEventListener("scroll", handleScroll);
  }, []);

  useEffect(() => {
    if (focusedTagIndex === null) return;
    const container = containerRef.current;
    if (!container) return;
    if (focusedTagIndex === 0) {
      container.scrollLeft = 0;
      return;
    }
    const tagElement = container.querySelector<HTMLElement>(`[data-tag-index="${focusedTagIndex}"]`);
    tagElement?.scrollIntoView({ block: "nearest", inline: "nearest" });
  }, [focusedTagIndex]);

  useEffect(() => {
    const container = containerRef.current;
    if (!container) return;
    function handleWheel(event: WheelEvent) {
      if (event.deltaY === 0 || !container) return;
      const maxScrollLeft = container.scrollWidth - container.clientWidth;
      const nextScrollLeft = container.scrollLeft + event.deltaY;
      if (maxScrollLeft <= 0 || nextScrollLeft < 0 || nextScrollLeft > maxScrollLeft) return;
      event.preventDefault();
      container.scrollLeft = nextScrollLeft;
    }
    container.addEventListener("wheel", handleWheel, { passive: false });
    return () => container.removeEventListener("wheel", handleWheel);
  }, []);

  function addTag(raw: string) {
    const tag = raw.trim().toLowerCase();
    if (!tag || value.includes(tag) || value.length >= MAX_TAGS) return;
    onChange([...value, tag]);
    setDraft("");
  }

  function removeTag(tag: string) {
    onChange(value.filter((existing) => existing !== tag));
  }

  const trimmedDraft = draft.trim();
  const normalizedDraft = trimmedDraft.toLowerCase();
  const filteredSuggestions = suggestions
    .filter((suggestion) => !value.includes(suggestion) && suggestion.includes(normalizedDraft))
    .slice(0, MAX_SUGGESTIONS);
  const showCreateOption =
    normalizedDraft !== "" && !value.includes(normalizedDraft) && filteredSuggestions.length === 0;
  const hasOptions = showCreateOption || filteredSuggestions.length > 0;
  const maskImage = `linear-gradient(to right, ${canScrollLeft ? "transparent" : "black"} 0, black 12px, black calc(100% - 12px), ${canScrollRight ? "transparent" : "black"} 100%)`;

  return (
    <Command shouldFilter={false} className="overflow-visible bg-transparent">
      <Popover open={open && hasOptions} onOpenChange={(next) => setOpen(next)}>
        <PopoverAnchor asChild>
          <div
            ref={containerRef}
            style={{ maskImage, WebkitMaskImage: maskImage }}
            role="listbox"
            aria-label="Selected tags"
            className="flex h-10 items-center gap-1.5 overflow-x-auto overflow-y-hidden rounded-md border border-input px-3 py-2 [-ms-overflow-style:none] [scrollbar-width:none] [&::-webkit-scrollbar]:hidden"
          >
            {value.map((tag, index) => (
              <Badge
                key={tag}
                id={`${baseId}-tag-${index}`}
                role="option"
                aria-selected={focusedTagIndex === index}
                variant="secondary"
                data-tag-index={index}
                className={cn(
                  "shrink-0 cursor-pointer gap-1",
                  focusedTagIndex === index && "ring-2 ring-ring ring-offset-1"
                )}
                onClick={() => {
                  setOpen(false);
                  setFocusedTagIndex(index);
                  inputRef.current?.focus();
                }}
              >
                {tag}
                <button
                  type="button"
                  onClick={(event) => {
                    event.stopPropagation();
                    removeTag(tag);
                  }}
                  aria-label={`Remove ${tag}`}
                >
                  <X className="h-3 w-3" />
                </button>
              </Badge>
            ))}
            <CommandPrimitive.Input
              ref={inputRef}
              value={draft}
              onValueChange={(next) => {
                setDraft(next);
                if (next !== "") {
                  setFocusedTagIndex(null);
                  setOpen(true);
                }
              }}
              onFocus={() => {
                setOpen(true);
                scrollToInput();
              }}
              onBlur={() => setFocusedTagIndex(null)}
              onKeyDown={(event) => {
                if (event.key === "ArrowLeft" && draft === "") {
                  if (value.length === 0) return;
                  event.preventDefault();
                  setOpen(false);
                  setFocusedTagIndex(focusedTagIndex === null ? value.length - 1 : Math.max(0, focusedTagIndex - 1));
                } else if (event.key === "ArrowRight" && focusedTagIndex !== null) {
                  event.preventDefault();
                  if (focusedTagIndex < value.length - 1) {
                    setFocusedTagIndex(focusedTagIndex + 1);
                  } else {
                    setFocusedTagIndex(null);
                    setOpen(true);
                  }
                } else if (event.key === "Home" && draft === "" && value.length > 0) {
                  event.preventDefault();
                  setOpen(false);
                  setFocusedTagIndex(0);
                } else if (event.key === "End" && focusedTagIndex !== null) {
                  event.preventDefault();
                  setFocusedTagIndex(null);
                  setOpen(true);
                } else if (event.key === "Escape" && focusedTagIndex !== null) {
                  event.preventDefault();
                  setFocusedTagIndex(null);
                } else if ((event.key === "Backspace" || event.key === "Delete") && focusedTagIndex !== null) {
                  event.preventDefault();
                  removeTag(value[focusedTagIndex]);
                  const remaining = value.length - 1;
                  setFocusedTagIndex(remaining === 0 ? null : Math.min(focusedTagIndex, remaining - 1));
                } else if (event.key === "Enter" && focusedTagIndex !== null) {
                  event.preventDefault();
                } else if (event.key === ",") {
                  event.preventDefault();
                  addTag(draft);
                } else if (event.key === "Enter" && !hasOptions) {
                  event.preventDefault();
                  addTag(draft);
                } else if (event.key === "Backspace" && draft === "" && value.length > 0) {
                  removeTag(value[value.length - 1]);
                }
              }}
              placeholder={placeholder}
              aria-label={rest["aria-label"]}
              aria-activedescendant={focusedTagIndex !== null ? `${baseId}-tag-${focusedTagIndex}` : undefined}
              className={cn(
                "h-full min-w-24 flex-1 shrink-0 border-0 bg-transparent p-0 text-sm shadow-none outline-none placeholder:text-muted-foreground"
              )}
            />
          </div>
        </PopoverAnchor>
        <PopoverContent
          className="w-[var(--radix-popover-trigger-width)] p-1"
          align="start"
          onOpenAutoFocus={(event) => event.preventDefault()}
          onPointerDownOutside={(event) => {
            if (containerRef.current?.contains(event.target as Node)) event.preventDefault();
          }}
          onFocusOutside={(event) => {
            if (containerRef.current?.contains(event.target as Node)) event.preventDefault();
          }}
        >
          <CommandList>
            {showCreateOption && (
              <CommandItem value={`__create__${normalizedDraft}`} onSelect={() => addTag(trimmedDraft)}>
                Add "{trimmedDraft}"
              </CommandItem>
            )}
            {filteredSuggestions.map((suggestion) => (
              <CommandItem key={suggestion} value={suggestion} onSelect={() => addTag(suggestion)}>
                {suggestion}
              </CommandItem>
            ))}
          </CommandList>
        </PopoverContent>
      </Popover>
    </Command>
  );
}
