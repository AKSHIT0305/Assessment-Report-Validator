export default function ErrorDetails({ error }: { error: any }) {
  return (
    <article>
      <strong>{error?.message ?? "Validation error"}</strong>
      <div>Sheet: {error?.sheet ?? "-"}</div>
      <div>Cell: {error?.cell ?? "-"}</div>
      <div>Expected: {String(error?.expected ?? "-")}</div>
      <div>Actual: {String(error?.actual ?? "-")}</div>
    </article>
  );
}
