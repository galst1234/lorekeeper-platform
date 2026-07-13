import { Badge } from "@/components/ui/badge";
import { cn } from "@/lib/utils";

interface TagRowProps {
  tags: string[];
  className?: string;
}

export function TagRow({ tags, className }: TagRowProps) {
  if (tags.length === 0) return null;
  return (
    <div className={cn("flex flex-wrap items-center gap-1.5", className)}>
      {tags.map((tag) => (
        <Badge key={tag} variant="secondary" className="font-normal text-muted-foreground">
          {tag}
        </Badge>
      ))}
    </div>
  );
}
