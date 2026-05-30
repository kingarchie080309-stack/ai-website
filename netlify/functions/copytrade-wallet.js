const https = require('https');

const TARGET_WALLET = '0xb27bc932bf8110d8f78e55da7d5f0497a18b5b82'.toLowerCase();
const CACHE_TTL = 30000; // 30 seconds

let walletTradesCache = null;
let cacheTimestamp = 0;

function fetchURL(url, headers = {}) {
  return new Promise((resolve, reject) => {
    const req = https.get(url, {
      headers: {
        'User-Agent': 'Mozilla/5.0',
        ...headers
      },
      timeout: 8000
    }, (res) => {
      let data = '';
      res.on('data', chunk => data += chunk);
      res.on('end', () => {
        try {
          resolve(JSON.parse(data));
        } catch (e) {
          resolve(null);
        }
      });
    });

    req.on('error', () => resolve(null));
    req.on('timeout', () => {
      req.destroy();
      resolve(null);
    });
  });
}

async function fetchWalletTrades() {
  try {
    // Get wallet portfolio from Polymarket API
    const portfolioUrl = `https://clob.polymarket.com/user-portfolio?address=${TARGET_WALLET}`;
    const portfolio = await fetchURL(portfolioUrl);

    if (!portfolio || !portfolio.portfolio) {
      return { positions: [], recentTrades: [], stats: {} };
    }

    // Extract positions
    const positions = [];
    for (const position of portfolio.portfolio || []) {
      if (position.balance > 0 || position.position > 0) {
        positions.push({
          token_id: position.token_id,
          outcome: position.outcome || position.side,
          balance: parseFloat(position.balance) || 0,
          value: parseFloat(position.value) || 0,
          avg_price: parseFloat(position.avg_price) || 0
        });
      }
    }

    // Get recent trades
    const tradesUrl = `https://clob.polymarket.com/user-history?address=${TARGET_WALLET}&limit=50`;
    const tradesData = await fetchURL(tradesUrl);

    const recentTrades = [];
    if (tradesData && tradesData.history) {
      for (const trade of tradesData.history.slice(0, 20)) {
        recentTrades.push({
          id: trade.order_id || trade.id,
          timestamp: trade.timestamp,
          market: trade.market_question || trade.market,
          side: trade.side === 'BUY' ? 'BUY' : 'SELL',
          outcome: trade.outcome,
          size: parseFloat(trade.size) || 0,
          price: parseFloat(trade.price) || 0,
          total: (parseFloat(trade.size) || 0) * (parseFloat(trade.price) || 0),
          tx_hash: trade.tx_hash
        });
      }
    }

    return {
      positions,
      recentTrades,
      stats: {
        totalPositions: positions.length,
        totalValue: positions.reduce((sum, p) => sum + (p.value || 0), 0),
        lastUpdate: new Date().toISOString()
      }
    };
  } catch (error) {
    console.error('Copytrade fetch error:', error.message);
    return { positions: [], recentTrades: [], stats: {} };
  }
}

async function analyzeWalletStrategy() {
  const trades = await fetchWalletTrades();

  if (!trades.recentTrades || trades.recentTrades.length === 0) {
    return {
      strategy: 'monitoring',
      confidence: 0,
      topMarkets: [],
      tradingPattern: 'insufficient_data'
    };
  }

  // Analyze trading patterns
  const buyTrades = trades.recentTrades.filter(t => t.side === 'BUY');
  const sellTrades = trades.recentTrades.filter(t => t.side === 'SELL');

  const winRate = calculateWinRate(trades);
  const avgTradeSize = (trades.recentTrades.reduce((sum, t) => sum + t.size, 0) / trades.recentTrades.length).toFixed(2);

  // Group by market to find focus areas
  const marketFreq = {};
  trades.recentTrades.forEach(t => {
    marketFreq[t.market] = (marketFreq[t.market] || 0) + 1;
  });

  const topMarkets = Object.entries(marketFreq)
    .sort((a, b) => b[1] - a[1])
    .slice(0, 5)
    .map(([market, count]) => ({ market, trades: count }));

  return {
    strategy: determineTradingStrategy(buyTrades, sellTrades),
    confidence: Math.min(100, (trades.recentTrades.length / 2) * 10),
    topMarkets,
    tradingPattern: {
      buyCount: buyTrades.length,
      sellCount: sellTrades.length,
      avgTradeSize,
      winRate: (winRate * 100).toFixed(1) + '%'
    }
  };
}

function calculateWinRate(trades) {
  if (!trades.positions || trades.positions.length === 0) return 0.5;

  const profitablePositions = trades.positions.filter(p => p.value > p.balance * p.avg_price).length;
  return profitablePositions / Math.max(1, trades.positions.length);
}

function determineTradingStrategy(buyTrades, sellTrades) {
  if (buyTrades.length > sellTrades.length * 2) return 'accumulating';
  if (sellTrades.length > buyTrades.length * 2) return 'distributing';
  if (buyTrades.length > 10) return 'active_trader';
  return 'swing_trader';
}

exports.handler = async (event, context) => {
  try {
    // Check cache
    const now = Date.now();
    if (walletTradesCache && (now - cacheTimestamp) < CACHE_TTL) {
      return {
        statusCode: 200,
        headers: {
          'Content-Type': 'application/json',
          'Access-Control-Allow-Origin': '*',
          'Cache-Control': 'max-age=30'
        },
        body: JSON.stringify({
          ...walletTradesCache,
          cached: true,
          cacheAge: now - cacheTimestamp
        })
      };
    }

    const trades = await fetchWalletTrades();
    const strategy = await analyzeWalletStrategy();

    const response = {
      wallet: TARGET_WALLET,
      positions: trades.positions,
      recentTrades: trades.recentTrades,
      strategy,
      stats: trades.stats,
      timestamp: new Date().toISOString()
    };

    // Update cache
    walletTradesCache = response;
    cacheTimestamp = now;

    return {
      statusCode: 200,
      headers: {
        'Content-Type': 'application/json',
        'Access-Control-Allow-Origin': '*',
        'Cache-Control': 'max-age=30'
      },
      body: JSON.stringify(response)
    };
  } catch (error) {
    console.error('Function error:', error);
    return {
      statusCode: 500,
      headers: { 'Access-Control-Allow-Origin': '*' },
      body: JSON.stringify({ error: error.message })
    };
  }
};
