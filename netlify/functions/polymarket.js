const https = require('https');

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

async function fetchPolymarketMarkets() {
  try {
    const data = await fetchURL('https://clob.polymarket.com/markets?limit=100');

    if (!data || !data.data) return [];

    const markets = data.data.filter(m =>
      m.question && m.accepting_orders
    );

    return markets.map(m => ({
      token_id: m.token_id,
      question: m.question,
      slug: m.market_slug,
      end_date: m.end_date_iso,
      price: m.current_price || 0.5,
      volume_24h: m.volume_24h || 0,
      liquidity: m.liquidity || 0
    }));
  } catch (error) {
    console.error('Polymarket fetch error:', error.message);
    return [];
  }
}

function findArbitrage(markets) {
  const opportunities = [];

  for (const market of markets) {
    const yes = market.price;
    const no = 1 - yes;
    const spread = yes + no;

    if (spread < 0.98) {
      opportunities.push({
        token_id: market.token_id,
        question: market.question,
        yes_price: yes,
        no_price: no,
        spread: spread,
        profit_pct: ((1 - spread) / spread * 100).toFixed(2),
        volume_24h: market.volume_24h
      });
    }
  }

  return opportunities.sort((a, b) => b.profit_pct - a.profit_pct);
}

function filterBTCMarkets(markets) {
  return markets.filter(m =>
    m.question.includes('Bitcoin') ||
    m.question.includes('BTC') ||
    m.question.includes('$BTC')
  );
}

exports.handler = async (event, context) => {
  try {
    const markets = await fetchPolymarketMarkets();
    const btcMarkets = filterBTCMarkets(markets);
    const opportunities = findArbitrage(markets);

    return {
      statusCode: 200,
      headers: {
        'Content-Type': 'application/json',
        'Access-Control-Allow-Origin': '*',
        'Cache-Control': 'max-age=30'
      },
      body: JSON.stringify({
        markets: btcMarkets.slice(0, 10),
        opportunities: opportunities.slice(0, 10),
        total_markets: markets.length,
        last_update: new Date().toISOString()
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
