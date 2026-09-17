/**
 * Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
 */
/** 导出当前表格数据为 CSV（UTF-8 BOM） */
export function downloadTableCsv(
  filename: string,
  headers: string[],
  rows: Array<Array<string | number | null | undefined>>,
) {
  const escape = (cell: string | number | null | undefined) => {
    const s = cell === undefined || cell === null ? '' : String(cell);
    return `"${s.replace(/"/g, '""')}"`;
  };
  const csv = [headers.join(','), ...rows.map((row) => row.map(escape).join(','))].join('\n');
  const blob = new Blob(['\uFEFF' + csv], { type: 'text/csv;charset=utf-8;' });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = filename;
  a.click();
  URL.revokeObjectURL(url);
}
