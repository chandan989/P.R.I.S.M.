import { ShieldCheck, Github, ExternalLink } from "lucide-react";

export default function Footer() {
  return (
    <footer className="container footer">
      <div className="footer-left">
        <div className="nav-logo">
          <img src="/Logo.svg" alt="P.R.I.S.M." style={{ height: 32 }} />
        </div>
        <p className="footer-tagline" style={{ fontStyle: "italic" }}>
          "Users don't need AI to be perfect. They need AI to show its work."
        </p>
        <span className="footer-badge">
          <ShieldCheck size={12} /> Zero-Data-Egress · HIPAA-Compliant
        </span>
        {/* <div className="footer-badges" style={{ display: "flex", gap: 6, flexWrap: "wrap", marginTop: 8 }}>
          <img src="https://img.shields.io/badge/Powered%20by-Gemma%204%20A4B%2026B-4285F4?logo=google&logoColor=white" alt="Gemma 4" style={{ height: 20 }} />
          <img src="https://img.shields.io/badge/Kaggle-Gemma%204%20Good-20BEFF?logo=kaggle&logoColor=white" alt="Kaggle" style={{ height: 20 }} />
          <img src="https://img.shields.io/badge/Tracks-Safety%20%26%20Trust%20%7C%20Health%20%26%20Sciences-34A853" alt="Tracks" style={{ height: 20 }} />
        </div> */}
      </div>
      <div className="footer-links">
        <a href="/how-it-works">Architecture</a>
        <a href="/demo">Glass Box Demo</a>
        <a href="https://github.com/chandan989/P.R.I.S.M." target="_blank" rel="noreferrer" style={{ display: "inline-flex", alignItems: "center", gap: 4 }}>
          <Github size={14} /> GitHub
        </a>
      </div>
    </footer>
  );
}
