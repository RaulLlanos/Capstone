export default function Table({ columns, data, emptyText = "Sin datos", getRowProps }) {
  return (
    <div style={{ overflowX: "auto" }}>
      <table style={{ width: "100%", borderCollapse: "collapse" }}>
        <thead>
          <tr>
            {columns.map((c) => (
              <th
                key={c.key}
                style={{
                  textAlign: "left",
                  borderBottom: "1px solid #eee",
                  padding: "8px",
                }}
              >
                {c.title}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {data.length === 0 ? (
            <tr>
              <td colSpan={columns.length} style={{ padding: 12, color: "#666" }}>
                {emptyText}
              </td>
            </tr>
          ) : (
            data.map((row) => {
              const extra = getRowProps ? getRowProps(row) : {};
              return (
                <tr key={row.id} {...extra}>
                  {columns.map((c) => (
                    <td
                      key={c.key}
                      style={{ padding: "8px", borderBottom: "1px solid #fafafa" }}
                    >
                      {c.render ? c.render(row[c.dataIndex], row) : row[c.dataIndex]}
                    </td>
                  ))}
                </tr>
              );
            })
          )}
        </tbody>
      </table>
    </div>
  );
}
