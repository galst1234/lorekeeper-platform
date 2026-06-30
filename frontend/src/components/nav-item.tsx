import { Link } from "@tanstack/react-router";
import type { LucideIcon } from "lucide-react";
import { Badge } from "@/components/ui/badge";

interface NavItemProps {
  to: string;
  params?: Record<string, string>;
  hash?: string;
  icon: LucideIcon;
  label: string;
  badge?: number;
  isActive?: boolean;
  exact?: boolean;
}

const activeClass =
  "flex items-center gap-3 px-3 py-2 rounded-md text-sm transition-colors bg-primary/10 text-primary font-medium";
const inactiveClass =
  "flex items-center gap-3 px-3 py-2 rounded-md text-sm transition-colors text-muted-foreground hover:bg-muted hover:text-foreground";

export function NavItem({ to, params, hash, icon: Icon, label, badge, isActive, exact }: NavItemProps) {
  const content = (
    <>
      <Icon className="h-4 w-4 shrink-0" />
      <span className="flex-1">{label}</span>
      {badge !== undefined && badge > 0 && (
        <Badge variant="secondary" className="ml-auto text-xs">
          {badge}
        </Badge>
      )}
    </>
  );

  if (isActive !== undefined) {
    return (
      <Link
        to={to}
        params={params}
        hash={hash}
        aria-current={isActive ? "page" : undefined}
        className={isActive ? activeClass : inactiveClass}
      >
        {content}
      </Link>
    );
  }

  return (
    <Link
      to={to}
      params={params}
      hash={hash}
      activeOptions={{ exact: exact ?? false }}
      activeProps={{ className: activeClass, "aria-current": "page" as const }}
      inactiveProps={{ className: inactiveClass }}
    >
      {content}
    </Link>
  );
}
