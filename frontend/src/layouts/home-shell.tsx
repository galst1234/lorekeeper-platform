import { useSuspenseQuery } from "@tanstack/react-query";
import { Link } from "@tanstack/react-router";
import { meQueryOptions } from "@/api/me";
import { ThemeToggle } from "@/components/theme-toggle";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import { Button } from "@/components/ui/button";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";

export function HomeShell({ children }: { children: React.ReactNode }) {
  const { data: me } = useSuspenseQuery(meQueryOptions);

  return (
    <div className="min-h-screen flex flex-col bg-background">
      <header className="h-14 border-b bg-background flex items-center px-4 gap-3 shrink-0">
        <Link to="/" className="font-semibold text-foreground">
          Lorekeeper
        </Link>
        <div className="ml-auto flex items-center gap-1">
          <ThemeToggle />
          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <Button variant="ghost" className="flex items-center gap-2 h-9 px-2">
                <Avatar className="h-7 w-7">
                  <AvatarFallback className="text-xs">{me.display_name?.[0]?.toUpperCase() ?? "?"}</AvatarFallback>
                </Avatar>
                <span className="text-sm">{me.display_name}</span>
              </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="end">
              <DropdownMenuItem asChild>
                <a href="/legacy-agent">Legacy Agent</a>
              </DropdownMenuItem>
              <DropdownMenuItem asChild>
                <Link to="/logout">Sign out</Link>
              </DropdownMenuItem>
            </DropdownMenuContent>
          </DropdownMenu>
        </div>
      </header>
      <main className="flex-1">{children}</main>
    </div>
  );
}
