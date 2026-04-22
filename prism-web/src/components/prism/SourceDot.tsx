import { useEffect, useRef, useState } from "react";
import type { Signal } from "@/lib/types";

interface Props {
  signal: Signal;
  sourceTitle: string;
  snippet: string;
}

const labels: Record<Signal, string> = {
  green: "Verified source",
  yellow: "Inferred / weakly grounded",
  red: "Contradicted by source",
  grey: "Insufficient evidence",
};

export default function SourceDot({ signal, sourceTitle, snippet }: Props) {
  const [open, setOpen] = useState(false);
  const ref = useRef<HTMLSpanElement | null>(null);

  useEffect(() => {
    if (!open) return;
    const onDoc = (e: MouseEvent) => {
      if (ref.current && !ref.current.contains(e.target as Node)) setOpen(false);
    };
    document.addEventListener("mousedown", onDoc);
    return () => document.removeEventListener("mousedown", onDoc);
  }, [open]);

  return (
    <span className="source-dot-wrap" ref={ref}>
      <button
        className={`source-dot source-dot--${signal}`}
        aria-label={`${labels[signal]}: ${sourceTitle}`}
        aria-expanded={open}
        onClick={() => setOpen((v) => !v)}
      />
      {open && (
        <span className="source-popover" role="dialog">
          <span className="source-popover-title">{sourceTitle}</span>
          <span className="source-popover-snippet">{snippet}</span>
        </span>
      )}
    </span>
  );
}
