export type Signal = "green" | "yellow" | "red" | "grey";
export type ConfidenceLevel = "HIGH" | "MODERATE" | "LOW";

export interface SourceRef {
  signal: Signal;
  source: string;
  snippet: string;
}

export interface Confidence {
  level: ConfidenceLevel;
  score: number; // 0-100
  brier?: number;
  ece?: number;
  ood?: boolean;
}

export interface Interpretation {
  label: string;
  probability: number; // 0-100
  supporting: string[];
  weakening: string[];
}

export interface AuditResult {
  /** Answer text with [SOURCED:green] / [SOURCED:red] / [SOURCED:yellow] / [SOURCED:grey] markers */
  answer: string;
  sources: SourceRef[]; // ordered to match markers in answer
  interpretations: Interpretation[];
  discarded: string[];
  selected: number;
  confidence: Confidence;
  daysSinceUpdate: number;
}

export interface AuditStreamEvent {
  type: "thought" | "answer" | "source_dot" | "confidence" | "done" | "error";
  content?: string;
  signal?: Signal;
  source?: string;
  snippet?: string;
  confidence?: Confidence;
}
