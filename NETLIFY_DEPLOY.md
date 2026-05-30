# Deploy Bitcoin Arbitrage Scanner to Netlify

This guide walks you through deploying the Bitcoin Arbitrage Scanner to Netlify for free.

## Prerequisites

- GitHub account (free)
- Netlify account (free)

## Setup Steps

### 1. Initialize Git (if not already done)

```bash
git init
git add .
git commit -m "Add Bitcoin arbitrage scanner"
```

### 2. Create GitHub Repository

1. Go to [github.com/new](https://github.com/new)
2. Create a new repository (e.g., `bitcoin-arb-scanner`)
3. Push your code:

```bash
git remote add origin https://github.com/YOUR_USERNAME/bitcoin-arb-scanner.git
git branch -M main
git push -u origin main
```

### 3. Deploy to Netlify

#### Option A: Netlify CLI (Fastest)

```bash
npm install -g netlify-cli
netlify login
netlify deploy --prod
```

#### Option B: Netlify Dashboard

1. Go to [netlify.com](https://netlify.com)
2. Click "New site from Git"
3. Connect your GitHub account
4. Select your repository
5. Click "Deploy"

## How It Works

The scanner uses **Netlify Functions** (serverless) to:
- Fetch prices from Polymarket API
- Fetch prices from Kalshi API
- Analyze for arbitrage opportunities
- Return results to the frontend

**No backend server needed.** Everything runs on Netlify's free tier.

## What You Get

✅ **Live Dashboard** at `yoursite.netlify.app`
✅ **Auto-refresh** every 30 seconds
✅ **Free hosting** (Netlify free tier)
✅ **No credit card** required
✅ **Custom domain** option
✅ **HTTPS** out of the box

## File Structure

```
.
├── index.html                 # Dashboard UI
├── netlify.toml              # Netlify configuration
├── netlify/
│   └── functions/
│       └── markets.js        # Serverless function
└── README.md
```

## Customization

### Change Refresh Rate

Edit `index.html`, find this line:
```javascript
}, 30000);  // 30 seconds
```

Change `30000` to your desired interval in milliseconds.

### Change Markets

Edit `netlify/functions/markets.js` and update the search filters in:
- `fetchKalshiMarkets()`
- `fetchPolymarketMarkets()`

## Troubleshooting

**Dashboard shows "Unable to fetch market data"**
- APIs may be rate-limited or temporarily down
- Check browser console (F12) for error messages
- Wait a moment and refresh

**Function errors**
- Check Netlify deploy logs: `netlify logs --function=markets`
- Make sure `netlify.toml` is in root directory

**Live updates not working**
- Netlify Functions have cold starts (first call takes 1-2 seconds)
- This is normal - they'll warm up on subsequent calls

## Monitoring

Monitor your function performance:
1. Go to Netlify dashboard
2. Click your site
3. Go to "Functions" tab
4. View logs and performance metrics

## Next Steps

- Add alerting (email/SMS when opportunities appear)
- Create a Telegram bot for notifications
- Expand to other markets (ETH, sports, politics)
- Add trade execution (if you have exchange API keys)

## Support

Issues? Check:
1. Browser console for error messages
2. Netlify deploy logs
3. API status pages (polymarket.com, kalshi.com)

Deploy now and start finding arbitrage opportunities! 🚀
