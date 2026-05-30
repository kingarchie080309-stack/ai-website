const http = require('http');
const fs = require('fs');
const path = require('path');
const url = require('url');

// Load all Netlify functions
const polymarketFn = require('./netlify/functions/polymarket.js');
const copytradeFn = require('./netlify/functions/copytrade-wallet.js');
const executeFn = require('./netlify/functions/execute-copytrade.js');

const PORT = 3000;

const server = http.createServer(async (req, res) => {
  const parsedUrl = url.parse(req.url, true);
  const pathname = parsedUrl.pathname;
  const query = parsedUrl.query;

  // CORS headers
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'GET, POST, OPTIONS');
  res.setHeader('Content-Type', 'application/json');

  try {
    // Route Netlify functions
    if (pathname === '/.netlify/functions/polymarket') {
      const result = await polymarketFn.handler({}, {});
      res.writeHead(result.statusCode, result.headers);
      res.end(result.body);
    } else if (pathname === '/.netlify/functions/copytrade-wallet') {
      const result = await copytradeFn.handler({}, {});
      res.writeHead(result.statusCode, result.headers);
      res.end(result.body);
    } else if (pathname === '/.netlify/functions/execute-copytrade') {
      const result = await executeFn.handler({ queryStringParameters: query }, {});
      res.writeHead(result.statusCode, result.headers);
      res.end(result.body);
    } else if (pathname === '/' || pathname === '/index.html') {
      // Serve trading-hud.html
      const filePath = path.join(__dirname, 'trading-hud.html');
      const content = fs.readFileSync(filePath, 'utf8');
      res.setHeader('Content-Type', 'text/html');
      res.writeHead(200);
      res.end(content);
    } else {
      // Serve static files
      const filePath = path.join(__dirname, pathname);

      if (fs.existsSync(filePath) && fs.statSync(filePath).isFile()) {
        const content = fs.readFileSync(filePath);
        const ext = path.extname(filePath);
        const contentType = {
          '.html': 'text/html',
          '.css': 'text/css',
          '.js': 'text/javascript',
          '.json': 'application/json',
          '.png': 'image/png',
          '.jpg': 'image/jpeg'
        }[ext] || 'application/octet-stream';

        res.setHeader('Content-Type', contentType);
        res.writeHead(200);
        res.end(content);
      } else {
        res.writeHead(404);
        res.end(JSON.stringify({ error: 'Not found' }));
      }
    }
  } catch (error) {
    console.error('Server error:', error);
    res.writeHead(500);
    res.end(JSON.stringify({ error: error.message }));
  }
});

server.listen(PORT, () => {
  console.log(`\n✅ Trading HUD running at http://localhost:${PORT}`);
  console.log(`📊 Copytrade wallet: 0xb27bc932bf8110d8f78e55da7d5f0497a18b5b82`);
  console.log(`\nPress Ctrl+C to stop\n`);
});
