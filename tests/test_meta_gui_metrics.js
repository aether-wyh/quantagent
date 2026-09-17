'use strict';
// Run with node --test tests/test_meta_gui_metrics.js from this isolated revision.
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const assert = require('node:assert/strict');
const test = require('node:test');

class Element {
  constructor(tag = 'div') {
    this.tagName = tag;
    this.children = [];
    this.dataset = {};
    this.style = {};
    this.hidden = false;
    this._text = '';
    this.value = '';
    this.classList = { toggle() {} };
  }
  set textContent(value) { this._text = String(value); this.children = []; }
  get textContent() { return this._text + this.children.map(child => child.textContent || '').join(''); }
  append(...children) { this.children.push(...children); }
  replaceChildren(...children) { this.children = children; this._text = ''; }
  addEventListener() {}
  setAttribute() {}
  querySelector() { return null; }
}

function loadPage() {
  const filename = path.resolve(__dirname, '../src/quanta_agents/meta/web/index.html');
  const html = fs.readFileSync(filename, 'utf8');
  const script = html.match(/<script>([\s\S]*?)<\/script>/)[1];
  new vm.Script(script); // Parse the complete production script, including bootstrap.
  assert(!script.includes('innerHTML'), 'dynamic rendering must use text nodes');
  const ids = [...html.matchAll(/\bid="([^"]+)"/g)].map(match => match[1]);
  assert.equal(new Set(ids).size, ids.length, 'duplicate DOM ids');
  const elements = new Map(ids.map(id => [id, new Element()]));
  const context = {
    document: {
      getElementById(id) { assert(elements.has(id), 'unknown DOM id: ' + id); return elements.get(id); },
      createElement: tag => new Element(tag),
    },
    console, Date, Intl, Number, Set, Object, JSON, Math, AbortController,
    setTimeout() {}, clearTimeout() {}, setInterval() {},
  };
  vm.createContext(context);
  // Do not bootstrap networking. Execute actual formatting and render functions.
  const bootstrap = script.lastIndexOf("    $('liveStart').addEventListener");
  assert(bootstrap > 0);
  vm.runInContext(script.slice(0, bootstrap), context);
  return { elements, context, run: expression => vm.runInContext(expression, context) };
}

function comparisonRows(element) {
  const table = element.children.find(child => child.tagName === 'table');
  assert(table, 'comparison table is missing');
  const body = table.children.find(child => child.tagName === 'tbody');
  return new Map(body.children.map(row => [row.children[0].textContent,
    row.children.slice(1).map(cell => cell.textContent)]));
}

const realMetrics = {
  sharpe_ratio: -0.107,
  annual_return: -0.03,
  max_drawdown: -528547.0055,
  max_ddpercent: -0.497585,
  total_trade_count: 1377,
  completed_exit_orders: 622,
};

test('real research summary uses percentage drawdown and separately labelled CNY amount', () => {
  const page = loadPage();
  page.context.observation = { case_id: 'ashare_csi500_price_repair_v1', metrics: realMetrics };
  const summary = page.run('evidenceSummary(observation)');
  assert(summary.includes('夏普 -0.107'));
  assert(summary.includes('最大回撤 -49.76%'));
  assert(summary.includes('最大回撤金额 -528,547.01 元'));
  assert(summary.includes('成交订单数 1,377'));
  assert(summary.includes('已实现卖出订单数 622'));
  assert(!summary.includes('-52854700'));
});

test('real comparison does not let amount shadow max_ddpercent and supports actual aliases', () => {
  const page = loadPage();
  page.context.fixture = {
    id: 'real', data_kind: 'ashare_daily', config: { final_opened: false },
    comparison: { scope: 'real_case_development_integration', final_opened: false,
      baseline: { score: -0.107, metrics: realMetrics, eligible: true },
      candidate: { score: 0, metrics: { ...realMetrics, max_ddpercent: 0, max_drawdown: 0,
        total_trade_count: 0, completed_exit_orders: 0 }, eligible: false }, score_delta: 0.107 },
  };
  page.run('renderComparison(fixture)');
  const rows = comparisonRows(page.elements.get('comparisonBody'));
  assert.deepEqual(rows.get('最大回撤'), ['-49.76%', '0.00%']);
  assert.deepEqual(rows.get('最大回撤金额'), ['-528,547.01 元', '0.00 元']);
  assert.deepEqual(rows.get('成交订单数'), ['1,377', '0']);
  assert.deepEqual(rows.get('已实现卖出订单数'), ['622', '0']);
  assert.deepEqual(rows.get('夏普'), ['-0.107', '-0.107']);
});

