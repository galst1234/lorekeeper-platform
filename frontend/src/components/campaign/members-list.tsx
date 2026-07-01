import { useSuspenseQuery } from "@tanstack/react-query";
import { membersQueryOptions } from "@/api/membership";
import { Badge } from "@/components/ui/badge";
import { Card } from "@/components/ui/card";

interface MembersListProps {
  slug: string;
}

export function MembersList({ slug }: MembersListProps) {
  const { data: members } = useSuspenseQuery(membersQueryOptions(slug));

  return (
    <div>
      <h2 className="text-lg font-semibold mb-3">Members</h2>
      <div className="space-y-2">
        {members.map((member) => (
          <Card key={member.user_id} className="px-4 py-3">
            <div className="flex items-center justify-between">
              <span className="font-medium">{member.display_name ?? "Unknown"}</span>
              <Badge variant={member.role === "gm" ? "default" : "secondary"} className="text-xs">
                {member.role === "gm" ? "GM" : "Player"}
              </Badge>
            </div>
          </Card>
        ))}
      </div>
    </div>
  );
}
