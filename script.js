// 美股基金涨跌助手 - 核心逻辑

const DATA_URL = 'data.json';
const FALLBACK_INDEX_API = 'https://api.allorigins.win/raw?url=' + encodeURIComponent('https://query1.finance.yahoo.com/v8/finance/chart/%5EIXIC');

let fundData = [];
let sortAsc = false;
let selectedIndex = null;

// ==================== 数据加载 ====================

async function refreshData() {
  const btn = document.querySelector('.btn-refresh');
  btn.classList.add('spinning');
  document.getElementById('updateTime').textContent = '正在刷新...';

  try {
    await Promise.all([loadFundData(), loadIndexData()]);
    const now = new Date();
    document.getElementById('updateTime').textContent =
      `数据更新于 ${now.toLocaleString('zh-CN')}`;
  } catch (e) {
    document.getElementById('updateTime').textContent = '数据加载失败，使用缓存数据';
    console.error('数据加载失败:', e);
  } finally {
    btn.classList.remove('spinning');
  }
}

async function loadFundData() {
  try {
    const resp = await fetch(DATA_URL + '?t=' + Date.now(), { cache: 'no-cache' });
    const data = await resp.json();
    fundData = data.funds || [];
    renderFundList();
  } catch (e) {
    console.warn('基金数据加载失败，使用默认数据');
    fundData = getDefaultFunds();
    renderFundList();
  }
}

async function loadIndexData() {
  // 优先使用 data.json 中的指数数据
  try {
    const resp = await fetch(DATA_URL + '?t=' + Date.now(), { cache: 'no-cache' });
    const data = await resp.json();
    if (data.indices) {
      renderIndices(data.indices);
      return;
    }
  } catch (e) {}

  // 降级：尝试从 Yahoo Finance 获取实时数据
  try {
    const symbols = [
      { id: 'nasdaq', symbol: '%5EIXIC', name: '纳斯达克' },
      { id: 'sp500', symbol: '%5EGSPC', name: '标普500' },
      { id: 'dji', symbol: '%5EDJI', name: '道琼斯' }
    ];

    for (const s of symbols) {
      try {
        const url = `https://api.allorigins.win/raw?url=${encodeURIComponent('https://query1.finance.yahoo.com/v8/finance/chart/' + s.symbol)}`;
        const resp = await fetch(url, { signal: AbortSignal.timeout(5000) });
        const json = await resp.json();
        const result = json?.chart?.result?.[0];
        if (result) {
          const meta = result.meta;
          const changePercent = meta.regularMarketPrice && meta.previousClose
            ? ((meta.regularMarketPrice - meta.previousClose) / meta.previousClose * 100)
            : null;
          updateIndexCard(s.id, changePercent);
        }
      } catch (e) {
        console.warn(`获取${s.name}数据失败:`, e.message);
      }
    }
    updateFxRate();
  } catch (e) {
    console.warn('指数数据获取失败');
  }
}

// ==================== 渲染 ====================

function renderIndices(indices) {
  for (const key in indices) {
    updateIndexCard(key, indices[key]);
  }
}

function updateIndexCard(id, changePercent) {
  const el = document.getElementById('val-' + id);
  if (!el || changePercent === null || changePercent === undefined) return;

  const val = changePercent.toFixed(2);
  el.textContent = (changePercent >= 0 ? '+' : '') + val + '%';

  el.className = 'index-value';
  if (changePercent > 0) el.classList.add('up');
  else if (changePercent < 0) el.classList.add('down');
  else el.classList.add('neutral');
}

async function updateFxRate() {
  try {
    const url = 'https://api.allorigins.win/raw?url=' + encodeURIComponent('https://open.er-api.com/v6/latest/USD');
    const resp = await fetch(url, { signal: AbortSignal.timeout(5000) });
    const json = await resp.json();
    if (json?.rates?.CNY) {
      const rate = json.rates.CNY;
      const prevRate = 7.25; // 近似前值
      const change = ((rate - prevRate) / prevRate * 100);
      updateIndexCard('fx', change);
    }
  } catch (e) {
    console.warn('汇率获取失败');
  }
}

