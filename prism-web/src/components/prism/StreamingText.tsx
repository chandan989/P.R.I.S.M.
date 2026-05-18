import { Fragment, useMemo } from "react";
import SourceDot from "./SourceDot";
import type { SourceRef } from "@/lib/types";
import { AlertTriangle, AlertCircle, Info, ShieldAlert, CheckCircle2 } from "lucide-react";

interface Token {
  type: "text" | "dot";
  text?: string;
  ref?: SourceRef;
}

interface Props {
  tokens: Token[];
  isStreaming: boolean;
}

export default function StreamingText({ tokens, isStreaming }: Props) {
  const elements = useMemo(() => {
    let combinedText = "";
    const dots: React.ReactNode[] = [];
    
    for (let i = 0; i < tokens.length; i++) {
      const t = tokens[i];
      if (t.type === "text") {
        combinedText += t.text;
      } else if (t.type === "dot" && t.ref) {
        const dotId = dots.length;
        combinedText += `__DOT_${dotId}__`;
        dots.push(<SourceDot key={`dot-${i}`} signal={t.ref.signal} sourceTitle={t.ref.source} snippet={t.ref.snippet} />);
      }
    }

    const renderInline = (str: string) => {
      const parts = str.split(/(__DOT_\d+__)/);
      return parts.map((part, idx) => {
        const dotMatch = part.match(/__DOT_(\d+)__/);
        if (dotMatch) {
          return <Fragment key={idx}>{dots[parseInt(dotMatch[1])]}</Fragment>;
        }
        
        let html = part
          .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
          .replace(/(^|\s)\*(.*?)\*(?=\s|$|[.,!?])/g, '$1<em>$2</em>')
          .replace(/\$\\rightarrow\$/g, '→');
          
        return <span key={idx} dangerouslySetInnerHTML={{ __html: html }} />;
      });
    };

    const rawBlocks = combinedText.split(/\n\n+/);
    const els: React.ReactNode[] = [];

    rawBlocks.forEach((block, bIdx) => {
      if (!block.trim()) return;

      const lines = block.trim().split('\n');
      const headerLine = lines[0];

      const isRisk = headerLine.match(/^(CRITICAL|HIGH|MODERATE(?:\/HIGH)?)\s+RISK:\s*(.*)$/i);
      const isOtherObs = headerLine.match(/^OTHER OBSERVATIONS:?/i);
      const isRecs = headerLine.match(/^Recommendation(s)?:?/i);

      if (isRisk || isOtherObs || isRecs) {
        let accentColor = "var(--aura-cyan)";
        let bg = "rgba(0, 225, 217, 0.03)";

        if (isRisk) {
          const level = isRisk[1].toUpperCase();
          if (level.includes("HIGH") && !level.includes("CRITICAL")) {
            accentColor = "var(--aura-orange)";
            bg = "rgba(255, 128, 8, 0.03)";
          } else if (level === "MODERATE") {
            accentColor = "var(--aura-yellow)";
            bg = "rgba(255, 200, 55, 0.03)";
          } else if (level === "CRITICAL") {
            accentColor = "#F87171";
            bg = "rgba(248, 113, 113, 0.03)";
          }
        } else if (isRecs) {
          accentColor = "#4ADE80";
          bg = "rgba(74, 222, 128, 0.03)";
        }

        els.push(
          <div key={bIdx} className="clinical-output-block good" style={{ borderLeft: `3px solid ${accentColor}`, background: bg, marginBottom: "var(--space-4)" }}>
            {lines.map((line, lIdx) => {
              const isHeader = lIdx === 0;
              return (
                <div key={lIdx} style={{ 
                  fontWeight: isHeader ? 600 : 400, 
                  color: isHeader ? accentColor : "inherit",
                  marginBottom: isHeader ? 8 : 4,
                  fontSize: isHeader ? 14 : 13
                }}>
                  {renderInline(line)}
                </div>
              );
            })}
          </div>
        );
      } else {
        els.push(
          <div key={bIdx} style={{ fontSize: 13, lineHeight: 1.6, marginBottom: "var(--space-4)" }}>
            {lines.map((line, lIdx) => (
              <div key={lIdx} style={{ marginBottom: 4 }}>
                {renderInline(line)}
              </div>
            ))}
          </div>
        );
      }
    });

    return els;
  }, [tokens]);

  return (
    <div className="output-text" style={{ fontFamily: "var(--font-primary)", color: "var(--ink-primary)" }}>
      {elements}
      {isStreaming && (
        <span className="inline-block w-2 h-4 ml-1 bg-primary animate-pulse align-middle" aria-hidden style={{ background: "var(--ink-primary)" }} />
      )}
    </div>
  );
}

export type { Token };

