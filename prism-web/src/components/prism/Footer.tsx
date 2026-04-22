import { ShieldCheck } from "lucide-react";

export default function Footer() {
  return (
    <footer className="container footer">
      <div className="footer-left">
        <div className="nav-logo">P.R.I.S.M.</div>
        <p className="footer-tagline">The Glass Box Interpreter — a transparency layer for clinical AI.</p>
        <span className="footer-badge">
          <ShieldCheck size={12} /> Zero-Data-Egress · HIPAA-Compliant
        </span>
      </div>
      <div className="footer-links">
        <a href="#features">Features</a>
        <a href="#docs">Docs</a>
        <a href="#github">GitHub</a>
      </div>
    </footer>
  );
}
