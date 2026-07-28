/**
 * Shared "not built yet" screen for modules still in development.
 *
 * Keeps the launcher's three cards all leading somewhere real, so the
 * platform demos as one product rather than one working link and two dead
 * ones. Delete your module's usage of this once you have a real screen.
 */
import { Link } from "react-router-dom";

export default function ModulePlaceholder({ moduleNumber, name, team, description, buildNotes }) {
  return (
    <div className="mx-auto max-w-2xl">
      <p className="text-sm font-medium text-slate-500">
        Module {moduleNumber} · {team}
      </p>
      <h1 className="mt-1 text-2xl font-semibold text-slate-900">{name}</h1>
      <p className="mt-2 text-slate-600">{description}</p>

      <div className="mt-6 rounded-lg border border-dashed border-slate-300 bg-white p-6">
        <p className="font-medium text-slate-900">This module is still in development.</p>
        <p className="mt-1 text-sm text-slate-600">
          The route, navigation, and authentication are already wired up — {team} only needs to
          drop their screens in.
        </p>

        {buildNotes?.length > 0 && (
          <>
            <p className="mt-4 text-sm font-medium text-slate-900">To build this out:</p>
            <ol className="mt-2 list-decimal space-y-1 pl-5 text-sm text-slate-600">
              {buildNotes.map((note) => (
                <li key={note}>{note}</li>
              ))}
            </ol>
          </>
        )}
      </div>

      <Link to="/" className="mt-6 inline-block text-sm text-slate-600 underline hover:text-slate-900">
        ← Back to all modules
      </Link>
    </div>
  );
}
