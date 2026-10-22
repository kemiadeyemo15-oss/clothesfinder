// Thin API client. In dev, Vite proxies /api -> backend. In prod, set
// VITE_API_URL to the deployed backend origin.
const BASE = import.meta.env.VITE_API_URL ?? "/api";

export interface Attributes {
  category: string | null;
  colours: string[];
  materials: string[];
  silhouettes: string[];
  price_max: number | null;
}

export interface Product {
  id: string;
  title: string;
  retailer: string;
  price: number;
  currency: string;
  url: string;
  image: string;
  category: string | null;
}

export interface Result {
  product: Product;
  similarity: number;
  trust: number;
  ship_days: number | null;
  score: number;
}

export interface SearchResponse {
  query: Attributes;
  results: Result[];
  took_ms: number;
}

export async function search(text: string, image: string | null): Promise<SearchResponse> {
  const res = await fetch(`${BASE}/search`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ text: text || null, image }),
  });
  if (!res.ok) throw new Error(`search failed: ${res.status}`);
  return res.json();
}