test('legacy synthetic summary and comparison keep ratio drawdown and completed trades', () => {
  const page = loadPage();
  const metrics = { sharpe: 0.4, max_drawdown: -0.125, annualized_return: 0.08,
    completed_trades: 14, turnover_over_initial_cash: 3.5 };
  page.context.observation = { case_id: 'synthetic_trend_reversal_v1', metrics };
  const summary = page.run('evidenceSummary(observation)');
  assert(summary.includes('最大回撤 -12.50%'));
  assert(summary.includes('年化收益 8.00%'));
  assert(summary.includes('完成交易 14'));
  assert(summary.includes('成交额 / 初始资金 3.50 倍'));
  assert(!summary.includes('回撤金额'));
  page.context.fixture = { id: 'synthetic', data_kind: 'synthetic_fixture', comparison: {
    baseline: { metrics, score: 0.4 }, candidate: { metrics, score: 0.4 }, score_delta: 0 } };
  page.run('renderComparison(fixture)');
  const rows = comparisonRows(page.elements.get('comparisonBody'));
  assert.deepEqual(rows.get('最大回撤'), ['-12.50%', '-12.50%']);
  assert(!rows.has('最大回撤金额'));
});

test('yearly A-share max_drawdown is explicitly a ratio; portfolio amount cannot substitute', () => {
  const page = loadPage();
  assert.equal(page.run("metricDefinitions('ashare','yearly').find(x=>x.label==='最大回撤').keys[0]"), 'max_drawdown');
  assert.equal(page.run("metricDefinitions('ashare','yearly').find(x=>x.label==='最大回撤').unit"), 'ratio');
  assert.equal(page.run("metricDefinitions('ashare').find(x=>x.label==='最大回撤').keys[0]"), 'max_ddpercent');
  assert.equal(page.run("readMetric({max_drawdown:-528547},metricDefinitions('ashare').find(x=>x.label==='最大回撤'))"), undefined);
  assert.equal(page.run("formatMetric(-0.125,'ratio')"), '-12.50%');
});

test('missing, nonfinite and wrong-type metrics remain unknown and aliases produce one row', () => {
  const page = loadPage();
  for (const value of ['undefined', 'null', 'NaN', 'Infinity', '"0.25"']) {
    assert.equal(page.run(`formatMetric(${value},'ratio')`), '—');
  }
  assert.equal(page.run("readMetric({sharpe_ratio:null,sharpe:0.5},metricDefinitions('ashare')[0])"), 0.5);
  page.context.fixture = { id: 'partial', data_kind: 'ashare_daily', config: {}, comparison: {
    baseline: { metrics: { max_ddpercent: null, max_drawdown: -100, annual_return: 0.1,
      annualized_return: 999 } }, candidate: { metrics: {} } } };
  page.run('renderComparison(fixture)');
  const rows = comparisonRows(page.elements.get('comparisonBody'));
  assert.deepEqual(rows.get('最大回撤'), ['—', '—']);
  assert.deepEqual(rows.get('最大回撤金额'), ['-100.00 元', '—']);
  assert.deepEqual(rows.get('年化收益'), ['10.00%', '—']);
});

test('single-arm development comparison marks other arm unarranged and never calls it out of sample', () => {
  const page = loadPage();
  page.context.fixture = { id: 'development-arm-02', data_kind: 'ashare_daily',
    config: { case_config: { task: 'relative_strength' }, evaluation_split: 'development',
      research_config: { only_architecture: 'candidate' }, research_calls_per_architecture: 12 },
    research: { baseline: [], candidate: [] }, calls: [], self_checks: [], comparison: {
      scope: 'frozen_architecture_development_comparison', score_delta: null,
      arm_results: { candidate: { score: -0.107, metrics: realMetrics, eligible: true } } } };
  page.run('state.run=fixture;renderComparison(fixture);renderResearch(fixture)');
  const rows = comparisonRows(page.elements.get('comparisonBody'));
  assert.deepEqual(rows.get('评测分数'), ['未安排', '-0.107']);
  assert.deepEqual(rows.get('最大回撤'), ['未安排', '-49.76%']);
  assert.deepEqual(rows.get('样本与交易门槛'), ['未安排', '满足']);
  const text = page.elements.get('comparisonBody').textContent;
  assert(text.includes('开发期复核，非样本外结果'));
  assert(text.includes('本次不访问确认期和最终保留期'));
  assert(!text.includes('确认期独立评测'));
  assert(!text.includes('候选 − 基线分数'));
  assert(page.elements.get('researchCards').textContent.includes('未安排'));
  assert(page.elements.get('researchCards').textContent.includes('0 / 12 轮'));
  assert(page.run('runName(fixture)').includes('相对强弱 · 候选'));
});

