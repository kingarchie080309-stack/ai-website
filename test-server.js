const http = require('http');
const fs = require('fs');
const path = require('path');
const https = require('https');

const PORT = process.env.PORT || 3000;

// Mock Polymarket API
async function fetchPolymarketData() {
  return new Promise((resolve) => {
    https.get('https://clob.polymarket.com/markets?limit=100', {
      timeout: 5000
    }, (res) => {
      let data = '';
      res.on('data', chunk => data += chunk);
      res.on('end', () => {
        try {
          const parsed = JSON.parse(data);
          const markets = parsed.data || [];

          // Bitcoin markets
          const btcMarkets = markets.filter(m =>
            m.question && (m.question.includes('Bitcoin') || m.question.includes('BTC'))
          ).slice(0, 10).map(m => ({
            token_id: m.token_id,
            question: m.question,
            yes_price: m.current_price || 0.5,
            no_price: 1 - (m.current_price || 0.5),
            volume_24h: m.volume_24h || 0
          }));

          // Find arbitrage
          const opportunities = [];
          for (const market of markets.slice(0, 50)) {
            const yes = market.current_price || 0.5;
            const no = 1 - yes;
            const spread = yes + no;

            if (spread < 0.98) {
              opportunities.push({
                token_id: market.token_id,
                question: market.question,
                yes_price: yes,
                no_price: no,
                profit_pct: ((1 - spread) / spread * 100).toFixed(2),
                volume_24h: market.volume_24h || 0
              });
            }
          }

          resolve({
            markets: btcMarkets,
            opportunities: opportunities.sort((a, b) => b.profit_pct - a.profit_pct).slice(0, 10),
            total_markets: markets.length,
            last_update: new Date().toISOString()
          });
        } catch (e) {
          resolve({
            markets: [],
            opportunities: [],
            total_markets: 0,
            last_update: new Date().toISOString()
          });
        }
      });
    }).on('error', () => {
      resolve({
        markets: [],
        opportunities: [],
        total_markets: 0,
        last_update: new Date().toISOString()
      });
    });
  });
}

const server = http.createServer(async (req, res) => {
  // CORS headers
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'GET, POST, OPTIONS');
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type');

  if (req.method === 'OPTIONS') {
    res.writeHead(200);
    res.end();
    return;
  }

  // API endpoint
  if (req.url === '/.netlify/functions/polymarket' || req.url === '/api/polymarket') {
    const data = await fetchPolymarketData();
    res.writeHead(200, { 'Content-Type': 'application/json' });
    res.end(JSON.stringify(data));
    return;
  }

  // Serve HTML files
  let filePath = req.url === '/' ? '/trading-hud.html' : req.url;
  filePath = path.join(__dirname, filePath);

  fs.readFile(filePath, (err, data) => {
    if (err) {
      res.writeHead(404);
      res.end('File not found');
      return;
    }

    const ext = path.extname(filePath);
    const contentType = {
      '.html': 'text/html',
      '.js': 'application/javascript',
      '.css': 'text/css',
      '.json': 'application/json'
    }[ext] || 'text/plain';

    res.writeHead(200, { 'Content-Type': contentType });
    res.end(data);
  });
});

server.listen(PORT, () => {
  console.log(`\n🚀 Server running at http://localhost:${PORT}\n`);
  console.log(`📊 Dashboard: http://localhost:${PORT}`);
  console.log(`📡 API: http://localhost:${PORT}/.netlify/functions/polymarket\n`);
});
