import type { ReactNode } from "react";
import { cn } from "@/lib/utils";

interface PageContainerProps {
  className?: string;
  children: ReactNode;
}

export function PageContainer({ className, children }: PageContainerProps) {
  return <div className={cn("max-w-7xl mx-auto px-6 py-8", className)}>{children}</div>;
}
