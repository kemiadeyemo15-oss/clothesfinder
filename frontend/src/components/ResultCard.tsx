import type { Result } from "../api";

// Trust/shipping is encoded in the left rule's colour, not a badge:
// teal = trusted/fast, gold = slower shipping (>= 6 days).
export function ResultCard({ r, index }: { r: Result; index: number }) {
  const slow = r.ship_days != null && r.ship_days >= 6;
  const href = r.product.url !== "unknown" ? r.product.url : null;
  const className = `card${slow ? " slow" : ""}`;
  const style = { animationDelay: `${index * 40}ms` };

  const inner = (
    <>
      <span className="title">
        {r.product.title} <span className="retailer">· {r.product.retailer}</span>
      </span>
      <span className="ship">~{r.ship_days ?? "—"}d</span>
      <span className="price">{({ GBP: "£", USD: "$", EUR: "€" } as Record<string, string>)[r.product.currency] ?? ""}{Math.round(r.product.price)}</span>
      <span className="score">{r.score.toFixed(2)}</span>
    </>
  );

  if (href) {
    return (
      <a className={className} style={style} href={href} target="_blank" rel="noreferrer">
        {inner}
      </a>
    );
  }
  return (
    <div className={className} style={style}>
      {inner}
    </div>
  );
}
