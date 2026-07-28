/**
 * Top navigation. Module links come from `src/modules/registry.js`, so a
 * team enabling their module gets a nav entry automatically.
 */
import { Link, useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext.jsx";
import { MODULES } from "../modules/registry.js";

export default function Navbar() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();

  function handleLogout() {
    logout();
    navigate("/login");
  }

  return (
    <nav className="border-b border-slate-200 bg-white">
      <div className="mx-auto flex max-w-5xl items-center justify-between px-4 py-3">
        <Link to="/" className="text-lg font-semibold text-slate-900">
          CaseArena
        </Link>
        {user && (
          <div className="flex items-center gap-4 text-sm">
            <Link to="/" className="text-slate-600 hover:text-slate-900">
              Modules
            </Link>
            {MODULES.map((module) => (
              <Link
                key={module.id}
                to={module.path}
                className="text-slate-600 hover:text-slate-900"
              >
                {module.name}
              </Link>
            ))}
            <Link to="/profile" className="text-slate-600 hover:text-slate-900">
              Profile
            </Link>
            <button
              onClick={handleLogout}
              className="rounded-md border border-slate-300 px-3 py-1 text-slate-600 hover:bg-slate-50"
            >
              Log out
            </button>
          </div>
        )}
      </div>
    </nav>
  );
}
