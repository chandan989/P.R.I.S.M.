import { NavLink, Link, useLocation } from "react-router-dom";
import { useState, useEffect } from "react";
import { Menu, X } from "lucide-react";

const links = [
  { to: "/", label: "Home" },
  { to: "/how-it-works", label: "How It Works" },
  { to: "/demo", label: "Demo" },
  { to: "/audit", label: "Glass Box" },
];

export default function Nav() {
  const [open, setOpen] = useState(false);
  const loc = useLocation();
  useEffect(() => setOpen(false), [loc.pathname]);

  return (
    <nav className="nav" aria-label="Primary">
      <div className="container nav-inner">
        <Link to="/" className="nav-logo" aria-label="P.R.I.S.M. home">
          P.R.I.S.M.
        </Link>
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
        <Link to="/audit" className="pill pill--solid nav-cta">
          Launch Glass Box →
        </Link>
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
            <Link to="/audit" className="pill pill--solid">
              Launch Glass Box →
            </Link>
          </aside>
        </>
      )}
    </nav>
  );
}
