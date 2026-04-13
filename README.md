# MacroRanked MVP

A gamified macro tracking app — MyFitnessPal meets Fortnite Tracker meets Duolingo.

## Quick Start

1. Make sure you have **Node.js** installed (download from https://nodejs.org)
2. Open this folder in VS Code
3. Open the terminal (Ctrl+` or Cmd+`)
4. Run these two commands:

```bash
npm install
npm run dev
```

5. Your browser will open automatically at `http://localhost:3000`

## Project Structure

```
macroranked-app/
├── index.html              # Entry HTML
├── package.json            # Dependencies
├── vite.config.js          # Build config
├── src/
│   ├── main.jsx            # App entry point
│   ├── index.css           # Global styles + animations
│   ├── App.jsx             # Main app with all screens
│   ├── components/
│   │   ├── RankBadge.jsx   # Rank badge using your PNG images
│   │   └── AppIcon.jsx     # App icon using your logo PNG
│   ├── data/
│   │   ├── ranks.js        # Rank config + image imports
│   │   └── mockData.js     # Mock meals, leaderboard, etc.
│   └── assets/
│       ├── brand/
│       │   └── logo-main.png    # Your MR shield logo
│       └── ranks/
│           ├── bronze.png       # Your rank badge PNGs
│           ├── silver.png
│           ├── gold.png
│           ├── platinum.png
│           ├── diamond.png
│           └── crimson.png
└── public/                  # Static files
```

## Swapping Images

To update any logo or rank badge, just replace the PNG file in `src/assets/` with a new one (keep the same filename). The app will pick it up automatically on refresh.

## What's Mocked

- All meal data (mock JSON, no real backend)
- AI food recognition (no real API)
- Leaderboard (hardcoded users)
- Share functionality (visual only)
- User auth (local state only)

## Next Steps to Build for Real

1. **Backend**: Set up Supabase (auth + database + storage)
2. **Manual macro entry**: Wire up the "enter manually" flow
3. **Scoring algorithm**: Real scoring against daily targets
4. **Social features**: Friend system + real leaderboard
5. **AI recognition**: Nutritionix API or custom vision model
6. **Deploy as PWA or React Native app**
