import { AlertTriangle } from "lucide-react";

export default function StalenessWarning({ daysSinceUpdate }: { daysSinceUpdate: number }) {
  if (daysSinceUpdate <= 7) return null;
  return (
    <div className="staleness" role="alert">
      <AlertTriangle size={14} />
      Knowledge base last updated {daysSinceUpdate} days ago. Cross-reference with current FDA resources.
    </div>
  );
}
