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

      const riskMatch = headerLine.match(/^(CRITICAL|HIGH|MODERATE(?:\/HIGH)?)\s+RISK:\s*(.*)$/i);
      const isOtherObs = headerLine.match(/^OTHER OBSERVATIONS:?/i);
      const isRecs = headerLine.match(/^Recommendation(s)?:?/i);

      if (riskMatch) {
        const level = riskMatch[1].toUpperCase();
        const title = riskMatch[2] || "Identified Risk";
        
        let color = "#F87171"; // Red
        let bg = "rgba(248, 113, 113, 0.03)";
        let pillBg = "rgba(248, 113, 113, 0.15)";
        let Icon = ShieldAlert;
        
        if (level.includes("HIGH") && !level.includes("CRITICAL")) {
          color = "var(--aura-orange)";
          bg = "rgba(255, 128, 8, 0.03)";
          pillBg = "rgba(255, 128, 8, 0.15)";
          Icon = AlertTriangle;
        }
        if (level === "MODERATE") {
          color = "var(--aura-yellow)";
          bg = "rgba(255, 200, 55, 0.03)";
          pillBg = "rgba(255, 200, 55, 0.15)";
          Icon = AlertCircle;
        }
        if (level === "CRITICAL") {
          color = "#F87171";
          bg = "rgba(248, 113, 113, 0.03)";
          pillBg = "rgba(248, 113, 113, 0.15)";
          Icon = ShieldAlert;
        }

        els.push(
          <div key={bIdx} style={{ borderLeft: `3px solid ${color}`, background: bg }} className="my-4 p-4 rounded-r-md border border-l-0 border-border/50 shadow-sm transition-all duration-300 animate-in fade-in slide-in-from-bottom-2">
            <div style={{ color }} className="flex items-center gap-2 mb-3 font-semibold text-[15px] tracking-tight uppercase">
              <Icon size={18} className="shrink-0" />
              <span>{level} RISK: {renderInline(title)}</span>
            </div>
            <div className="space-y-3 text-[14px] leading-relaxed text-foreground/90">
              {lines.slice(1).map((line, lIdx) => {
                if (line.trim().startsWith('*')) {
                  const parts = line.replace(/^\*\s*/, '').split(':');
                  if (parts.length > 1) {
                    const key = parts[0];
                    const val = parts.slice(1).join(':');
                    return (
                      <div key={lIdx} className="flex gap-3 items-start">
                        <span style={{ fontSize: 11, fontWeight: 600, color: color, background: pillBg, display: "inline-block", padding: "2px 6px", borderRadius: 4, textTransform: "uppercase", letterSpacing: "0.02em", marginTop: 2, whiteSpace: "nowrap" }}>
                          {renderInline(key)}
                        </span>
                        <span className="text-foreground/90 leading-relaxed">{renderInline(val)}</span>
                      </div>
                    );
                  }
                }
                return <div key={lIdx} className="text-foreground/80">{renderInline(line)}</div>;
              })}
            </div>
          </div>
        );
      } else if (isOtherObs) {
        els.push(
          <div key={bIdx} style={{ borderLeft: "3px solid var(--aura-cyan)", background: "rgba(0, 225, 217, 0.03)" }} className="my-4 p-4 rounded-r-md border border-l-0 border-border/50 shadow-sm transition-all duration-300 animate-in fade-in slide-in-from-bottom-2">
            <div style={{ color: "var(--aura-cyan)" }} className="flex items-center gap-2 mb-3 font-semibold text-[15px] tracking-tight uppercase">
              <Info size={18} className="shrink-0" />
              <span>Other Observations</span>
            </div>
            <ul className="space-y-2 text-[14px] ml-5 list-disc text-foreground/80 leading-relaxed">
              {lines.slice(1).map((line, lIdx) => (
                <li key={lIdx} className="pl-1">{renderInline(line.replace(/^\*\s*/, ''))}</li>
              ))}
            </ul>
          </div>
        );
      } else if (isRecs) {
        els.push(
          <div key={bIdx} style={{ borderLeft: "3px solid #4ADE80", background: "rgba(74, 222, 128, 0.03)" }} className="my-4 p-4 rounded-r-md border border-l-0 border-border/50 shadow-sm transition-all duration-300 animate-in fade-in slide-in-from-bottom-2">
            <div style={{ color: "#4ADE80" }} className="flex items-center gap-2 mb-3 font-semibold text-[15px] tracking-tight uppercase">
              <CheckCircle2 size={18} className="shrink-0" />
              <span>Recommendations</span>
            </div>
            <div className="space-y-3 text-[14px] text-foreground/80 leading-relaxed">
              {lines.slice(1).map((line, lIdx) => {
                const isBullet = line.trim().startsWith('*');
                const isNumbered = /^\d+\./.test(line.trim());
                
                return (
                  <div key={lIdx} className={`ml-1 ${isBullet || isNumbered ? 'pl-3' : ''}`}>
                    {renderInline(line)}
                  </div>
                );
              })}
            </div>
          </div>
        );
      } else {
        els.push(
          <p key={bIdx} className="mb-4 text-[14px] leading-[1.7] text-foreground/80">
            {lines.map((line, lIdx) => (
              <Fragment key={lIdx}>
                {renderInline(line)}
                {lIdx < lines.length - 1 && <br />}
              </Fragment>
            ))}
          </p>
        );
      }
    });

    return els;
  }, [tokens]);

  return (
    <div className="output-text relative font-medium">
      {elements}
      {isStreaming && (
        <span className="inline-block w-2.5 h-5 ml-1 bg-primary animate-pulse align-middle rounded-sm opacity-70" aria-hidden />
      )}
    </div>
  );
}

export type { Token };

