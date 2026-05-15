import { Fragment, useMemo } from "react";
import SourceDot from "./SourceDot";
import type { SourceRef } from "@/lib/types";

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
  // We need to parse markdown-like syntax while maintaining the interleaved SourceDots.
  // We combine text tokens, but split when a dot appears.
  const chunks = useMemo(() => {
    const res: React.ReactNode[] = [];
    let currentText = "";
    
    const pushText = () => {
      if (!currentText) return;
      // Basic markdown parsing
      let html = currentText
        .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
        .replace(/\*(.*?)\*/g, '<em>$1</em>')
        .replace(/\n\n/g, '<br/><br/>')
        .replace(/\n/g, '<br/>')
        .replace(/### (.*?)(<br\/>|$)/g, '<h3>$1</h3>')
        .replace(/## (.*?)(<br\/>|$)/g, '<h2>$1</h2>');
        
      res.push(<span key={`text-${res.length}`} dangerouslySetInnerHTML={{ __html: html }} />);
      currentText = "";
    };

    for (let i = 0; i < tokens.length; i++) {
      const t = tokens[i];
      if (t.type === "text") {
        currentText += t.text;
      } else if (t.type === "dot" && t.ref) {
        pushText();
        res.push(<SourceDot key={`dot-${i}`} signal={t.ref.signal} sourceTitle={t.ref.source} snippet={t.ref.snippet} />);
      }
    }
    pushText();
    return res;
  }, [tokens]);

  return (
    <div className="output-text" style={{ lineHeight: "1.6" }}>
      {chunks}
      {isStreaming && <span className="cursor" aria-hidden />}
    </div>
  );
}

export type { Token };

