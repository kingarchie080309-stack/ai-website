const https = require('https');

function fetchURL(url) {
  return new Promise((resolve, reject) => {
    const req = https.get(url, {
      headers: {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)'
      },
      timeout: 5000
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

async function fetchKalshiMarkets() {
  try {
    const data = await fetchURL('https://api.kalshi.com/trade-api/v2/markets?limit=100&category=crypto');

    if (!data || !data.markets) return null;

    const btcMarkets = data.markets.filter(m =>
      m.title && m.title.includes('BTC') &&
      (m.title.includes('15') || m.title.includes('15 min'))
    );

    if (btcMarkets.length === 0) return null;

    const market = btcMarkets[0];
    const targetMatch = market.subtitle?.match(/\$([0-9,]+(?:\.[0-9]+)?)/);
    const target = targetMatch ?
      parseFloat(targetMatch[1].replace(/,/g, '')) :
      (market.strike_price || 0);

    return {
      platform: 'kalshi',
      title: market.title,
      target: target,
      yes: market.last_price || 0.5,
      no: 1 - (market.last_price || 0.5),
      volume: market.volume || 0
    };
  } catch (error) {
    console.error('Kalshi error:', error.message);
    return null;
  }
}

async function fetchPolymarketMarkets() {
  try {
    // Fetch markets
    const data = await fetchURL('https://clob.polymarket.com/markets?limit=100');

    if (!data) return null;

    const btcMarkets = data.filter(m =>
      m.question && m.question.includes('Bitcoin') &&
      m.question.includes('15')
    );

    if (btcMarkets.length === 0) return null;

    const market = btcMarkets[0];
    const targetMatch = market.question.match(/\$([0-9,]+(?:\.[0-9]+)?)/);
    const target = targetMatch ?
      parseFloat(targetMatch[1].replace(/,/g, '')) : 0;

    // Fetch orderbook for current prices
    const obData = await fetchURL(`https://clob.polymarket.com/orderbook/${market.token_id}`);

    let yesPrice = 0.5;
    let noPrice = 0.5;

    if (obData && obData.bids && obData.bids.length > 0) {
      yesPrice = parseFloat(obData.bids[0].price) || 0.5;
      noPrice = 1 - yesPrice;
    }

    return {
      platform: 'polymarket',
      title: market.question,
      target: target,
      yes: yesPrice,
      no: noPrice,
      volume: market.volume_24h || 0
    };
  } catch (error) {
    console.error('Polymarket error:', error.message);
    return null;
  }
}

function analyzeOpportunities(kalshi, polymarket) {
  const opportunities = [];

  if (!kalshi || !polymarket) {
    return opportunities;
  }

  const targetDiff = Math.abs(kalshi.target - polymarket.target);

  // Middle bet 1: Polymarket Up + Kalshi Down
  const cost1 = polymarket.yes + kalshi.no;
  if (cost1 < 1.25 && targetDiff > 5) {
    opportunities.push({
      type: 'middle',
      title: 'Middle Bet: Poly Up + Kalshi Down',
      bets: [
        { platform: 'polymarket', outcome: 'yes', price: polymarket.yes },
        { platform: 'kalshi', outcome: 'no', price: kalshi.no }
      ],
      cost: cost1,
      middleProfit: 2 - cost1,
      outsideProfit: -(cost1 - 1),
      range: [Math.min(kalshi.target, polymarket.target), Math.max(kalshi.target, polymarket.target)],
      targetDiff: targetDiff,
      roi: ((1 - cost1) / cost1 * 100).toFixed(1)
    });
  }

  // Middle bet 2: Polymarket Down + Kalshi Up
  const cost2 = polymarket.no + kalshi.yes;
  if (cost2 < 1.25 && targetDiff > 5) {
    opportunities.push({
      type: 'middle',
      title: 'Middle Bet: Poly Down + Kalshi Up',
      bets: [
        { platform: 'polymarket', outcome: 'no', price: polymarket.no },
        { platform: 'kalshi', outcome: 'yes', price: kalshi.yes }
      ],
      cost: cost2,
      middleProfit: 2 - cost2,
      outsideProfit: -(cost2 - 1),
      range: [Math.min(kalshi.target, polymarket.target), Math.max(kalshi.target, polymarket.target)],
      targetDiff: targetDiff,
      roi: ((1 - cost2) / cost2 * 100).toFixed(1)
    });
  }

  // Pure arbitrage
  if (Math.abs(kalshi.target - polymarket.target) < 1) {
    const totalCost = kalshi.yes + kalshi.no;
    if (totalCost < 1) {
      opportunities.push({
        type: 'arb',
        title: 'Pure Arbitrage',
        cost: totalCost,
        profit: 1 - totalCost,
        roi: ((1 - totalCost) / totalCost * 100).toFixed(1)
      });
    }
  }

  return opportunities;
}

exports.handler = async (event, context) => {
  try {
    const [kalshi, polymarket] = await Promise.all([
      fetchKalshiMarkets(),
      fetchPolymarketMarkets()
    ]);

    const opportunities = analyzeOpportunities(kalshi, polymarket);

    return {
      statusCode: 200,
      headers: {
        'Content-Type': 'application/json',
        'Access-Control-Allow-Origin': '*'
      },
      body: JSON.stringify({
        kalshi,
        polymarket,
        opportunities,
        lastUpdate: new Date().toISOString()
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
