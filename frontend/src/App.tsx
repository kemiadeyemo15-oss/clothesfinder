import { useState } from "react";
import { search, type Attributes, type Result } from "./api";
import { SearchBar } from "./components/SearchBar";
import { ResultsList } from "./components/ResultsList";

function parsedLine(q: Attributes): string {
  const bits: string[] = [];
  if (q.category) bits.push(q.category);
  if (q.colours.length) bits.push(q.colours.join("/"));
  if (q.materials.length) bits.push(q.materials.join("/"));
  if (q.silhouettes.length) bits.push(q.silhouettes.join(", "));
  if (q.price_max) bits.push(`≤ £${q.price_max}`);
  return bits.join("  ·  ");
}

export default function App() {
  const [busy, setBusy] = useState(false);
  const [query, setQuery] = useState<Attributes | null>(null);
  const [results, setResults] = useState<Result[] | null>(null);
  const [error, setError] = useState<string | null>(null);

  async function run(text: string, image: string | null) {
    setBusy(true);
    setError(null);
    try {
      const data = await search(text, image);
      setQuery(data.query);
      setResults(data.results);
    } catch (e) {
      setError(e instanceof Error ? e.message : "something went wrong");
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="wrap">
      <header>
        <h1>clothesfinder</h1>
        <p>Describe it, show it, or both. Trusted retailers only — no marketplaces, no 50-day shipping.</p>
      </header>

      <SearchBar onSearch={run} busy={busy} />

      {query && (
        <div className="parsed">
          reading as → <b>{parsedLine(query) || "no attributes detected"}</b>
        </div>
      )}
      {error && <div className="empty">{error}</div>}
      {results && <ResultsList results={results} />}
    </div>
  );
}
