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
  // Parse textual stream and inject SourceDots accurately
  const elements = useMemo(() => {
    let combinedText = "";
    const dots: React.ReactNode[] = [];
    
    // Combine text and save dots as marker variables
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

      // Detect Block Types
      const riskMatch = headerLine.match(/^(CRITICAL|HIGH|MODERATE(?:\/HIGH)?)\s+RISK:\s*(.*)$/i);
      const isOtherObs = headerLine.match(/^OTHER OBSERVATIONS:?/i);
      const isRecs = headerLine.match(/^Recommendation(s)?:?/i);

      if (riskMatch) {
        const level = riskMatch[1].toUpperCase();
        const title = riskMatch[2] || "Identified Risk";
        
        let colorClass = "bg-red-500/10 border-red-500/20 text-red-900 dark:text-red-400";
        let Icon = ShieldAlert;
        
        if (level.includes("HIGH") && !level.includes("CRITICAL")) {
          colorClass = "bg-orange-500/10 border-orange-500/20 text-orange-900 dark:text-orange-400";
          Icon = AlertTriangle;
        }
        if (level === "MODERATE") {
          colorClass = "bg-yellow-500/10 border-yellow-500/20 text-yellow-900 dark:text-yellow-400";
          Icon = AlertCircle;
        }
        if (level === "CRITICAL") {
          colorClass = "bg-rose-500/20 border-rose-500/30 text-rose-900 dark:text-rose-400";
          Icon = ShieldAlert;
        }

        els.push(
          <div key={bIdx} className={`my-4 p-5 rounded-2xl border shadow-sm ${colorClass} backdrop-blur-sm transition-all duration-300 animate-in fade-in slide-in-from-bottom-2`}>
            <div className="flex items-center gap-2.5 mb-3 font-semibold text-lg tracking-tight">
              <Icon size={22} className="shrink-0" />
              <span>{level} RISK: {renderInline(title)}</span>
            </div>
            <div className="space-y-2.5 text-[15px] leading-relaxed text-foreground/90">
              {lines.slice(1).map((line, lIdx) => {
                if (line.trim().startsWith('*')) {
                  const parts = line.replace(/^\*\s*/, '').split(':');
                  if (parts.length > 1) {
                    const key = parts[0];
                    const val = parts.slice(1).join(':');
                    return (
                      <div key={lIdx} className="flex gap-2">
                        <strong className="font-semibold text-foreground shrink-0">{renderInline(key)}:</strong>
                        <span className="text-foreground/80">{renderInline(val)}</span>
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
          <div key={bIdx} className="my-4 p-5 rounded-2xl border bg-blue-500/10 border-blue-500/20 text-blue-900 dark:text-blue-300 shadow-sm backdrop-blur-sm transition-all duration-300 animate-in fade-in slide-in-from-bottom-2">
            <div className="flex items-center gap-2.5 mb-3 font-semibold text-lg tracking-tight">
              <Info size={22} className="shrink-0" />
              <span>Other Observations</span>
            </div>
            <ul className="space-y-2.5 text-[15px] ml-5 list-disc text-foreground/80">
              {lines.slice(1).map((line, lIdx) => (
                <li key={lIdx} className="pl-1">{renderInline(line.replace(/^\*\s*/, ''))}</li>
              ))}
            </ul>
          </div>
        );
      } else if (isRecs) {
        els.push(
          <div key={bIdx} className="my-4 p-5 rounded-2xl border bg-emerald-500/10 border-emerald-500/20 text-emerald-900 dark:text-emerald-300 shadow-sm backdrop-blur-sm transition-all duration-300 animate-in fade-in slide-in-from-bottom-2">
            <div className="flex items-center gap-2.5 mb-3 font-semibold text-lg tracking-tight">
              <CheckCircle2 size={22} className="shrink-0" />
              <span>Recommendations</span>
            </div>
            <div className="space-y-3 text-[15px] text-foreground/80">
              {lines.slice(1).map((line, lIdx) => {
                const isBullet = line.trim().startsWith('*');
                const isNumbered = /^\d+\./.test(line.trim());
                
                return (
                  <div key={lIdx} className={`ml-2 ${isBullet || isNumbered ? 'pl-2' : ''}`}>
                    {renderInline(line)}
                  </div>
                );
              })}
            </div>
          </div>
        );
      } else {
        els.push(
          <p key={bIdx} className="mb-4 text-[15px] leading-relaxed text-foreground/80">
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
