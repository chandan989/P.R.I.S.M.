export default function SkeletonLoader({ rows = 3 }: { rows?: number }) {
  return (
    <div aria-busy="true" aria-label="Loading">
      {Array.from({ length: rows }).map((_, i) => (
        <div key={i} className="skeleton" style={{ width: `${85 - i * 12}%` }} />
      ))}
    </div>
  );
}
