import type { LucideIcon } from "lucide-react";
import { Pencil, Trash2 } from "lucide-react";
import { type ChangeEvent, useRef, useState } from "react";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";

interface EntityImageFieldProps {
  imageUrl: string | null;
  placeholderIcon: LucideIcon;
  onFileSelected: (file: File) => void;
  onRemove: () => void;
}

export function EntityImageField({
  imageUrl,
  placeholderIcon: PlaceholderIcon,
  onFileSelected,
  onRemove,
}: EntityImageFieldProps) {
  const inputRef = useRef<HTMLInputElement>(null);
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);

  const displayUrl = previewUrl ?? imageUrl;

  function handleFileChange(event: ChangeEvent<HTMLInputElement>) {
    const file = event.target.files?.[0];
    if (!file) return;
    setPreviewUrl(URL.createObjectURL(file));
    onFileSelected(file);
    event.target.value = "";
  }

  function handleRemove() {
    setPreviewUrl(null);
    onRemove();
  }

  return (
    <div className="space-y-2">
      <button
        type="button"
        onClick={() => inputRef.current?.click()}
        className="aspect-square w-full overflow-hidden rounded-md bg-muted flex items-center justify-center"
        aria-label="Change image"
      >
        {displayUrl ? (
          <img src={displayUrl} alt="" className="h-full w-full object-cover" />
        ) : (
          <PlaceholderIcon className="h-12 w-12 text-muted-foreground" />
        )}
      </button>
      <input
        ref={inputRef}
        type="file"
        accept="image/jpeg,image/png,image/webp"
        className="hidden"
        onChange={handleFileChange}
      />
      <div className="flex items-center justify-center gap-1">
        <Button
          type="button"
          variant="ghost"
          size="icon"
          onClick={() => inputRef.current?.click()}
          aria-label="Edit image"
        >
          <Pencil className="h-4 w-4" />
        </Button>
        <Button
          type="button"
          variant="ghost"
          size="icon"
          onClick={handleRemove}
          disabled={!displayUrl}
          aria-label="Remove image"
        >
          <Trash2 className={cn("h-4 w-4", displayUrl && "text-destructive")} />
        </Button>
      </div>
    </div>
  );
}
