const https = require('https');
const crypto = require('crypto');

const TARGET_WALLET = '0xb27bc932bf8110d8f78e55da7d5f0497a18b5b82'.toLowerCase();
const POLYMARKET_API = 'https://clob.polymarket.com';

let executionHistory = [];
let pendingExecutions = [];

function fetchURL(url, headers = {}, method = 'GET', body = null) {
  return new Promise((resolve, reject) => {
    const urlObj = new URL(url);
    const options = {
      hostname: urlObj.hostname,
      path: urlObj.pathname + urlObj.search,
      method,
      headers: {
        'User-Agent': 'Mozilla/5.0',
        'Content-Type': 'application/json',
        ...headers
      },
      timeout: 8000
    };

    const req = https.request(options, (res) => {
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

    if (body) req.write(JSON.stringify(body));
    req.end();
  });
}

async function getWalletTrades() {
  try {
    const url = `${POLYMARKET_API}/user-history?address=${TARGET_WALLET}&limit=20`;
    const trades = await fetchURL(url);
    return trades ? trades.history || [] : [];
  } catch (error) {
    console.error('Error fetching wallet trades:', error.message);
    return [];
  }
}

async function executeTradeIfNeeded(trade) {
  if (!trade || !trade.token_id || !trade.side) {
    return { success: false, error: 'Invalid trade data' };
  }

  const tradeKey = `${trade.token_id}_${trade.side}_${trade.price}`;

  // Check if already executed
  if (executionHistory.some(t => t.key === tradeKey &&
      Date.now() - t.timestamp < 60000)) {
    return { success: false, error: 'Trade already executed recently' };
  }

  // In production, this would:
  // 1. Sign the order with your private key
  // 2. Submit to Polymarket CLOB
  // 3. Track execution status

  const execution = {
    key: tradeKey,
    timestamp: Date.now(),
    token_id: trade.token_id,
    side: trade.side,
    price: trade.price,
    size: trade.size || 1,
    status: 'pending'
  };

  pendingExecutions.push(execution);
  executionHistory.push(execution);

  // Keep history to last 100 trades
  if (executionHistory.length > 100) {
    executionHistory = executionHistory.slice(-100);
  }

  return {
    success: true,
    execution,
    message: `Copytrade order queued: ${trade.side} ${trade.size} @ ${trade.price}`
  };
}

async function getExecutionStatus() {
  const pending = pendingExecutions.length;
  const completed = executionHistory.filter(t => t.status === 'completed').length;
  const failed = executionHistory.filter(t => t.status === 'failed').length;

  // Simulate status updates (in production, poll blockchain)
  pendingExecutions = pendingExecutions.map(exec => {
    if (Math.random() > 0.7) {
      exec.status = 'completed';
    }
    return exec;
  }).filter(exec => exec.status === 'pending');

  return {
    pending,
    completed,
    failed,
    totalExecuted: completed + failed,
    recentTrades: executionHistory.slice(-10),
    successRate: completed + failed > 0 ?
      ((completed / (completed + failed)) * 100).toFixed(1) : 0
  };
}

exports.handler = async (event, context) => {
  try {
    const { action = 'status' } = event.queryStringParameters || {};

    let result;

    switch (action) {
      case 'trades':
        // Get wallet's recent trades
        result = await getWalletTrades();
        break;

      case 'execute':
        // Execute copytrade based on wallet activity
        const trades = await getWalletTrades();
        const executions = [];

        for (const trade of trades.slice(0, 3)) {
          const execution = await executeTradeIfNeeded(trade);
          executions.push(execution);
        }

        result = { executions, message: 'Copytrade execution processed' };
        break;

      case 'status':
      default:
        result = await getExecutionStatus();
        break;
    }

    return {
      statusCode: 200,
      headers: {
        'Content-Type': 'application/json',
        'Access-Control-Allow-Origin': '*',
        'Cache-Control': 'max-age=10'
      },
      body: JSON.stringify({
        action,
        wallet: TARGET_WALLET,
        ...result,
        timestamp: new Date().toISOString()
      })
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
