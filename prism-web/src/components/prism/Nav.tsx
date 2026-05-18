import { NavLink, Link, useLocation } from "react-router-dom";
import { useState, useEffect } from "react";
import { Menu, X, Sparkles } from "lucide-react";
import BackendSettings from "./BackendSettings";

const links = [
  { to: "/", label: "Home" },
  { to: "/how-it-works", label: "How It Works" },
  { to: "/audit", label: "Audit" },
];

export default function Nav() {
  const [open, setOpen] = useState(false);
  const [scrolled, setScrolled] = useState(false);
  const loc = useLocation();
  useEffect(() => setOpen(false), [loc.pathname]);

  useEffect(() => {
    const handleScroll = () => {
      setScrolled(window.scrollY > 20);
    };
    window.addEventListener("scroll", handleScroll);
    return () => window.removeEventListener("scroll", handleScroll);
  }, []);

  return (
    <nav className={`nav ${scrolled ? "nav--scrolled" : ""}`} aria-label="Primary">
      <div className="container nav-inner">
        <Link to="/" className="nav-logo" aria-label="P.R.I.S.M. home">
          <img src="/Logo.svg" alt="P.R.I.S.M." style={{ height: 28 }} />
        </Link>
        <div style={{ display: "flex", alignItems: "center", gap: "var(--space-4)" }}>
          <div className="nav-links" role="menubar">
            {links.slice(1).map((l) => (
              <NavLink
                key={l.to}
                to={l.to}
                end
                className={({ isActive }) =>
                  isActive ? "pill pill--active" : "pill"
                }
              >
                {l.label}
              </NavLink>
            ))}
          </div>
          <BackendSettings />
          <Link to="/demo" className="pill pill--solid nav-cta">
            <Sparkles size={14} /> Launch Glass Box
          </Link>
        </div>
        <button
          className="nav-mobile-toggle"
          aria-label="Toggle menu"
          aria-expanded={open}
          onClick={() => setOpen((v) => !v)}
        >
          {open ? <X size={20} /> : <Menu size={20} />}
        </button>
      </div>
      {open && (
        <>
          <div className="drawer-backdrop" onClick={() => setOpen(false)} />
          <aside className="drawer" aria-label="Mobile navigation">
            {links.map((l) => (
              <NavLink
                key={l.to}
                to={l.to}
                end
                className={({ isActive }) =>
                  isActive ? "pill pill--active" : "pill"
                }
              >
                {l.label}
              </NavLink>
            ))}
            <Link to="/demo" className="pill pill--solid">
              <Sparkles size={14} /> Launch Glass Box
            </Link>
          </aside>
        </>
      )}
    </nav>
  );
}