function renderFundList() {
  const container = document.getElementById('fundList');
  if (!fundData.length) {
    container.innerHTML = '<div class="loading">暂无基金数据</div>';
    return;
  }

  let list = [...fundData];

  // 按选中指数筛选
  if (selectedIndex) {
    list = list.filter(f => f.indexTag === selectedIndex);
  }

  // 排序
  list.sort((a, b) => sortAsc ? a.change - b.change : b.change - a.change);

  container.innerHTML = list.map(f => {
    const changeStr = f.change >= 0 ? '+' + f.change.toFixed(2) : f.change.toFixed(2);
    const changeClass = f.change > 0 ? 'up' : f.change < 0 ? 'down' : 'neutral';
    const tag = f.tag || 'QDII';
    const code = f.code || '';
    return `
      <div class="fund-item" data-code="${code}">
        <div class="fund-left">
          <span class="fund-tag">${tag}</span>
          <span class="fund-name">${f.name}</span>
          ${code ? `<span class="fund-code">${code}</span>` : ''}
        </div>
        <span class="fund-change ${changeClass}">${changeStr}%</span>
      </div>
    `;
  }).join('');
}

// ==================== 交互 ====================

function toggleSort() {
  sortAsc = !sortAsc;
  document.getElementById('sortArrow').textContent = sortAsc ? '↑' : '↓';
  renderFundList();
}

// 指数卡片点击筛选
document.addEventListener('click', function(e) {
  const card = e.target.closest('.index-card');
  if (!card) return;

  const idMap = {
    'card-nasdaq': 'nasdaq',
    'card-sp500': 'sp500',
    'card-dji': 'dji',
    'card-fx': null
  };

  const tag = idMap[card.id];
  if (selectedIndex === tag) {
    selectedIndex = null;
    card.classList.remove('selected');
  } else {
    document.querySelectorAll('.index-card').forEach(c => c.classList.remove('selected'));
    selectedIndex = tag;
    if (tag) card.classList.add('selected');
  }
  renderFundList();
});

// ==================== 默认数据 ====================

function getDefaultFunds() {
  return [
    { name: '华夏全球科技先锋', code: '005698', change: -0.29, tag: '夜盘' },
    { name: '易方达全球成长精选', code: '012920', change: -0.21, tag: '夜盘' },
    { name: '国富全球科技互联', code: '006373', change: -0.12, tag: '夜盘' },
    { name: '嘉实全球产业升级', code: '017730', change: -0.11, tag: '夜盘' },
    { name: '银海海外数字经济', code: '015203', change: -0.10, tag: '夜盘' },
    { name: '浦银安盛全球智能科技', code: '006555', change: -0.10, tag: '夜盘' },
    { name: '华夏移动互联', code: '002891', change: -0.10, tag: '夜盘' },
    { name: '天弘全球高端制造', code: '016664', change: -0.08, tag: '夜盘' },
    { name: '华宝纳斯达克精选', code: '017436', change: -0.07, tag: '夜盘' },
    { name: '汇添富全球移动互联', code: '001668', change: -0.07, tag: '夜盘' },
    { name: '景顺长城纳斯达克科技', code: '017091', change: -0.07, tag: '夜盘' },
    { name: '嘉实美国成长', code: '000043', change: -0.05, tag: '夜盘' },
    { name: '华宝致远混合', code: '008253', change: -0.04, tag: '夜盘' },
    { name: '长城全球新能源车', code: '501226', change: -0.03, tag: '夜盘' },
    { name: '广发全球精选股票', code: '270023', change: -0.02, tag: '夜盘' },
    { name: '大成纳斯达克100', code: '000834', change: -0.01, tag: '夜盘' },
  ];
}

// ==================== 初始化 ====================

function init() {
  const now = new Date();
  document.getElementById('updateTime').textContent =
    `数据更新于 ${now.toLocaleString('zh-CN')}`;
  loadFundData();
  loadIndexData();

  // 每5分钟自动刷新
  setInterval(refreshData, 5 * 60 * 1000);
}

init();
