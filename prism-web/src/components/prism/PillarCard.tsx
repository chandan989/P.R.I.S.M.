interface Props {
  accent: "magenta" | "orange" | "cyan";
  icon: React.ReactNode;
  title: string;
  body: string;
  preview: React.ReactNode;
}

export default function PillarCard({ accent, icon, title, body, preview }: Props) {
  return (
    <article className={`pillar-card pillar-card--${accent}`}>
      <div className="pillar-icon">{icon}</div>
      <h3>{title}</h3>
      <p>{body}</p>
      <div style={{ marginTop: "auto", paddingTop: "var(--space-4)" }}>{preview}</div>
    </article>
  );
}
