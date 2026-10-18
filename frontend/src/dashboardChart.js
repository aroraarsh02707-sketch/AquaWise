const chartGeometry = {
  center: 120,
  innerRadius: 82,
  outerRadius: 109,
  gapRadians: (3 * Math.PI) / 180,
};

function pointAt(radius, angle) {
  return {
    x: chartGeometry.center + radius * Math.cos(angle),
    y: chartGeometry.center + radius * Math.sin(angle),
  };
}

function arcPath(startAngle, endAngle) {
  const span = endAngle - startAngle;
  const gap = Math.min(chartGeometry.gapRadians / 2, span / 4);
  const start = startAngle + gap;
  const end = endAngle - gap;
  const outerStart = pointAt(chartGeometry.outerRadius, start);
  const outerEnd = pointAt(chartGeometry.outerRadius, end);
  const innerEnd = pointAt(chartGeometry.innerRadius, end);
  const innerStart = pointAt(chartGeometry.innerRadius, start);
  const largeArc = end - start > Math.PI ? 1 : 0;

  return [
    `M ${outerStart.x} ${outerStart.y}`,
    `A ${chartGeometry.outerRadius} ${chartGeometry.outerRadius} 0 ${largeArc} 1 ${outerEnd.x} ${outerEnd.y}`,
    `L ${innerEnd.x} ${innerEnd.y}`,
    `A ${chartGeometry.innerRadius} ${chartGeometry.innerRadius} 0 ${largeArc} 0 ${innerStart.x} ${innerStart.y}`,
    'Z',
  ].join(' ');
}

export function createDonutSegments(categories, colors) {
  const chartData = categories
    .map((item) => ({ ...item, value: Number(item.litres_per_day) || 0 }))
    .filter((item) => item.value > 0);
  const total = chartData.reduce((sum, item) => sum + item.value, 0);
  if (!total) return [];

  let accumulated = 0;
  return chartData.map((item, index) => {
    const startAngle = -Math.PI / 2 + (accumulated / total) * 2 * Math.PI;
    accumulated += item.value;
    const endAngle = -Math.PI / 2 + (accumulated / total) * 2 * Math.PI;

    return {
      ...item,
      color: colors[index % colors.length],
      path: arcPath(startAngle, endAngle),
    };
  });
}
