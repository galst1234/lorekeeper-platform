import { useSuspenseQuery } from "@tanstack/react-query";
import { Link } from "@tanstack/react-router";
import { LayoutDashboard, Menu, Package, Settings, Users } from "lucide-react";
import { useState } from "react";
import { campaignQueryOptions } from "@/api/campaigns";
import { charactersQueryOptions } from "@/api/characters";
import { itemsQueryOptions } from "@/api/items";
import { meQueryOptions } from "@/api/me";
import { NavItem } from "@/components/nav-item";
import { ThemeToggle } from "@/components/theme-toggle";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import { Button } from "@/components/ui/button";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { Separator } from "@/components/ui/separator";
import { Sheet, SheetContent, SheetTrigger } from "@/components/ui/sheet";

interface CampaignShellProps {
  slug: string;
  children: React.ReactNode;
}

export function CampaignShell({ slug, children }: CampaignShellProps) {
  const { data: me } = useSuspenseQuery(meQueryOptions);
  const { data: campaign } = useSuspenseQuery(campaignQueryOptions(me.id, slug));
  const { data: characters } = useSuspenseQuery(charactersQueryOptions(slug));
  const { data: items } = useSuspenseQuery(itemsQueryOptions(slug));
  const [sheetOpen, setSheetOpen] = useState(false);

  const isGm = campaign.role === "gm";

  const sidebarItems = (
    <>
      <NavItem to="/campaigns/$slug" params={{ slug }} icon={LayoutDashboard} label="Overview" exact />
      <NavItem
        to="/campaigns/$slug/characters"
        params={{ slug }}
        icon={Users}
        label="Characters"
        badge={characters.length}
      />
      <NavItem to="/campaigns/$slug/items" params={{ slug }} icon={Package} label="Items" badge={items.length} />
      <Separator className="my-2" />
      {isGm && <NavItem to="/campaigns/$slug/settings" params={{ slug }} icon={Settings} label="Settings" exact />}
    </>
  );

  return (
    <div className="min-h-screen flex flex-col bg-background">
      {/* Top bar */}
      <header className="h-14 border-b bg-background flex items-center px-4 gap-3 shrink-0">
        <Sheet open={sheetOpen} onOpenChange={setSheetOpen}>
          <SheetTrigger asChild>
            <Button variant="ghost" size="icon" className="md:hidden" aria-label="Open sidebar">
              <Menu className="h-5 w-5" />
            </Button>
          </SheetTrigger>
          <SheetContent side="left" className="p-0 w-56">
            <nav
              className="flex flex-col gap-1 p-3"
              onClick={() => setSheetOpen(false)}
              onKeyDown={(e) => {
                if (e.key === "Enter" || e.key === " ") setSheetOpen(false);
              }}
            >
              {sidebarItems}
            </nav>
          </SheetContent>
        </Sheet>
        <Link to="/" className="font-semibold text-foreground hidden md:block shrink-0">
          Lorekeeper
        </Link>
        /
        <Link
          to="/campaigns/$slug"
          params={{ slug }}
          className="text-sm font-medium text-foreground truncate flex-1 md:flex-none"
        >
          {campaign.name}
        </Link>
        <div className="ml-auto flex items-center gap-1">
          <ThemeToggle />
          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <Button variant="ghost" className="flex items-center gap-2 h-9 px-2">
                <Avatar className="h-7 w-7">
                  <AvatarFallback className="text-xs">{me.display_name?.[0]?.toUpperCase() ?? "?"}</AvatarFallback>
                </Avatar>
                <span className="text-sm hidden md:block">{me.display_name}</span>
              </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="end">
              <DropdownMenuItem asChild>
                <Link to="/">Switch Campaign</Link>
              </DropdownMenuItem>
              <DropdownMenuItem asChild>
                <Link to="/logout">Sign out</Link>
              </DropdownMenuItem>
            </DropdownMenuContent>
          </DropdownMenu>
        </div>
      </header>

      <div className="flex flex-1 overflow-hidden">
        {/* Desktop sidebar */}
        <aside className="w-56 bg-sidebar border-r hidden md:flex flex-col shrink-0">
          <nav className="flex flex-col gap-1 p-3">{sidebarItems}</nav>
        </aside>

        {/* Page content */}
        <main className="flex-1 overflow-auto">{children}</main>
      </div>
    </div>
  );
}
