(function() {
  var style = getComputedStyle(document.documentElement);
  var accent = style.getPropertyValue('--accent').trim();
  var accent2 = style.getPropertyValue('--accent2').trim();
  var ink = style.getPropertyValue('--ink').trim();
  var muted = style.getPropertyValue('--muted').trim();
  var rule = style.getPropertyValue('--rule').trim();
  var green = style.getPropertyValue('--green').trim();
  var blue = style.getPropertyValue('--blue').trim();

  var chart1 = echarts.init(document.getElementById('chart-gap'), null, { renderer: 'svg' });
  chart1.setOption({
    animation: false,
    tooltip: { appendToBody: true, trigger: 'axis' },
    legend: { data: ['\u5f53\u524d\u8bc4\u5206', '\u4e0e\u76ee\u6807\u5dee\u8ddd'], textStyle: { color: muted, fontSize: 12 }, top: 0 },
    grid: { left: 100, right: 40, top: 40, bottom: 30 },
    xAxis: { type: 'value', max: 10, min: 0, axisLabel: { color: muted }, splitLine: { lineStyle: { color: rule } } },
    yAxis: { type: 'category', data: ['\u4ea7\u54c1\u5546\u4e1a', '\u4ee3\u7801\u8d28\u91cf', '\u6027\u80fd\u6269\u5c55', '\u83b7\u5ba2\u80fd\u529b', '\u5b89\u5168\u5408\u89c4', '\u67b6\u6784\u8bbe\u8ba1'], axisLabel: { color: ink, fontSize: 12 }, axisLine: { lineStyle: { color: rule } } },
    series: [
      { name: '\u5f53\u524d\u8bc4\u5206', type: 'bar', data: [5.8, 5.7, 6.7, 2.9, 7.7, 7.5], itemStyle: { color: function(p) { var v = p.value; if (v >= 7.5) return green; if (v >= 5.5) return accent2; return accent; }, borderRadius: [0, 4, 4, 0] }, barWidth: 16, label: { show: true, position: 'right', color: ink, fontSize: 12, fontWeight: 700, formatter: '{c}' } },
      { name: '\u4e0e\u76ee\u6807\u5dee\u8ddd', type: 'bar', data: [3.7, 3.8, 2.8, 6.6, 1.8, 2.0], itemStyle: { color: 'rgba(239,68,68,0.35)', borderRadius: [0, 4, 4, 0] }, barWidth: 16, label: { show: true, position: 'right', color: accent, fontSize: 11, formatter: '-{c}' } }
    ]
  });
  window.addEventListener('resize', function() { chart1.resize(); });

  var chart2 = echarts.init(document.getElementById('chart-layers'), null, { renderer: 'svg' });
  chart2.setOption({
    animation: false,
    tooltip: { appendToBody: true, trigger: 'axis', axisPointer: { type: 'shadow' } },
    legend: { data: ['P0 \u81f4\u547d', 'P1 \u4e25\u91cd', 'P2 \u6539\u8fdb', '\u6b63\u5e38'], textStyle: { color: muted, fontSize: 12 }, top: 0 },
    grid: { left: 140, right: 40, top: 50, bottom: 30 },
    xAxis: { type: 'value', axisLabel: { color: muted }, splitLine: { lineStyle: { color: rule } } },
    yAxis: { type: 'category', data: ['L5 \u57fa\u7840\u8bbe\u65bd\u5c42', 'L4 \u6570\u636e\u8bb0\u5fc6\u5c42', 'L3 \u5e73\u53f0\u670d\u52a1\u5c42', 'L2 AI \u667a\u80fd\u4f53\u5c42', 'L1 \u7528\u6237\u63a5\u5165\u5c42'], axisLabel: { color: ink, fontSize: 12 }, axisLine: { lineStyle: { color: rule } } },
    series: [
      { name: 'P0 \u81f4\u547d', type: 'bar', stack: 'total', data: [0, 0, 2, 2, 0], itemStyle: { color: accent }, barWidth: 20 },
      { name: 'P1 \u4e25\u91cd', type: 'bar', stack: 'total', data: [2, 1, 1, 2, 2], itemStyle: { color: accent2 } },
      { name: 'P2 \u6539\u8fdb', type: 'bar', stack: 'total', data: [1, 0, 0, 0, 0], itemStyle: { color: blue } },
      { name: '\u6b63\u5e38', type: 'bar', stack: 'total', data: [1, 1, 1, 0, 1], itemStyle: { color: green, borderRadius: [0, 4, 4, 0] } }
    ]
  });
  window.addEventListener('resize', function() { chart2.resize(); });
})();