test('frozen order and configured 18-call research budget are displayed', () => {
  const page = loadPage();
  page.context.fixture = { id: 'ordered', data_kind: 'ashare_daily',
    task_key: 'volume_expansion', only_architecture: 'baseline',
    config: { phase_order: ['prepare', 'meta_proposal', 'candidate_initial', 'baseline_initial'],
      phase_labels: { meta_proposal: '复用冻结方法' },
      experiment_protocol: { max_research_calls_per_architecture: 18 } },
    research: { baseline: [], candidate: [] }, calls: [], self_checks: [] };
  assert.equal(page.run('runPhases(fixture)[1][1]'), '复用冻结方法');
  assert.equal(page.run('runPhases(fixture)[2][0]'), 'candidate_initial');
  page.run('state.run=fixture;renderResearch(fixture)');
  assert(page.elements.get('researchCards').textContent.includes('0 / 18 轮'));
  assert(page.run('runName(fixture)').includes('成交量扩张 · 基线'));
});

test('UI creation sends task/call controls only for A-share and defaults remain six calls', async () => {
  const page = loadPage();
  const html = fs.readFileSync(path.resolve(__dirname, '../src/quanta_agents/meta/web/index.html'), 'utf8');
  assert(html.includes('<option value="6" selected>每架构 6 轮</option>'));
  page.elements.get('caseSelect').value = 'ashare';
  page.elements.get('taskSelect').value = 'price_breakout';
  page.elements.get('roundSelect').value = '12';
  page.run("state.online=true;api=async (path,options)=>{globalThis.sent=JSON.parse(options.body);return {run_id:'created'};};selectRun=()=>{};");
  await page.run("createRun('fixture')");
  assert.deepEqual(JSON.parse(JSON.stringify(page.context.sent)), {
    mode: 'fixture', case: 'ashare', task: 'price_breakout', research_calls: 12 });
  page.elements.get('caseSelect').value = 'synthetic';
  await page.run("createRun('fixture')");
  assert.deepEqual(JSON.parse(JSON.stringify(page.context.sent)), { mode: 'fixture', case: 'synthetic' });
});

test('batch card shows bounded progress, unknown usage, active run and development scope', () => {
  const page = loadPage();
  page.run('renderBatches([])');
  assert.equal(page.elements.get('batchPanel').hidden, true);
  page.context.batch = { batch_id: 'batch-01', status: 'waiting', scope: 'development_only',
    counts: { planned: 8, completed: 2, failed: 1, active: 1, not_started: 4,
      cancelled: 0, attention: 0 },
    usage: { known_tokens: 100000, is_partial: true, unknown_entries: 1,
      reserved_tokens: 1000000, accident_token_limit: 8000000 },
    current_entry_id: 'case_repeat_candidate', current_run_id: 'run-03',
    elapsed_seconds: 91, updated_at: '2026-09-06T02:00:00Z' };
  page.run('renderBatches([batch])');
  assert.equal(page.elements.get('batchPanel').hidden, false);
  assert.equal(page.elements.get('batchCounts').textContent, '8 / 2 / 1');
  assert.equal(page.elements.get('batchTokens').textContent, '100,000 + 未知');
  assert.equal(page.elements.get('batchLimit').textContent, '8,000,000');
  assert(page.elements.get('batchCurrent').textContent.includes('case_repeat_candidate'));
  assert(page.elements.get('batchScope').textContent.includes('非样本外'));
  assert.equal(page.elements.get('batchOpenRun').disabled, false);
  page.context.batch = { batch_id: 'broken', status: 'unavailable', report_error: '报告暂不可读' };
  page.run('renderBatches([batch])');
  assert.equal(page.elements.get('batchCounts').textContent, '— / — / —');
  assert.equal(page.elements.get('batchTokens').textContent, '—');
  assert.equal(page.elements.get('batchOpenRun').disabled, true);
});
