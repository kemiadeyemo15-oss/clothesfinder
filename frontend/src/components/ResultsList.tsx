import type { Result } from "../api";
import { ResultCard } from "./ResultCard";

export function ResultsList({ results }: { results: Result[] }) {
  if (!results.length) {
    return <div className="empty">Nothing trusted matched. Loosen the description.</div>;
  }
  return (
    <div className="results">
      {results.map((r, i) => (
        <ResultCard key={r.product.id} r={r} index={i} />
      ))}
    </div>
  );
}
