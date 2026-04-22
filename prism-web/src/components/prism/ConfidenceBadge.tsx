import { useEffect, useState } from "react";
import type { ConfidenceLevel } from "@/lib/types";
import { CheckCircle2, AlertTriangle, HelpCircle } from "lucide-react";

interface Props {
  level: ConfidenceLevel;
  score: number;
}

const labels: Record<ConfidenceLevel, string> = {
  HIGH: "The AI is confident",
  MODERATE: "The AI is moderately confident",
  LOW: "The AI is estimating",
};

export default function ConfidenceBadge({ level, score }: Props) {
  const [w, setW] = useState(0);
  useEffect(() => {
    const t = setTimeout(() => setW(score), 50);
    return () => clearTimeout(t);
  }, [score]);

  const Icon = level === "HIGH" ? CheckCircle2 : level === "MODERATE" ? AlertTriangle : HelpCircle;
  return (
    <div className="conf">
      <div className="conf-row">
        <span className={`conf-badge conf-badge--${level.toLowerCase()}`}>
          <Icon size={12} /> {level} · {score}%
        </span>
        <span style={{ fontFamily: "var(--font-mono)", fontSize: "var(--text-caption)", color: "var(--ink-tertiary)" }}>
          calibrated
        </span>
      </div>
      <div className="conf-bar" aria-hidden>
        <div className={`conf-bar-fill conf-bar-fill--${level.toLowerCase()}`} style={{ width: `${w}%` }} />
      </div>
      <div className="conf-label">{labels[level]}</div>
    </div>
  );
}
