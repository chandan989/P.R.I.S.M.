import { Fragment } from "react";
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
  return (
    <p className="output-text">
      {tokens.map((t, i) => (
        <Fragment key={i}>
          {t.type === "text" ? (
            <span>{t.text}</span>
          ) : t.ref ? (
            <SourceDot signal={t.ref.signal} sourceTitle={t.ref.source} snippet={t.ref.snippet} />
          ) : null}
        </Fragment>
      ))}
      {isStreaming && <span className="cursor" aria-hidden />}
    </p>
  );
}

export type { Token };
