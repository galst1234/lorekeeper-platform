import { X } from "lucide-react";
import { useState } from "react";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import { cn } from "@/lib/utils";

interface TagInputProps {
  value: string[];
  onChange: (next: string[]) => void;
  suggestions: string[];
  placeholder?: string;
  "aria-label"?: string;
}

const MAX_TAGS = 20;

export function TagInput({ value, onChange, suggestions, placeholder, ...rest }: TagInputProps) {
  const [draft, setDraft] = useState("");

  function addTag(raw: string) {
    const tag = raw.trim().toLowerCase();
    if (!tag || value.includes(tag) || value.length >= MAX_TAGS) return;
    onChange([...value, tag]);
    setDraft("");
  }

  function removeTag(tag: string) {
    onChange(value.filter((existing) => existing !== tag));
  }

  const available = suggestions.filter(
    (suggestion) => !value.includes(suggestion) && suggestion.includes(draft.trim().toLowerCase())
  );

  return (
    <div className="rounded-md border border-input p-2">
      <div className="flex flex-wrap items-center gap-1.5">
        {value.map((tag) => (
          <Badge key={tag} variant="secondary" className="gap-1">
            {tag}
            <button type="button" onClick={() => removeTag(tag)} aria-label={`Remove ${tag}`}>
              <X className="h-3 w-3" />
            </button>
          </Badge>
        ))}
        <Input
          value={draft}
          onChange={(event) => setDraft(event.target.value)}
          onKeyDown={(event) => {
            if (event.key === "Enter" || event.key === ",") {
              event.preventDefault();
              addTag(draft);
            } else if (event.key === "Backspace" && draft === "" && value.length > 0) {
              removeTag(value[value.length - 1]);
            }
          }}
          placeholder={value.length === 0 ? placeholder : undefined}
          aria-label={rest["aria-label"]}
          className={cn("h-7 w-24 flex-1 border-0 p-0 shadow-none focus-visible:ring-0")}
        />
      </div>
      {draft.trim() !== "" && available.length > 0 && (
        <div className="mt-2 flex flex-wrap gap-1.5">
          {available.slice(0, 8).map((suggestion) => (
            <button key={suggestion} type="button" onClick={() => addTag(suggestion)}>
              <Badge variant="outline">{suggestion}</Badge>
            </button>
          ))}
        </div>
      )}
    </div>
  );
}
