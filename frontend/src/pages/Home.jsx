/**
 * Post-login launcher: the three platform modules.
 *
 * Rendered entirely from `src/modules/registry.js` — to change what
 * appears here, edit the registry, not this file.
 */
import { Link } from "react-router-dom";
import { MODULES, MODULE_STATUS } from "../modules/registry.js";

function ModuleCard({ module }) {
  const isLive = module.status === MODULE_STATUS.LIVE;

  return (
    <Link
      to={module.path}
      data-testid={`module-card-${module.id}`}
      className="flex flex-col rounded-lg border border-slate-200 bg-white p-5 transition hover:border-slate-400 hover:shadow-sm"
    >
      <div className="flex items-start justify-between gap-3">
        <span className="text-xs font-medium uppercase tracking-wide text-slate-400">
          Module {module.moduleNumber}
        </span>
        <span
          className={
            isLive
              ? "rounded-full bg-emerald-50 px-2 py-0.5 text-xs font-medium text-emerald-700"
              : "rounded-full bg-slate-100 px-2 py-0.5 text-xs font-medium text-slate-500"
          }
        >
          {isLive ? "Available" : "In development"}
        </span>
      </div>

      <h2 className="mt-3 text-lg font-semibold text-slate-900">{module.name}</h2>
      <p className="mt-2 flex-1 text-sm text-slate-600">{module.description}</p>
      <p className="mt-4 text-xs text-slate-400">{module.team}</p>
    </Link>
  );
}

export default function Home() {
  return (
    <div>
      <h1 className="text-2xl font-semibold text-slate-900">Choose a module</h1>
      <p className="mt-2 text-slate-600">
        Three parts of your case-interview preparation, in one place.
      </p>

      <div className="mt-6 grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {MODULES.map((module) => (
          <ModuleCard key={module.id} module={module} />
        ))}
      </div>
    </div>
  );
}
