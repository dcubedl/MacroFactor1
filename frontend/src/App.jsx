import { useState, useRef, useEffect } from "react";
import { getRank, LOGO_IMAGE } from "./data/ranks";
import SplashScreen from "./components/SplashScreen";
import OnboardingGraph from "./components/OnboardingGraph";
import { MOCK_MEALS, MOCK_LEADERBOARD } from "./data/mockData";
import RankBadge from "./components/RankBadge";
import AppIcon from "./components/AppIcon";
import AuthScreen from "./components/AuthScreen";
import { api } from "./services/api";
import navHome from './assets/nav/home.png';
import navRanks from './assets/nav/ranked.png';
import navProfile from './assets/nav/profile.png';
import navShare from './assets/nav/share.png';

// --- Shared UI ---
const PBar = ({ value, max, color = "var(--acc)", h = 6, label, showVal = false, unit = "g" }) => {
  const pct = Math.min(100, (value / max) * 100);
  return (
    <div style={{ width: "100%" }}>
      {(label || showVal) && <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 4 }}>
        {label && <span style={{ color: "var(--t2)", textTransform: "uppercase", letterSpacing: ".06em", fontFamily: "var(--fm)", fontSize: 10, fontWeight: 600 }}>{label}</span>}
        {showVal && <span style={{ color: "var(--t1)", fontFamily: "var(--fm)", fontSize: 11 }}>{value}/{max}{unit}</span>}
      </div>}
      <div style={{ width: "100%", height: h, borderRadius: h, background: "rgba(255,255,255,.05)", overflow: "hidden" }}>
        <div style={{ height: "100%", width: `${pct}%`, borderRadius: h, background: color, animation: "pf .8s ease forwards", boxShadow: `0 0 8px ${color}40` }} />
      </div>
    </div>
  );
};

const Card = ({ children, style = {}, onClick }) => (
  <div onClick={onClick} style={{ background: "var(--card)", borderRadius: 16, border: "1px solid var(--bdr)", padding: 16, cursor: onClick ? "pointer" : "default", transition: "all .2s", ...style }}
    onMouseEnter={e => { if (onClick) { e.currentTarget.style.background = "var(--cardH)"; e.currentTarget.style.borderColor = "var(--bdrL)"; } }}
    onMouseLeave={e => { if (onClick) { e.currentTarget.style.background = style.background || "var(--card)"; e.currentTarget.style.borderColor = "var(--bdr)"; } }}>
    {children}
  </div>
);

const Nav = ({ active, go }) => {
  const [uploadPressed, setUploadPressed] = useState(false);
  const tabs = [
    { id: "home", l: "Home", i: navHome },
    { id: "leaderboard", l: "Ranks", i: navRanks },
    { id: "upload" },
    { id: "profile", l: "Profile", i: navProfile },
    { id: "share", l: "Share", i: navShare },
  ];
  return (
    <div style={{ position: "fixed", bottom: 0, left: "50%", transform: "translateX(-50%)", width: "100%", maxWidth: 430, background: "rgba(10,10,15,.94)", backdropFilter: "blur(20px)", borderTop: "1px solid var(--bdr)", display: "flex", justifyContent: "space-around", alignItems: "center", padding: "4px 0 env(safe-area-inset-bottom,5px)", zIndex: 100 }}>
      {tabs.map(x => {
        if (x.id === "upload") return (
          <button key="upload" onClick={() => { go("upload"); setUploadPressed(true); setTimeout(() => setUploadPressed(false), 200); }} style={{ background: uploadPressed ? "#fff" : "var(--acc)", border: "none", cursor: "pointer", borderRadius: "50%", width: 50, height: 50, display: "flex", alignItems: "center", justifyContent: "center", boxShadow: "0 0 24px var(--accG)", position: "relative", top: -12, padding: 0, transition: "all 0.15s ease" }}>
            <img src={LOGO_IMAGE} alt="Upload" style={{ width: 'auto', height: 44, objectFit: "contain", filter: uploadPressed ? "none" : "brightness(10)", mixBlendMode: "screen", transition: "all 0.15s ease" }} />
          </button>
        );
        return (
          <button key={x.id} onClick={() => go(x.id)} style={{ background: "none", border: "none", color: active === x.id ? "var(--t1)" : "var(--t3)", display: "flex", flexDirection: "column", alignItems: "center", gap: 2, padding: "5px 16px", cursor: "pointer", fontSize: 18, position: "relative" }}>
            <img src={x.i} alt={x.l} style={{ width: 36, height: 'auto', display: 'block', lineHeight: 0, mixBlendMode: 'screen', opacity: active === x.id ? 1 : 0.45, transition: 'opacity 0.2s ease' }} />
            <span style={{ fontSize: 9, fontWeight: 600, letterSpacing: ".05em", textTransform: "uppercase", fontFamily: "var(--fm)" }}>{x.l}</span>
            {active === x.id && <div style={{ position: "absolute", bottom: 0, width: 16, height: 2, borderRadius: 1, background: "var(--acc)" }} />}
          </button>
        );
      })}
    </div>
  );
};

// --- SCREENS ---

const Home = ({ user, go, setSel }) => {
  const todayMeals = MOCK_MEALS.slice(0, 3);
  const tc = todayMeals.reduce((s, m) => s + m.cal, 0);
  const tp = todayMeals.reduce((s, m) => s + m.protein, 0);
  const tca = todayMeals.reduce((s, m) => s + m.carbs, 0);
  const tf = todayMeals.reduce((s, m) => s + m.fat, 0);
  const avg = Math.round(todayMeals.reduce((s, m) => s + m.score, 0) / 3);
  const dr = getRank(avg);

  return (
    <div style={{ padding: "0 16px 100px", overflowY: "auto", minHeight: "100vh", animation: "popIn .4s cubic-bezier(0.22,1.2,.36,1) both" }}>
      {/* Header */}
      <div className="fiu" style={{ display: "flex", justifyContent: "space-between", alignItems: "center", padding: "16px 4px 14px" }}>
        <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
          <AppIcon size={56} />
          <div>
            <h1 style={{ fontSize: 20, fontWeight: 800, letterSpacing: "-.02em" }}>@{user.username}</h1>
          </div>
        </div>
        <RankBadge rank={avg} size="md" animated showLabel={false} />
      </div>

      {/* Score Card */}
      <Card style={{ marginBottom: 12, background: "linear-gradient(135deg,var(--card) 0%,rgba(255,23,68,.03) 100%)", border: "1px solid rgba(255,23,68,.08)", animation: "popIn .4s .05s cubic-bezier(0.22,1.2,.36,1) both" }}>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 14 }}>
          <div>
            <p style={{ fontSize: 10, fontWeight: 700, color: "var(--t3)", letterSpacing: ".1em", textTransform: "uppercase", fontFamily: "var(--fm)", marginBottom: 2 }}>Today's Average</p>
            <div style={{ display: "flex", alignItems: "baseline", gap: 6 }}>
              <span style={{ fontSize: 34, fontWeight: 900, color: dr.color, fontFamily: "var(--fm)" }}>{avg}</span>
              <span style={{ fontSize: 13, fontWeight: 600, color: "var(--t2)" }}>/ 100</span>
            </div>
          </div>
          <div style={{ textAlign: "right" }}>
            <div style={{ display: "flex", alignItems: "center", gap: 5, marginBottom: 3 }}>
              <span style={{ fontSize: 20 }}>🔥</span>
              <span style={{ fontSize: 22, fontWeight: 800, fontFamily: "var(--fm)" }}>27</span>
            </div>
            <span style={{ fontSize: 9, color: "var(--t3)", fontFamily: "var(--fm)" }}>DAY STREAK</span>
          </div>
        </div>
        <div style={{ display: "flex", gap: 4 }}>
          {todayMeals.map((m, i) => {
            const r = getRank(m.score);
            return (
              <div key={i} style={{ flex: 1, background: "rgba(255,255,255,.025)", borderRadius: 10, padding: "8px 4px", textAlign: "center" }}>
                <div style={{ fontSize: 17, marginBottom: 2 }}>{m.photo}</div>
                <div style={{ fontSize: 9, color: "var(--t3)", fontFamily: "var(--fm)", marginBottom: 2 }}>{["BRKFST", "LUNCH", "DINNER"][i]}</div>
                <div style={{ fontSize: 13, fontWeight: 700, color: r.color, fontFamily: "var(--fm)" }}>{m.score}</div>
              </div>
            );
          })}
          <div onClick={() => go("upload")} style={{ flex: 1, background: "rgba(255,23,68,.03)", borderRadius: 10, padding: "8px 4px", textAlign: "center", border: "1px dashed rgba(255,23,68,.2)", display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center", cursor: "pointer" }}>
            <span style={{ fontSize: 18, color: "var(--acc)" }}>+</span>
            <span style={{ fontSize: 8, color: "var(--acc)", fontFamily: "var(--fm)", fontWeight: 600 }}>ADD</span>
          </div>
        </div>
      </Card>

      {/* Macros */}
      <Card style={{ marginBottom: 12, animation: "popIn .4s .1s cubic-bezier(0.22,1.2,.36,1) both" }}>
        <p style={{ fontSize: 10, fontWeight: 700, color: "var(--t3)", letterSpacing: ".1em", textTransform: "uppercase", fontFamily: "var(--fm)", marginBottom: 12 }}>Daily Macros</p>
        <div style={{ display: "flex", flexDirection: "column", gap: 10 }}>
          <PBar value={tc} max={user.calories} color="var(--acc)" label="Calories" showVal unit="kcal" />
          <PBar value={tp} max={user.protein} color="#00E5FF" label="Protein" showVal />
          <PBar value={tca} max={user.carbs} color="#FFD700" label="Carbs" showVal />
          <PBar value={tf} max={user.fat} color="#B388FF" label="Fat" showVal />
        </div>
      </Card>

      {/* Recent Meals */}
      <p style={{ fontSize: 10, fontWeight: 700, color: "var(--t3)", letterSpacing: ".1em", textTransform: "uppercase", fontFamily: "var(--fm)", marginBottom: 10, paddingLeft: 2 }}>Recent Meals</p>
      <div style={{ display: "flex", flexDirection: "column", gap: 6 }}>
        {MOCK_MEALS.map((meal, i) => {
          const r = getRank(meal.score);
          return (
            <Card key={meal.id} onClick={() => { setSel(meal); go("mr"); }} style={{ display: "flex", alignItems: "center", gap: 12, padding: "12px 14px", animation: `popIn .4s ${0.15 + i * 0.05}s cubic-bezier(0.22,1.2,.36,1) both` }}>
              <div style={{ fontSize: 26, width: 42, height: 42, borderRadius: 12, background: "var(--elev)", display: "flex", alignItems: "center", justifyContent: "center", flexShrink: 0 }}>{meal.photo}</div>
              <div style={{ flex: 1, minWidth: 0 }}>
                <div style={{ fontSize: 13, fontWeight: 600, marginBottom: 2, whiteSpace: "nowrap", overflow: "hidden", textOverflow: "ellipsis" }}>{meal.name}</div>
                <div style={{ fontSize: 11, color: "var(--t3)", fontFamily: "var(--fm)" }}>{meal.cal}kcal · {meal.time}</div>
              </div>
              <div style={{ textAlign: "right", flexShrink: 0 }}>
                <div style={{ fontSize: 15, fontWeight: 800, color: r.color, fontFamily: "var(--fm)" }}>{meal.score}</div>
                <div style={{ fontSize: 9, fontWeight: 600, color: r.color, fontFamily: "var(--fm)" }}>{r.name.toUpperCase()}</div>
              </div>
            </Card>
          );
        })}
      </div>
    </div>
  );
};

const MealResult = ({ meal, go }) => {
  if (!meal) return null;
  const r = getRank(meal.score);
  return (
    <div style={{ minHeight: "100vh", padding: "0 0 100px", animation: "popIn .4s cubic-bezier(0.22,1.2,.36,1) both" }}>
      <div style={{ padding: "16px 16px 0", display: "flex", alignItems: "center", gap: 12, marginBottom: 16 }}>
        <button onClick={() => go("home")} style={{ background: "var(--card)", border: "1px solid var(--bdr)", borderRadius: 10, width: 36, height: 36, display: "flex", alignItems: "center", justifyContent: "center", cursor: "pointer", color: "var(--t1)", fontSize: 16 }}>←</button>
        <h2 style={{ fontSize: 17, fontWeight: 700, flex: 1, whiteSpace: "nowrap", overflow: "hidden", textOverflow: "ellipsis" }}>{meal.name}</h2>
      </div>
      <div style={{ margin: "0 16px 16px", borderRadius: 20, background: `linear-gradient(135deg, var(--card), ${r.color}10)`, border: `1px solid ${r.color}20`, padding: 20, display: "flex", alignItems: "center", gap: 16 }}>
        <div style={{ fontSize: 52, width: 68, height: 68, borderRadius: 18, background: "var(--elev)", display: "flex", alignItems: "center", justifyContent: "center", flexShrink: 0 }}>{meal.photo}</div>
        <div style={{ flex: 1 }}>
          <div style={{ display: "flex", alignItems: "baseline", gap: 4, marginBottom: 4 }}>
            <span style={{ fontSize: 40, fontWeight: 900, color: r.color, fontFamily: "var(--fm)" }}>{meal.score}</span>
            <span style={{ fontSize: 13, color: "var(--t3)" }}>/100</span>
          </div>
          <p style={{ fontSize: 11, color: "var(--t3)", fontFamily: "var(--fm)" }}>{meal.time}</p>
        </div>
        <RankBadge rank={meal.score} size="md" animated />
      </div>
      <div style={{ padding: "0 16px", marginBottom: 12 }}>
        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr 1fr 1fr", gap: 8 }}>
          {[
            { l: "CAL", v: meal.cal, unit: "", color: "var(--acc)" },
            { l: "PRO", v: meal.protein, unit: "g", color: "#00E5FF" },
            { l: "CARB", v: meal.carbs, unit: "g", color: "#FFD700" },
            { l: "FAT", v: meal.fat, unit: "g", color: "#B388FF" },
          ].map(m => (
            <Card key={m.l} style={{ textAlign: "center", padding: "12px 4px" }}>
              <div style={{ fontSize: 17, fontWeight: 800, color: m.color, fontFamily: "var(--fm)" }}>{m.v}{m.unit}</div>
              <div style={{ fontSize: 9, color: "var(--t3)", fontFamily: "var(--fm)", letterSpacing: ".06em", marginTop: 2 }}>{m.l}</div>
            </Card>
          ))}
        </div>
      </div>
      <div style={{ padding: "0 16px", marginBottom: 12 }}>
        <Card>
          <p style={{ fontSize: 10, fontWeight: 700, color: "var(--t3)", letterSpacing: ".1em", textTransform: "uppercase", fontFamily: "var(--fm)", marginBottom: 10 }}>Ingredients</p>
          {meal.foods.map((f, i) => (
            <div key={i} style={{ display: "flex", alignItems: "center", gap: 8, padding: "7px 0", borderBottom: i < meal.foods.length - 1 ? "1px solid var(--bdr)" : "none" }}>
              <span style={{ fontSize: 11, color: "var(--acc)", fontWeight: 700, fontFamily: "var(--fm)", width: 16 }}>{i + 1}</span>
              <span style={{ fontSize: 13, color: "var(--t1)" }}>{f}</span>
            </div>
          ))}
        </Card>
      </div>
      <div style={{ padding: "0 16px" }}>
        <Card style={{ border: `1px solid ${r.color}20`, background: `linear-gradient(135deg, var(--card), ${r.color}08)` }}>
          <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 10 }}>
            <span style={{ fontSize: 16 }}>🔬</span>
            <p style={{ fontSize: 11, fontWeight: 700, color: r.color, letterSpacing: ".08em", textTransform: "uppercase", fontFamily: "var(--fm)" }}>Why this rank?</p>
          </div>
          <p style={{ fontSize: 13, lineHeight: 1.6, color: "var(--t2)", marginBottom: 10 }}>
            {meal.score >= 80 ? "Excellent macro balance with high protein and clean energy sources. This meal fuels performance and supports muscle growth." : meal.score >= 70 ? "Good nutritional profile with solid protein content. Minor improvements in micronutrient density would push this higher." : "Moderate nutrition score. Consider increasing protein content and reducing refined carbohydrates."}
          </p>
          <p style={{ fontSize: 11, fontWeight: 700, color: "var(--t3)", letterSpacing: ".08em", textTransform: "uppercase", fontFamily: "var(--fm)", marginBottom: 6 }}>Improve this meal</p>
          {["Increase protein by 10–20g for optimal muscle protein synthesis", "Add fibrous vegetables to boost micronutrient density", "Track sodium if having this multiple days in a row"].map((tip, i) => (
            <div key={i} style={{ display: "flex", alignItems: "flex-start", gap: 8, marginBottom: 5 }}>
              <span style={{ color: "var(--acc)", fontSize: 12, marginTop: 1 }}>→</span>
              <span style={{ fontSize: 12, color: "var(--t2)", lineHeight: 1.5 }}>{tip}</span>
            </div>
          ))}
        </Card>
      </div>
    </div>
  );
};

const FOOD_DB = [
  { name: "Chicken Breast", cal: 165, protein: 31, carbs: 0, fat: 3.6 },
  { name: "Rice (cooked)", cal: 130, protein: 2.7, carbs: 28, fat: 0.3 },
  { name: "Broccoli", cal: 34, protein: 2.8, carbs: 6.6, fat: 0.4 },
  { name: "Salmon", cal: 208, protein: 20, carbs: 0, fat: 13 },
  { name: "Sweet Potato", cal: 86, protein: 1.6, carbs: 20, fat: 0.1 },
  { name: "Eggs", cal: 155, protein: 13, carbs: 1.1, fat: 11 },
  { name: "Oats", cal: 389, protein: 17, carbs: 66, fat: 7 },
  { name: "Banana", cal: 89, protein: 1.1, carbs: 23, fat: 0.3 },
  { name: "Avocado", cal: 160, protein: 2, carbs: 9, fat: 15 },
  { name: "Greek Yogurt", cal: 59, protein: 10, carbs: 3.6, fat: 0.4 },
  { name: "Whey Protein", cal: 400, protein: 80, carbs: 10, fat: 5 },
  { name: "Peanut Butter", cal: 588, protein: 25, carbs: 20, fat: 50 },
  { name: "Olive Oil", cal: 884, protein: 0, carbs: 0, fat: 100 },
  { name: "Almonds", cal: 579, protein: 21, carbs: 22, fat: 50 },
  { name: "Steak", cal: 271, protein: 26, carbs: 0, fat: 18 },
  { name: "Pasta (cooked)", cal: 131, protein: 5, carbs: 25, fat: 1.1 },
  { name: "Bread", cal: 265, protein: 9, carbs: 49, fat: 3.2 },
  { name: "Milk", cal: 61, protein: 3.2, carbs: 4.8, fat: 3.3 },
  { name: "Apple", cal: 52, protein: 0.3, carbs: 14, fat: 0.2 },
  { name: "Blueberries", cal: 57, protein: 0.7, carbs: 14, fat: 0.3 },
];

const Upload = ({ go, user, setSel }) => {
  const [phase, setPhase] = useState("idle");
  const [progress, setProgress] = useState(0);
  const [statusIdx, setStatusIdx] = useState(0);
  const statuses = ["Detecting foods...", "Estimating portions...", "Calculating macros...", "Assigning rank..."];
  const [search, setSearch] = useState("");
  const [searchFocused, setSearchFocused] = useState(false);
  const [selectedFoods, setSelectedFoods] = useState([]);
  const [manualResult, setManualResult] = useState(null);
  const [scanResult, setScanResult] = useState(null);
  const [scanError, setScanError] = useState(null);
  const [imagePreview, setImagePreview] = useState(null);
  const fileRef = useRef(null);
  const cameraRef = useRef(null);

  const startScan = async (file) => {
    setPhase("scanning");
    setProgress(0);
    setStatusIdx(0);
    setScanResult(null);
    setScanError(null);
    if (file) setImagePreview(URL.createObjectURL(file));

    // Progress animation runs independently; API call races alongside it.
    let p = 0;
    const iv = setInterval(() => {
      p += 1;
      setProgress(p);
      setStatusIdx(Math.min(3, Math.floor(p / 25)));
      if (p >= 100) clearInterval(iv);
    }, 35);

    if (!file) { setTimeout(() => setPhase("results"), 4000); return; }

    try {
      const result = await api.scanFood(file);
      setScanResult(result);
    } catch (err) {
      setScanError(
        err.status === 0   ? "Cannot reach the server. Make sure the backend is running." :
        err.status === 429 ? "Gemini is rate limited — please wait a moment and try again." :
        err.status === 401 ? "Session expired. Please log back in." :
        err.message        || "Could not analyse the image. Please try again."
      );
    } finally {
      clearInterval(iv);
      setProgress(100);
      setTimeout(() => setPhase("results"), 600);
    }
  };

  const fMacros = (food, grams) => ({
    cal: Math.round(food.cal * grams / 100),
    protein: Math.round(food.protein * grams / 100 * 10) / 10,
    carbs: Math.round(food.carbs * grams / 100 * 10) / 10,
    fat: Math.round(food.fat * grams / 100 * 10) / 10,
  });

  const addFood = (food) => {
    setSelectedFoods(prev => [...prev, { food, grams: 100 }]);
    setSearch("");
    setManualResult(null);
  };

  const removeFood = (i) => {
    setSelectedFoods(prev => prev.filter((_, idx) => idx !== i));
    setManualResult(null);
  };

  const updateGrams = (i, grams) => {
    setSelectedFoods(prev => prev.map((item, idx) => idx === i ? { ...item, grams: Math.max(1, Number(grams) || 1) } : item));
    setManualResult(null);
  };

  const calculateAndRank = () => {
    const totals = selectedFoods.reduce((acc, { food, grams }) => {
      const m = fMacros(food, grams);
      return { cal: acc.cal + m.cal, protein: acc.protein + m.protein, carbs: acc.carbs + m.carbs, fat: acc.fat + m.fat };
    }, { cal: 0, protein: 0, carbs: 0, fat: 0 });
    const targets = user
      ? { protein: user.protein / 3, carbs: user.carbs / 3, fat: user.fat / 3 }
      : { protein: 60, carbs: 90, fat: 25 };
    const acc = (actual, target) => Math.min(100, Math.max(0, 100 - Math.abs(actual - target) / target * 100));
    const score = Math.round(acc(totals.protein, targets.protein) * 0.4 + acc(totals.carbs, targets.carbs) * 0.3 + acc(totals.fat, targets.fat) * 0.3);
    setManualResult({ score, ...totals });
  };

  const matches = search.length > 1 ? FOOD_DB.filter(f => f.name.toLowerCase().includes(search.toLowerCase())) : [];

  // scan result variables populated after a real API call (results phase only)

  const QUICK_ADD = ["Chicken Breast", "Rice (cooked)", "Eggs", "Oats", "Banana", "Whey Protein", "Avocado", "Sweet Potato"]
    .map(name => FOOD_DB.find(f => f.name === name)).filter(Boolean);

  if (phase === "idle") return (
    <div style={{ minHeight: "100vh", padding: "60px 16px 100px", animation: "popIn .4s cubic-bezier(0.22,1.2,.36,1) both" }}>
      <h2 style={{ fontSize: 22, fontWeight: 800, marginBottom: 4 }}>Log Your Meal</h2>
      <p style={{ fontSize: 13, color: "var(--t3)", marginBottom: 18 }}>Build your meal and get your macro rank</p>

      {/* Search */}
      <div style={{ position: "relative", marginBottom: 20 }}>
        <div style={{
          background: "var(--card)", borderRadius: 16,
          border: searchFocused ? "1px solid var(--acc)" : "1px solid var(--bdr)",
          boxShadow: searchFocused ? "0 0 12px rgba(255,23,68,0.2)" : "none",
          display: "flex", alignItems: "center", gap: 10, padding: "0 16px",
          transition: "border-color .15s, box-shadow .15s",
        }}>
          <span style={{ fontSize: 16, color: "var(--t3)" }}>🔍</span>
          <input
            type="text"
            placeholder="Search food e.g. chicken breast, rice..."
            value={search}
            onChange={e => { setSearch(e.target.value); setManualResult(null); }}
            onFocus={() => setSearchFocused(true)}
            onBlur={() => setSearchFocused(false)}
            style={{ background: "none", border: "none", outline: "none", color: "var(--t1)", fontSize: 16, fontWeight: 500, padding: "16px 0", width: "100%", fontFamily: "var(--fd)" }}
          />
          {search.length > 0 && (
            <button onClick={() => setSearch("")} style={{ background: "none", border: "none", color: "var(--t3)", cursor: "pointer", fontSize: 16, padding: 0, lineHeight: 1 }}>✕</button>
          )}
        </div>
        {matches.length > 0 && (
          <div style={{ position: "absolute", left: 0, right: 0, zIndex: 10, background: "var(--card)", borderRadius: 12, border: "1px solid var(--bdr)", marginTop: 4, overflow: "hidden", boxShadow: "0 8px 24px rgba(0,0,0,0.5)" }}>
            {matches.slice(0, 6).map((food, i) => (
              <div key={food.name} onClick={() => addFood(food)} style={{ display: "flex", justifyContent: "space-between", alignItems: "center", padding: "13px 16px", borderBottom: i < Math.min(matches.length, 6) - 1 ? "1px solid var(--bdr)" : "none", cursor: "pointer" }}
                onMouseEnter={e => e.currentTarget.style.background = "var(--elev)"}
                onMouseLeave={e => e.currentTarget.style.background = "transparent"}>
                <span style={{ fontSize: 14, fontWeight: 600 }}>{food.name}</span>
                <span style={{ fontSize: 11, color: "var(--t3)", fontFamily: "var(--fm)" }}>{food.cal} kcal/100g</span>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Quick Add */}
      {search.length === 0 && (
        <div style={{ marginBottom: 20 }}>
          <p style={{ fontSize: 11, fontWeight: 700, color: "var(--t3)", letterSpacing: ".1em", textTransform: "uppercase", fontFamily: "var(--fm)", marginBottom: 10 }}>Quick Add</p>
          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 8 }}>
            {QUICK_ADD.map(food => (
              <button key={food.name} onClick={() => addFood(food)} style={{ background: "var(--card)", border: "1px solid var(--bdr)", borderRadius: 14, padding: 12, cursor: "pointer", textAlign: "left", display: "flex", flexDirection: "column", gap: 3 }}>
                <span style={{ fontSize: 13, fontWeight: 700, color: "var(--t1)" }}>{food.name}</span>
                <span style={{ fontSize: 11, color: "var(--t3)", fontFamily: "var(--fm)" }}>{food.cal} kcal/100g</span>
              </button>
            ))}
          </div>
        </div>
      )}

      {/* Selected Foods */}
      <div style={{ marginBottom: 16 }}>
        <p style={{ fontSize: 11, fontWeight: 700, color: "var(--t3)", letterSpacing: ".1em", textTransform: "uppercase", fontFamily: "var(--fm)", marginBottom: 10 }}>Selected Foods</p>
        {selectedFoods.length === 0 ? (
          <div style={{ background: "var(--card)", borderRadius: 14, border: "1px dashed var(--bdr)", padding: "20px 16px", textAlign: "center" }}>
            <p style={{ fontSize: 13, color: "var(--t3)", fontFamily: "var(--fd)" }}>No foods added yet</p>
            <p style={{ fontSize: 11, color: "var(--t3)", opacity: 0.6, marginTop: 4 }}>Search or tap above to start</p>
          </div>
        ) : (
          <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
            {selectedFoods.map((item, i) => {
              const m = fMacros(item.food, item.grams);
              return (
                <div key={i} style={{ background: "var(--card)", borderRadius: 14, border: "1px solid var(--bdr)", padding: 14 }}>
                  <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 10 }}>
                    <span style={{ fontSize: 14, fontWeight: 600 }}>{item.food.name}</span>
                    <button onClick={() => removeFood(i)} style={{ background: "rgba(255,255,255,.06)", border: "none", color: "var(--t3)", cursor: "pointer", fontSize: 12, width: 24, height: 24, borderRadius: "50%", display: "flex", alignItems: "center", justifyContent: "center" }}>✕</button>
                  </div>
                  <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 10 }}>
                    <input
                      type="number"
                      min="1"
                      max="2000"
                      value={item.grams}
                      onChange={e => updateGrams(i, e.target.value)}
                      style={{ background: "var(--elev)", border: "1px solid var(--bdr)", borderRadius: 8, color: "var(--t1)", fontSize: 16, fontWeight: 700, padding: "6px 10px", width: 80, fontFamily: "var(--fd)", outline: "none", textAlign: "center" }}
                    />
                    <span style={{ fontSize: 13, color: "var(--t3)", fontFamily: "var(--fm)" }}>g</span>
                  </div>
                  <div style={{ display: "flex", gap: 6 }}>
                    {[{ l: "CAL", v: m.cal, c: "var(--acc)" }, { l: "P", v: `${m.protein}g`, c: "#00E5FF" }, { l: "C", v: `${m.carbs}g`, c: "#FFD700" }, { l: "F", v: `${m.fat}g`, c: "#B388FF" }].map(x => (
                      <div key={x.l} style={{ flex: 1, background: "rgba(255,255,255,.03)", borderRadius: 8, padding: "6px 4px", textAlign: "center" }}>
                        <div style={{ fontSize: 12, fontWeight: 800, color: x.c, fontFamily: "var(--fm)" }}>{x.v}</div>
                        <div style={{ fontSize: 8, color: "var(--t3)", fontFamily: "var(--fm)", marginTop: 1 }}>{x.l}</div>
                      </div>
                    ))}
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>

      {/* Calculate & Rank */}
      <button
        onClick={selectedFoods.length > 0 ? calculateAndRank : undefined}
        style={{
          width: "100%", padding: "15px 0", border: "none", borderRadius: 14, fontSize: 15, fontWeight: 700,
          cursor: selectedFoods.length > 0 ? "pointer" : "default",
          background: selectedFoods.length > 0 ? "var(--acc)" : "var(--elev)",
          color: selectedFoods.length > 0 ? "#fff" : "var(--t3)",
          boxShadow: selectedFoods.length > 0 ? "0 0 24px var(--accG)" : "none",
          marginBottom: manualResult ? 16 : 0,
          transition: "background .2s, color .2s, box-shadow .2s",
        }}>
        Calculate &amp; Rank
      </button>

      {manualResult && (() => {
        const mr = getRank(manualResult.score);
        return (
          <div style={{ background: `linear-gradient(135deg, var(--card), ${mr.color}08)`, borderRadius: 20, border: `1px solid ${mr.color}20`, padding: 20, textAlign: "center", animation: "rr .5s cubic-bezier(.34,1.56,.64,1) forwards", marginTop: 16 }}>
            <p style={{ fontSize: 10, fontWeight: 700, color: "var(--t3)", letterSpacing: ".12em", textTransform: "uppercase", fontFamily: "var(--fm)", marginBottom: 12 }}>Meal Ranked</p>
            <RankBadge rank={manualResult.score} size="lg" animated />
            <div style={{ margin: "10px 0 16px" }}>
              <span style={{ fontSize: 44, fontWeight: 900, color: mr.color, fontFamily: "var(--fm)" }}>{manualResult.score}</span>
              <span style={{ fontSize: 15, color: "var(--t3)", fontFamily: "var(--fm)" }}>/100</span>
            </div>
            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr 1fr 1fr", gap: 8 }}>
              {[
                { l: "CAL", v: Math.round(manualResult.cal), c: "var(--acc)" },
                { l: "PRO", v: `${Math.round(manualResult.protein)}g`, c: "#00E5FF" },
                { l: "CARB", v: `${Math.round(manualResult.carbs)}g`, c: "#FFD700" },
                { l: "FAT", v: `${Math.round(manualResult.fat)}g`, c: "#B388FF" },
              ].map(m => (
                <div key={m.l} style={{ background: "rgba(255,255,255,.04)", borderRadius: 10, padding: "10px 4px" }}>
                  <div style={{ fontSize: 15, fontWeight: 800, color: m.c, fontFamily: "var(--fm)" }}>{m.v}</div>
                  <div style={{ fontSize: 9, color: "var(--t3)", fontFamily: "var(--fm)", marginTop: 2 }}>{m.l}</div>
                </div>
              ))}
            </div>
          </div>
        );
      })()}

      {/* OR divider */}
      <div style={{ display: "flex", alignItems: "center", gap: 12, margin: "28px 0 16px" }}>
        <div style={{ flex: 1, height: 1, background: "var(--bdr)" }} />
        <span style={{ fontSize: 11, fontWeight: 700, color: "var(--t3)", fontFamily: "var(--fm)", letterSpacing: ".1em" }}>OR</span>
        <div style={{ flex: 1, height: 1, background: "var(--bdr)" }} />
      </div>

      {/* Compact photo upload */}
      <div style={{ background: "var(--card)", borderRadius: 16, border: "1px solid var(--bdr)", padding: "12px 14px", display: "flex", alignItems: "center", gap: 12 }}>
        <input ref={cameraRef} type="file" accept="image/*" capture="environment" style={{ display: "none" }}
          onChange={e => { const f = e.target.files?.[0]; e.target.value = ""; if (f) startScan(f); }} />
        <input ref={fileRef} type="file" accept="image/*" style={{ display: "none" }}
          onChange={e => { const f = e.target.files?.[0]; e.target.value = ""; if (f) startScan(f); }} />
        <span style={{ fontSize: 22 }}>📷</span>
        <span style={{ flex: 1, fontSize: 14, fontWeight: 600, color: "var(--t2)" }}>Snap a photo</span>
        <button onClick={() => cameraRef.current?.click()} style={{ padding: "8px 14px", background: "var(--elev)", border: "1px solid var(--bdr)", borderRadius: 10, color: "var(--t1)", fontSize: 13, fontWeight: 600, cursor: "pointer", display: "flex", alignItems: "center", gap: 6 }}>
          <span style={{ fontSize: 14 }}>📷</span>Camera
        </button>
        <button onClick={() => fileRef.current?.click()} style={{ padding: "8px 14px", background: "var(--elev)", border: "1px solid var(--bdr)", borderRadius: 10, color: "var(--t1)", fontSize: 13, fontWeight: 600, cursor: "pointer", display: "flex", alignItems: "center", gap: 6 }}>
          <span style={{ fontSize: 14 }}>🖼️</span>Gallery
        </button>
      </div>
    </div>
  );

  if (phase === "scanning") return (
    <div style={{ minHeight: "100vh", padding: "60px 16px 100px", display: "flex", flexDirection: "column", alignItems: "center", animation: "popIn .4s cubic-bezier(0.22,1.2,.36,1) both" }}>
      <h2 style={{ fontSize: 22, fontWeight: 800, marginBottom: 24 }}>Analysing Meal</h2>
      <div style={{ width: "100%", maxWidth: 340, aspectRatio: "1/1", borderRadius: 20, background: "var(--card)", border: "1px solid var(--bdr)", position: "relative", overflow: "hidden", marginBottom: 28, display: "flex", alignItems: "center", justifyContent: "center" }}>
        {imagePreview
          ? <img src={imagePreview} alt="food" style={{ width: "100%", height: "100%", objectFit: "cover", borderRadius: 20 }} />
          : <span style={{ fontSize: 90 }}>🍗</span>
        }
        <div style={{ position: "absolute", left: 0, right: 0, height: 3, background: "linear-gradient(90deg, transparent, var(--acc), transparent)", animation: "sl 1.5s linear infinite", boxShadow: "0 0 14px var(--acc)" }} />
        <div style={{ position: "absolute", inset: 0, background: "linear-gradient(180deg, rgba(255,23,68,.04) 0%, transparent 100%)" }} />
      </div>
      <p style={{ fontSize: 14, fontWeight: 600, color: "var(--acc)", fontFamily: "var(--fm)", letterSpacing: ".05em", marginBottom: 20, minHeight: 20 }}>{statuses[statusIdx]}</p>
      <div style={{ width: "100%", maxWidth: 340 }}>
        <div style={{ width: "100%", height: 6, borderRadius: 6, background: "rgba(255,255,255,.05)", overflow: "hidden" }}>
          <div style={{ height: "100%", width: `${progress}%`, background: "var(--acc)", borderRadius: 6, boxShadow: "0 0 10px var(--acc)", transition: "width .035s linear" }} />
        </div>
        <div style={{ display: "flex", justifyContent: "space-between", marginTop: 8 }}>
          <span style={{ fontSize: 11, color: "var(--t3)", fontFamily: "var(--fm)" }}>AI Analysis</span>
          <span style={{ fontSize: 11, color: "var(--t2)", fontFamily: "var(--fm)" }}>{progress}%</span>
        </div>
      </div>
    </div>
  );

  // ---- Results phase -------------------------------------------------------
  if (scanError) return (
    <div style={{ minHeight: "100vh", padding: "60px 16px 100px", display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center", animation: "popIn .4s cubic-bezier(0.22,1.2,.36,1) both" }}>
      <div style={{ fontSize: 52, marginBottom: 16 }}>⚠️</div>
      <h2 style={{ fontSize: 20, fontWeight: 800, marginBottom: 10, textAlign: "center" }}>Scan Failed</h2>
      <p style={{ fontSize: 14, color: "var(--t3)", textAlign: "center", lineHeight: 1.6, marginBottom: 32, maxWidth: 300 }}>{scanError}</p>
      <button onClick={() => { setPhase("idle"); setScanError(null); setImagePreview(null); }}
        style={{ padding: "14px 32px", background: "var(--acc)", color: "#fff", border: "none", borderRadius: 14, fontSize: 15, fontWeight: 700, cursor: "pointer", boxShadow: "0 0 24px var(--accG)" }}>
        Try Again
      </button>
    </div>
  );

  const rScore = scanResult?.score ?? 0;
  const rRank  = getRank(rScore);
  const totCal  = Math.round(scanResult?.calories  ?? 0);
  const totPro  = Math.round(scanResult?.protein_g ?? 0);
  const totCarb = Math.round(scanResult?.carbs_g   ?? 0);
  const totFat  = Math.round(scanResult?.fat_g     ?? 0);
  const xpChange = scanResult?.xp_change ?? 0;

  return (
    <div style={{ padding: "60px 16px 100px", minHeight: "100vh", animation: "popIn .4s cubic-bezier(0.22,1.2,.36,1) both" }}>
      {/* Score + XP */}
      <div style={{ textAlign: "center", marginBottom: 24, animation: "rr .6s cubic-bezier(.34,1.56,.64,1) forwards" }}>
        <p style={{ fontSize: 10, fontWeight: 700, color: "var(--t3)", letterSpacing: ".12em", textTransform: "uppercase", fontFamily: "var(--fm)", marginBottom: 12 }}>Meal Ranked</p>
        <RankBadge rank={rScore} size="xl" animated />
        <div style={{ marginTop: 12 }}>
          <span style={{ fontSize: 52, fontWeight: 900, color: rRank.color, fontFamily: "var(--fm)" }}>{rScore}</span>
          <span style={{ fontSize: 16, color: "var(--t3)", fontFamily: "var(--fm)" }}>/100</span>
        </div>
        {scanResult && (
          <div style={{ marginTop: 10, display: "inline-flex", alignItems: "center", gap: 6, padding: "6px 16px", borderRadius: 20, background: xpChange >= 0 ? "rgba(0,229,255,.07)" : "rgba(255,23,68,.07)", border: `1px solid ${xpChange >= 0 ? "rgba(0,229,255,.2)" : "rgba(255,23,68,.2)"}` }}>
            <span style={{ fontSize: 13, fontWeight: 800, color: xpChange >= 0 ? "#00E5FF" : "var(--acc)", fontFamily: "var(--fm)" }}>
              {xpChange >= 0 ? "+" : ""}{xpChange} XP
            </span>
          </div>
        )}
      </div>

      {/* Identified food + thumbnail */}
      <Card style={{ marginBottom: 12 }}>
        <p style={{ fontSize: 10, fontWeight: 700, color: "var(--t3)", letterSpacing: ".1em", textTransform: "uppercase", fontFamily: "var(--fm)", marginBottom: 10 }}>Identified Food</p>
        <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
          {imagePreview
            ? <img src={imagePreview} alt="food" style={{ width: 60, height: 60, borderRadius: 12, objectFit: "cover", flexShrink: 0 }} />
            : <div style={{ width: 60, height: 60, borderRadius: 12, background: "var(--elev)", display: "flex", alignItems: "center", justifyContent: "center", fontSize: 28, flexShrink: 0 }}>🍽️</div>
          }
          <div>
            <p style={{ fontSize: 15, fontWeight: 700 }}>{scanResult?.food_name ?? "Unknown food"}</p>
            <p style={{ fontSize: 11, color: rRank.color, fontFamily: "var(--fm)", fontWeight: 600, marginTop: 3 }}>{scanResult?.meal_rank ?? ""}</p>
          </div>
        </div>
      </Card>

      {/* Macros */}
      <Card style={{ marginBottom: 12 }}>
        <p style={{ fontSize: 10, fontWeight: 700, color: "var(--t3)", letterSpacing: ".1em", textTransform: "uppercase", fontFamily: "var(--fm)", marginBottom: 12 }}>Macros</p>
        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr 1fr 1fr", gap: 8 }}>
          {[
            { l: "CAL", v: totCal, unit: "",  color: "var(--acc)" },
            { l: "PRO", v: totPro, unit: "g", color: "#00E5FF" },
            { l: "CARB",v: totCarb,unit: "g", color: "#FFD700" },
            { l: "FAT", v: totFat, unit: "g", color: "#B388FF" },
          ].map(m => (
            <div key={m.l} style={{ textAlign: "center", background: "rgba(255,255,255,.03)", borderRadius: 10, padding: "10px 4px" }}>
              <div style={{ fontSize: 16, fontWeight: 800, color: m.color, fontFamily: "var(--fm)" }}>{m.v}{m.unit}</div>
              <div style={{ fontSize: 9, color: "var(--t3)", fontFamily: "var(--fm)", letterSpacing: ".06em", marginTop: 2 }}>{m.l}</div>
            </div>
          ))}
        </div>
      </Card>

      {/* FoodScience — Gemini's health tip */}
      <Card style={{ marginBottom: 16, border: `1px solid ${rRank.color}20`, background: `linear-gradient(135deg, var(--card), ${rRank.color}08)` }}>
        <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 10 }}>
          <span style={{ fontSize: 16 }}>🔬</span>
          <p style={{ fontSize: 11, fontWeight: 700, color: rRank.color, letterSpacing: ".08em", textTransform: "uppercase", fontFamily: "var(--fm)" }}>FoodScience</p>
        </div>
        <p style={{ fontSize: 13, lineHeight: 1.6, color: "var(--t2)" }}>
          {scanResult?.explanation || "Nutritional analysis complete."}
        </p>
      </Card>

      <button
        onClick={() => {
          if (scanResult) {
            const mealObj = {
              id: Date.now(),
              name: scanResult.food_name,
              foods: [scanResult.food_name],
              photo: "📷",
              cal: totCal, protein: totPro, carbs: totCarb, fat: totFat,
              score: rScore,
              time: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
            };
            setSel(mealObj);
            go("mr");
          } else {
            go("home");
          }
        }}
        style={{ width: "100%", padding: "14px 0", background: "var(--acc)", color: "#fff", border: "none", borderRadius: 14, fontSize: 15, fontWeight: 700, cursor: "pointer", boxShadow: "0 0 24px var(--accG)" }}>
        Save Meal
      </button>
    </div>
  );
};

const Profile = ({ user }) => {
  const avg = 85;
  const weekScores = [72, 78, 85, 80, 91, 88, 85];
  const days = ["M", "T", "W", "T", "F", "S", "S"];
  const maxScore = Math.max(...weekScores);
  const rankHistory = [
    { period: "This Week", rank: "Diamond", score: 85 },
    { period: "Last Week", rank: "Platinum", score: 77 },
    { period: "2 Weeks Ago", rank: "Platinum", score: 73 },
    { period: "3 Weeks Ago", rank: "Gold", score: 64 },
  ];
  return (
    <div style={{ minHeight: "100vh", padding: "16px 16px 100px", animation: "popIn .4s cubic-bezier(0.22,1.2,.36,1) both" }}>
      <div style={{ textAlign: "center", marginBottom: 16, animation: "sf 3s ease-in-out infinite" }}>
        <RankBadge rank={avg} size="xl" animated />
      </div>
      {(() => {
        const TIERS = [
          { name: "Silver",   min: 40,  color: "#90A4AE" },
          { name: "Gold",     min: 55,  color: "#FFD600" },
          { name: "Platinum", min: 70,  color: "#B2EBF2" },
          { name: "Diamond",  min: 80,  color: "#40C4FF" },
          { name: "Crimson",  min: 90,  color: "#FF1744" },
        ];
        const currentTierIdx = [...TIERS].reverse().findIndex(t => avg >= t.min);
        const nextTier = currentTierIdx === -1 ? TIERS[0] : TIERS[TIERS.length - 1 - currentTierIdx + 1];
        const currentFloor = currentTierIdx === -1 ? 0 : TIERS[TIERS.length - 1 - currentTierIdx].min;
        const isMax = avg >= 90;
        const pct = isMax ? 1 : Math.min(1, (avg - currentFloor) / (nextTier.min - currentFloor));
        const ptsLeft = isMax ? 0 : nextTier.min - avg;
        return (
          <div style={{ marginBottom: 16, display: "flex", flexDirection: "column", alignItems: "center", gap: 6 }}>
            {isMax ? (
              <span style={{ fontSize: 11, fontWeight: 800, color: "#FF1744", fontFamily: "var(--fm)", letterSpacing: ".1em" }}>MAX RANK</span>
            ) : (
              <>
                <div style={{ width: 160, height: 6, borderRadius: 3, background: "var(--bdr)", overflow: "hidden" }}>
                  <div style={{ height: "100%", width: `${pct * 100}%`, borderRadius: 3, background: nextTier.color, boxShadow: `0 0 6px ${nextTier.color}88`, transition: "width .6s ease" }} />
                </div>
                <span style={{ fontSize: 11, fontWeight: 700, color: nextTier.color, fontFamily: "var(--fm)" }}>{ptsLeft} pts to {nextTier.name}</span>
              </>
            )}
          </div>
        );
      })()}
      <div style={{ textAlign: "center", marginBottom: 20 }}>
        <h2 style={{ fontSize: 22, fontWeight: 800 }}>@{user.username}</h2>
        <p style={{ color: "var(--t3)", fontFamily: "var(--fm)", fontSize: 12 }}>{user.goal.toUpperCase()} · {user.calories}kcal</p>
      </div>
      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr 1fr", gap: 6, marginBottom: 16 }}>
        {[{ l: "Meals", v: "147", i: "📊" }, { l: "Streak", v: "27", i: "🔥" }, { l: "Best", v: "Crimson", i: "💎", c: "#FF1744" }].map((s, i) => (
          <Card key={s.l} style={{ textAlign: "center", padding: "12px 6px", animation: `popIn .4s ${0.1 + i * 0.05}s cubic-bezier(0.22,1.2,.36,1) both` }}>
            <div style={{ fontSize: 16, marginBottom: 3 }}>{s.i}</div>
            <div style={{ fontSize: 17, fontWeight: 800, color: s.c || "var(--t1)", fontFamily: "var(--fm)" }}>{s.v}</div>
            <div style={{ fontSize: 8, color: "var(--t3)", fontFamily: "var(--fm)", letterSpacing: ".05em", marginTop: 2 }}>{s.l.toUpperCase()}</div>
          </Card>
        ))}
      </div>
      <Card style={{ marginBottom: 12 }}>
        <p style={{ fontSize: 10, fontWeight: 700, color: "var(--t3)", letterSpacing: ".1em", textTransform: "uppercase", fontFamily: "var(--fm)", marginBottom: 14 }}>This Week</p>
        <div style={{ display: "flex", alignItems: "flex-end", gap: 6, height: 90 }}>
          {weekScores.map((sc, i) => {
            const rr = getRank(sc);
            const h = Math.round((sc / maxScore) * 72);
            return (
              <div key={i} style={{ flex: 1, display: "flex", flexDirection: "column", alignItems: "center", gap: 4 }}>
                <div style={{ width: "100%", height: h, borderRadius: "4px 4px 0 0", background: rr.color, boxShadow: `0 0 8px ${rr.glow}` }} />
                <span style={{ fontSize: 9, color: "var(--t3)", fontFamily: "var(--fm)" }}>{days[i]}</span>
              </div>
            );
          })}
        </div>
        <div style={{ display: "flex", justifyContent: "space-between", marginTop: 8 }}>
          <span style={{ fontSize: 10, color: "var(--t3)", fontFamily: "var(--fm)" }}>Avg: {Math.round(weekScores.reduce((a, b) => a + b) / weekScores.length)}</span>
          <span style={{ fontSize: 10, color: "var(--t3)", fontFamily: "var(--fm)" }}>Best: {maxScore}</span>
        </div>
      </Card>
      <Card style={{ marginBottom: 12 }}>
        <p style={{ fontSize: 10, fontWeight: 700, color: "var(--t3)", letterSpacing: ".1em", textTransform: "uppercase", fontFamily: "var(--fm)", marginBottom: 12 }}>Rank History</p>
        {rankHistory.map((rh, i) => {
          const rr = getRank(rh.rank === "Crimson" ? 90 : rh.rank === "Diamond" ? 80 : rh.rank === "Platinum" ? 70 : rh.rank === "Gold" ? 55 : 40);
          return (
            <div key={i} style={{ display: "flex", alignItems: "center", gap: 10, padding: "8px 0", borderBottom: i < rankHistory.length - 1 ? "1px solid var(--bdr)" : "none" }}>
              <RankBadge rank={rh.rank} size="xs" showLabel={false} />
              <span style={{ flex: 1, fontSize: 13, fontWeight: 600 }}>{rh.period}</span>
              <span style={{ fontSize: 13, fontWeight: 700, color: rr.color, fontFamily: "var(--fm)" }}>{rh.score}</span>
              <span style={{ fontSize: 11, fontWeight: 600, color: rr.color, fontFamily: "var(--fm)" }}>{rh.rank}</span>
            </div>
          );
        })}
      </Card>
      <p style={{ fontSize: 10, fontWeight: 700, color: "var(--t3)", letterSpacing: ".1em", textTransform: "uppercase", fontFamily: "var(--fm)", marginBottom: 10 }}>Meal Gallery</p>
      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr 1fr", gap: 6 }}>
        {MOCK_MEALS.map(meal => {
          const mr = getRank(meal.score);
          return (
            <div key={meal.id} style={{ aspectRatio: "1/1", borderRadius: 14, background: "var(--card)", border: `1px solid ${mr.color}30`, display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center", gap: 4 }}>
              <span style={{ fontSize: 28 }}>{meal.photo}</span>
              <span style={{ fontSize: 11, fontWeight: 800, color: mr.color, fontFamily: "var(--fm)" }}>{meal.score}</span>
            </div>
          );
        })}
      </div>
    </div>
  );
};

const Leaderboard = () => {
  const [tab, setTab] = useState("global");
  const top3 = MOCK_LEADERBOARD.slice(0, 3);
  const rest = MOCK_LEADERBOARD.slice(3);
  const podiumColors = ["#FFD700", "#C0C0C0", "#CD7F32"];
  const podiumHeights = [84, 56, 42];
  const podiumOrder = [1, 0, 2];
  const rankScore = name => name === "Crimson" ? 90 : name === "Diamond" ? 80 : name === "Platinum" ? 70 : name === "Gold" ? 55 : name === "Silver" ? 40 : 0;
  return (
    <div style={{ minHeight: "100vh", padding: "16px 16px 100px", animation: "popIn .4s cubic-bezier(0.22,1.2,.36,1) both" }}>
      <h2 style={{ fontSize: 22, fontWeight: 800, marginBottom: 14 }}>Leaderboard</h2>
      <div style={{ display: "flex", background: "var(--card)", borderRadius: 12, padding: 4, marginBottom: 24, border: "1px solid var(--bdr)" }}>
        {["global", "friends", "weekly"].map(t => (
          <button key={t} onClick={() => setTab(t)} style={{ flex: 1, padding: "8px 0", background: tab === t ? "var(--acc)" : "none", border: "none", borderRadius: 9, color: tab === t ? "#fff" : "var(--t3)", fontSize: 12, fontWeight: 700, cursor: "pointer", textTransform: "capitalize", fontFamily: "var(--fm)", transition: "all .2s", boxShadow: tab === t ? "0 0 16px var(--accG)" : "none" }}>{t}</button>
        ))}
      </div>
      <div style={{ display: "flex", alignItems: "flex-end", justifyContent: "center", gap: 10, marginBottom: 24 }}>
        {podiumOrder.map(idx => {
          const u = top3[idx];
          const place = idx + 1;
          const rr = getRank(rankScore(u.rank));
          const isFirst = idx === 0;
          return (
            <div key={idx} style={{ display: "flex", flexDirection: "column", alignItems: "center", flex: isFirst ? 1.2 : 1 }}>
              {isFirst && <span style={{ fontSize: 22, marginBottom: 4 }}>👑</span>}
              <div style={{ fontSize: isFirst ? 36 : 28, width: isFirst ? 64 : 52, height: isFirst ? 64 : 52, borderRadius: "50%", background: "var(--card)", border: `2px solid ${podiumColors[idx]}`, display: "flex", alignItems: "center", justifyContent: "center", marginBottom: 6, boxShadow: `0 0 16px ${rr.glow}` }}>{u.avatar}</div>
              <span style={{ fontSize: 11, fontWeight: 700, marginBottom: 2 }}>@{u.username}</span>
              <span style={{ fontSize: 12, fontWeight: 800, color: rr.color, fontFamily: "var(--fm)", marginBottom: 6 }}>{u.score}</span>
              <div style={{ width: "100%", height: podiumHeights[idx], borderRadius: "8px 8px 0 0", background: `linear-gradient(180deg, ${podiumColors[idx]}28, ${podiumColors[idx]}0a)`, border: `1px solid ${podiumColors[idx]}40`, display: "flex", alignItems: "center", justifyContent: "center" }}>
                <span style={{ fontSize: 18, fontWeight: 900, color: podiumColors[idx], fontFamily: "var(--fm)" }}>{place}</span>
              </div>
            </div>
          );
        })}
      </div>
      <div style={{ display: "flex", flexDirection: "column", gap: 6 }}>
        {rest.map((u, i) => {
          const rr = getRank(rankScore(u.rank));
          return (
            <Card key={i} style={{ display: "flex", alignItems: "center", gap: 10, padding: "10px 12px", animation: `popIn .4s ${0.1 + i * 0.05}s cubic-bezier(0.22,1.2,.36,1) both` }}>
              <span style={{ fontSize: 13, fontWeight: 700, color: "var(--t3)", fontFamily: "var(--fm)", width: 20 }}>{i + 4}</span>
              <span style={{ fontSize: 20 }}>{u.avatar}</span>
              <div style={{ flex: 1 }}>
                <span style={{ fontSize: 13, fontWeight: 600 }}>@{u.username}</span>
                <div style={{ fontSize: 10, color: "var(--t3)", fontFamily: "var(--fm)" }}>🔥 {u.streak}d</div>
              </div>
              <span style={{ fontSize: 14, fontWeight: 800, color: rr.color, fontFamily: "var(--fm)" }}>{u.score}</span>
              <RankBadge rank={u.rank} size="sm" showLabel={false} />
            </Card>
          );
        })}
      </div>
    </div>
  );
};

const Share = ({ user }) => {
  const meal = MOCK_MEALS[0];
  const r = getRank(meal.score);
  const totalCals = meal.protein * 4 + meal.carbs * 4 + meal.fat * 9;
  return (
    <div style={{ minHeight: "100vh", padding: "16px 16px 100px", display: "flex", flexDirection: "column", alignItems: "center", animation: "popIn .4s cubic-bezier(0.22,1.2,.36,1) both" }}>
      <h2 style={{ fontSize: 20, fontWeight: 800, marginBottom: 14, alignSelf: "flex-start" }}>Share Meal</h2>
      <div style={{ width: "100%", maxWidth: 340, borderRadius: 24, background: "linear-gradient(165deg, #0C0C12, #121220, #1A0A12)", border: `1.5px solid ${r.color}20`, padding: 20, boxShadow: `0 0 40px ${r.glow}`, marginBottom: 16 }}>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 18 }}>
          <div style={{ display: "flex", alignItems: "center", gap: 6 }}>
            <img src={LOGO_IMAGE} alt="MR" style={{ width: 38, height: 38, objectFit: "contain", mixBlendMode: "screen" }} />
            <span style={{ fontSize: 12, fontWeight: 800 }}>Macro<span style={{ color: "var(--acc)" }}>Ranked</span></span>
          </div>
          <span style={{ fontSize: 10, color: "var(--t3)", fontFamily: "var(--fm)" }}>@{user.username}</span>
        </div>
        <div style={{ width: "100%", aspectRatio: "1/1", borderRadius: 16, background: "var(--card)", display: "flex", alignItems: "center", justifyContent: "center", fontSize: 80, marginBottom: 16, position: "relative", border: `1px solid ${r.color}15` }}>
          {meal.photo}
          <div style={{ position: "absolute", top: 10, right: 10 }}>
            <RankBadge rank={meal.score} size="sm" showLabel={false} animated />
          </div>
        </div>
        <div style={{ textAlign: "center", marginBottom: 14 }}>
          <div style={{ fontSize: 42, fontWeight: 900, fontFamily: "var(--fm)" }}>
            <span style={{ color: r.color }}>{meal.score}</span>
            <span style={{ fontSize: 16, color: "var(--t3)" }}>/100</span>
          </div>
          <p style={{ fontSize: 12, color: "var(--t2)", marginTop: 2 }}>{meal.name}</p>
        </div>
        <div style={{ marginBottom: 14 }}>
          <div style={{ display: "flex", height: 6, borderRadius: 6, overflow: "hidden" }}>
            {[{ val: meal.protein * 4, color: "#00E5FF" }, { val: meal.carbs * 4, color: "#FFD700" }, { val: meal.fat * 9, color: "#B388FF" }].map((seg, i) => (
              <div key={i} style={{ flex: seg.val / totalCals, background: seg.color }} />
            ))}
          </div>
          <div style={{ display: "flex", justifyContent: "space-between", marginTop: 6 }}>
            {[{ l: "P", v: meal.protein, c: "#00E5FF" }, { l: "C", v: meal.carbs, c: "#FFD700" }, { l: "F", v: meal.fat, c: "#B388FF" }].map(m => (
              <span key={m.l} style={{ fontSize: 10, color: m.c, fontFamily: "var(--fm)", fontWeight: 700 }}>{m.l} {m.v}g</span>
            ))}
          </div>
        </div>
        <p style={{ fontSize: 11, color: "var(--t3)", textAlign: "center", fontStyle: "italic" }}>"{meal.score >= 80 ? "Eating like a champion 💪" : meal.score >= 70 ? "Fueling the grind 🔥" : "Making progress every day 📈"}"</p>
      </div>
      <div style={{ width: "100%", maxWidth: 340, display: "flex", flexDirection: "column", gap: 8 }}>
        {[
          { l: "Share to Instagram Stories", i: "📸", primary: true },
          { l: "Copy Image", i: "📋", primary: false },
          { l: "Share Link", i: "↗", primary: false },
        ].map(btn => (
          <button key={btn.l} style={{ width: "100%", padding: "14px 0", background: btn.primary ? "var(--acc)" : "var(--card)", color: btn.primary ? "#fff" : "var(--t1)", border: btn.primary ? "none" : "1px solid var(--bdr)", borderRadius: 14, fontSize: 14, fontWeight: 700, cursor: "pointer", display: "flex", alignItems: "center", justifyContent: "center", gap: 8, boxShadow: btn.primary ? "0 0 24px var(--accG)" : "none" }}>
            <span>{btn.i}</span>{btn.l}
          </button>
        ))}
      </div>
    </div>
  );
};

// --- ONBOARDING ---
// --- Onboarding Shell (progress bar + pinned continue button) ---
const OnboardingShell = ({ step, total, onBack, canContinue, onContinue, continueLabel = "Continue", children }) => (
  <div style={{ minHeight: "100vh", display: "flex", flexDirection: "column", animation: "popIn .4s cubic-bezier(0.22,1.2,.36,1) both" }}>
    <div style={{ padding: "16px 20px 0", display: "flex", alignItems: "center", gap: 12, flexShrink: 0 }}>
      <button onClick={onBack} style={{ background: "none", border: "none", cursor: "pointer", color: "var(--t2)", fontSize: 22, padding: "4px 8px 4px 0", lineHeight: 1, fontWeight: 300 }}>←</button>
      <div style={{ flex: 1, height: 3, borderRadius: 3, background: "rgba(255,255,255,.07)", overflow: "hidden" }}>
        <div style={{ height: "100%", width: `${(step / total) * 100}%`, background: "var(--acc)", boxShadow: "0 0 8px var(--accG)", borderRadius: 3, transition: "width .4s cubic-bezier(0.22,1.2,.36,1)" }} />
      </div>
      <span style={{ fontSize: 10, fontWeight: 700, color: "var(--t3)", fontFamily: "var(--fm)", letterSpacing: ".08em", whiteSpace: "nowrap" }}>{step}/{total}</span>
    </div>
    <div style={{ flex: 1, padding: "32px 24px 20px", overflowY: "auto" }}>
      {children}
    </div>
    <div style={{ padding: "0 24px 36px", flexShrink: 0 }}>
      <button onClick={() => canContinue && onContinue()} disabled={!canContinue} style={{ width: "100%", padding: "17px 0", background: canContinue ? "var(--acc)" : "var(--elev)", color: canContinue ? "#fff" : "var(--t3)", border: "none", borderRadius: 14, fontSize: 16, fontWeight: 700, opacity: canContinue ? 1 : 0.4, cursor: canContinue ? "pointer" : "default", boxShadow: canContinue ? "0 0 28px var(--accG)" : "none", transition: "all .2s" }}>{continueLabel}</button>
    </div>
  </div>
);

const Onboarding = ({ onDone }) => {
  const [step, setStep] = useState(0);
  const [animKey, setAnimKey] = useState(0);
  const [d, setD] = useState({
    goal: "", gender: "", age: "", username: "",
    height_cm: 177.8, weight_kg: 75,
    activityFactor: 1.55,
    motivation: [],
    calories: 2500, protein: 180, carbs: 280, fat: 70,
  });
  const [heightUnit, setHeightUnit] = useState("cm");
  const [weightUnit, setWeightUnit] = useState("kg");
  // Picker indices: cm 140-210 default 175 (idx 35), ft 4'8"-6'10" default 5'9" (idx 13), kg 40-150 default 70 (idx 30), lbs 90-330 default 154 (idx 64)
  const [heightCmIdx, setHeightCmIdx] = useState(35);
  const [heightFtIdx, setHeightFtIdx] = useState(13);
  const [weightKgIdx, setWeightKgIdx] = useState(30);
  const [weightLbsIdx, setWeightLbsIdx] = useState(64);

  const TOTAL_STEPS = 11;
  const goNext = (n) => { setAnimKey(k => k + 1); setStep(n); };
  const goBack = () => { setAnimKey(k => k + 1); setStep(s => Math.max(0, s - 1)); };

  // --- Calc helpers ---
  const r5 = v => Math.round(v / 5) * 5;

  const calcMacros = (goal, wkg, cal) => {
    if (goal === "bulk") {
      const p = r5(wkg * 2.2), f = r5(cal * 0.25 / 9);
      return { protein: p, fat: f, carbs: Math.max(0, r5((cal - p * 4 - f * 9) / 4)) };
    } else if (goal === "cut") {
      const p = r5(wkg * 2.4), f = r5(cal * 0.25 / 9);
      return { protein: p, fat: f, carbs: Math.max(0, r5((cal - p * 4 - f * 9) / 4)) };
    } else {
      const p = r5(wkg * 2.0), f = r5(cal * 0.28 / 9);
      return { protein: p, fat: f, carbs: Math.max(0, r5((cal - p * 4 - f * 9) / 4)) };
    }
  };

  const calcTargets = (state) => {
    const { weight_kg, height_cm, age, gender, activityFactor, goal } = state;
    const bmr = gender === "female"
      ? 10 * weight_kg + 6.25 * height_cm - 5 * age - 161
      : 10 * weight_kg + 6.25 * height_cm - 5 * age + 5;
    const tdee = bmr * activityFactor;
    const base = goal === "bulk" ? tdee + 400 : goal === "cut" ? tdee - 500 : tdee;
    const cal = Math.round(base / 50) * 50;
    return { calories: cal, ...calcMacros(goal, weight_kg, cal) };
  };

  const isCustom = () => {
    const rec = calcMacros(d.goal, d.weight_kg, d.calories);
    return d.protein !== rec.protein || d.carbs !== rec.carbs || d.fat !== rec.fat;
  };

  // --- Shared styles ---
  const inputWrap = { background: "var(--card)", borderRadius: 16, border: "1px solid var(--bdr)", display: "flex", alignItems: "center", overflow: "hidden" };
  const numInput = { background: "none", border: "none", outline: "none", color: "var(--t1)", fontSize: 44, fontWeight: 800, padding: "22px 20px", width: "100%", fontFamily: "var(--fd)", textAlign: "center" };
  const unitLbl = { paddingRight: 22, color: "var(--t3)", fontFamily: "var(--fm)", fontSize: 16, whiteSpace: "nowrap", fontWeight: 700 };

  const ScrollPicker = ({ items, selectedIndex, onChange }) => {
    const ITEM_H = 48;
    const ref = useRef(null);
    const isSyncing = useRef(false);

    useEffect(() => {
      const el = ref.current;
      if (!el) return;
      isSyncing.current = true;
      el.scrollTop = selectedIndex * ITEM_H;
      setTimeout(() => { isSyncing.current = false; }, 50);
    }, [selectedIndex]);

    const onScroll = () => {
      if (isSyncing.current) return;
      const el = ref.current;
      if (!el) return;
      const idx = Math.round(el.scrollTop / ITEM_H);
      if (idx !== selectedIndex && idx >= 0 && idx < items.length) onChange(idx);
    };

    return (
      <div style={{ background: "var(--card)", border: "1px solid var(--bdr)", borderRadius: 20, overflow: "hidden", position: "relative", height: 250 }}>
        {/* Selected row highlight with top/bottom hairlines */}
        <div style={{ position: "absolute", left: 0, right: 0, top: "50%", transform: "translateY(-50%)", height: ITEM_H, pointerEvents: "none", zIndex: 1 }}>
          <div style={{ position: "absolute", top: 0, left: 16, right: 16, height: 1, background: "var(--bdrL)" }} />
          <div style={{ position: "absolute", bottom: 0, left: 16, right: 16, height: 1, background: "var(--bdrL)" }} />
        </div>
        {/* Top/bottom fade over card background */}
        <div style={{ position: "absolute", inset: 0, background: "linear-gradient(to bottom, var(--card) 0%, transparent 28%, transparent 72%, var(--card) 100%)", pointerEvents: "none", zIndex: 2 }} />
        <div
          ref={ref}
          onScroll={onScroll}
          style={{ width: "100%", height: 250, overflowY: "scroll", scrollSnapType: "y mandatory", scrollbarWidth: "none", msOverflowStyle: "none" }}
        >
          <div style={{ height: 101 }} />
          {items.map((item, i) => {
            const dist = Math.abs(i - selectedIndex);
            const isSelected = dist === 0;
            const opacity = isSelected ? 1 : dist === 1 ? 0.45 : dist === 2 ? 0.2 : 0.08;
            return (
              <div
                key={i}
                onClick={() => { onChange(i); isSyncing.current = true; ref.current.scrollTo({ top: i * ITEM_H, behavior: "smooth" }); setTimeout(() => { isSyncing.current = false; }, 400); }}
                style={{ height: ITEM_H, display: "flex", alignItems: "center", justifyContent: "center", scrollSnapAlign: "center", opacity, color: isSelected ? "var(--t1)" : "var(--t2)", fontFamily: "var(--fm)", fontWeight: isSelected ? 700 : 400, fontSize: isSelected ? 20 : 16, letterSpacing: isSelected ? "-.01em" : "0", cursor: "pointer", userSelect: "none", transition: "opacity .1s, font-size .1s" }}
              >
                {item}
              </div>
            );
          })}
          <div style={{ height: 101 }} />
        </div>
      </div>
    );
  };

  const UnitToggle = ({ options, value, onChange }) => (
    <div style={{ display: "flex", gap: 6, background: "var(--card)", borderRadius: 12, padding: 4, border: "1px solid var(--bdr)", marginBottom: 24 }}>
      {options.map(([val, lbl]) => (
        <button key={val} onClick={() => onChange(val)} style={{ flex: 1, padding: "8px 0", background: value === val ? "var(--acc)" : "none", color: value === val ? "#fff" : "var(--t3)", border: "none", borderRadius: 9, fontSize: 13, fontWeight: 700, cursor: "pointer", transition: "all .15s", fontFamily: "var(--fd)", boxShadow: value === val ? "0 0 12px var(--accG)" : "none" }}>{lbl}</button>
      ))}
    </div>
  );

  const OptionCard = ({ id, selected, onSelect, icon, label, desc, multi }) => (
    <div onClick={() => onSelect(id)} style={{ background: selected ? "rgba(255,23,68,.07)" : "var(--card)", border: selected ? "1.5px solid var(--acc)" : "1.5px solid var(--bdr)", borderRadius: 16, padding: "18px 18px", cursor: "pointer", display: "flex", alignItems: "center", gap: 14, transition: "background .15s, border-color .15s" }}>
      {icon && <div style={{ fontSize: 22, width: 48, height: 48, borderRadius: 13, background: "var(--elev)", display: "flex", alignItems: "center", justifyContent: "center", flexShrink: 0 }}>{icon}</div>}
      <div style={{ flex: 1 }}>
        <div style={{ fontSize: 16, fontWeight: 700 }}>{label}</div>
        {desc && <div style={{ fontSize: 12, color: "var(--t2)", marginTop: 2 }}>{desc}</div>}
      </div>
      {selected && <div style={{ width: 22, height: 22, borderRadius: multi ? 6 : "50%", background: "var(--acc)", display: "flex", alignItems: "center", justifyContent: "center", fontSize: 11, color: "#fff", flexShrink: 0 }}>✓</div>}
    </div>
  );

  // --- Step 0: Splash ---
  if (step === 0) return <SplashScreen onStart={() => goNext(1)} />;

  // --- Step 1: Goal ---
  if (step === 1) return (
    <OnboardingShell key={animKey} step={1} total={TOTAL_STEPS} onBack={() => goNext(0)} canContinue={!!d.goal} onContinue={() => goNext(2)}>
      <h2 style={{ fontSize: 30, fontWeight: 800, marginBottom: 8, letterSpacing: "-.02em" }}>What's your goal?</h2>
      <p style={{ color: "var(--t2)", fontSize: 15, marginBottom: 28 }}>This will be used to calibrate your custom plan.</p>
      <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
        {[
          { id: "bulk", icon: "📈", label: "Bulk", desc: "Build muscle & gain weight" },
          { id: "cut", icon: "🔥", label: "Cut", desc: "Lose fat & get lean" },
          { id: "maintain", icon: "⚖️", label: "Maintain", desc: "Stay where you are" },
        ].map(g => <OptionCard key={g.id} id={g.id} selected={d.goal === g.id} onSelect={id => setD(prev => ({ ...prev, goal: id }))} icon={g.icon} label={g.label} desc={g.desc} />)}
      </div>
    </OnboardingShell>
  );

  // --- Step 2: Gender ---
  if (step === 2) return (
    <OnboardingShell key={animKey} step={2} total={TOTAL_STEPS} onBack={goBack} canContinue={!!d.gender} onContinue={() => goNext(3)}>
      <h2 style={{ fontSize: 30, fontWeight: 800, marginBottom: 8, letterSpacing: "-.02em" }}>Choose your Gender</h2>
      <p style={{ color: "var(--t2)", fontSize: 15, marginBottom: 28 }}>This will be used to calibrate your custom plan.</p>
      <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
        {[
          { id: "male", icon: "♂", label: "Male" },
          { id: "female", icon: "♀", label: "Female" },
          { id: "other", icon: "◌", label: "Other" },
        ].map(g => <OptionCard key={g.id} id={g.id} selected={d.gender === g.id} onSelect={id => setD(prev => ({ ...prev, gender: id }))} icon={g.icon} label={g.label} />)}
      </div>
    </OnboardingShell>
  );

  // --- Step 3: Age ---
  if (step === 3) return (
    <OnboardingShell key={animKey} step={3} total={TOTAL_STEPS} onBack={goBack} canContinue={d.age >= 10 && d.age <= 100} onContinue={() => goNext(4)}>
      <h2 style={{ fontSize: 30, fontWeight: 800, marginBottom: 8, letterSpacing: "-.02em" }}>How old are you?</h2>
      <p style={{ color: "var(--t2)", fontSize: 15, marginBottom: 40 }}>This will be used to calibrate your custom plan.</p>
      <div style={inputWrap}>
        <input type="number" min="10" max="100" value={d.age || ""} placeholder="25" onChange={e => setD(prev => ({ ...prev, age: Number(e.target.value) }))} style={numInput} />
        <span style={unitLbl}>yrs</span>
      </div>
    </OnboardingShell>
  );

  // --- Step 4: Height ---
  const cmItems = Array.from({ length: 71 }, (_, i) => `${140 + i} cm`);
  const ftItems = (() => {
    const items = [];
    for (let total = 56; total <= 82; total++) {
      const ft = Math.floor(total / 12), inch = total % 12;
      items.push(`${ft}'${inch}"`);
    }
    return items;
  })();
  if (step === 4) return (
    <OnboardingShell key={animKey} step={4} total={TOTAL_STEPS} onBack={goBack} canContinue={d.height_cm >= 100} onContinue={() => goNext(5)}>
      <h2 style={{ fontSize: 30, fontWeight: 800, marginBottom: 8, letterSpacing: "-.02em" }}>What's your height?</h2>
      <p style={{ color: "var(--t2)", fontSize: 15, marginBottom: 24 }}>This will be used to calibrate your custom plan.</p>
      <UnitToggle options={[["cm", "cm"], ["ft", "ft / in"]]} value={heightUnit} onChange={u => {
        setHeightUnit(u);
        if (u === "cm") { const cm = 140 + heightCmIdx; setD(prev => ({ ...prev, height_cm: cm })); }
        else { const totalIn = 56 + heightFtIdx; setD(prev => ({ ...prev, height_cm: Math.round(totalIn * 2.54 * 10) / 10 })); }
      }} />
      {heightUnit === "cm"
        ? <ScrollPicker items={cmItems} selectedIndex={heightCmIdx} onChange={i => { setHeightCmIdx(i); setD(prev => ({ ...prev, height_cm: 140 + i })); }} />
        : <ScrollPicker items={ftItems} selectedIndex={heightFtIdx} onChange={i => { setHeightFtIdx(i); const totalIn = 56 + i; setD(prev => ({ ...prev, height_cm: Math.round(totalIn * 2.54 * 10) / 10 })); }} />
      }
    </OnboardingShell>
  );

  // --- Step 5: Weight ---
  const kgItems = Array.from({ length: 111 }, (_, i) => `${40 + i} kg`);
  const lbsItems = Array.from({ length: 241 }, (_, i) => `${90 + i} lbs`);
  if (step === 5) return (
    <OnboardingShell key={animKey} step={5} total={TOTAL_STEPS} onBack={goBack} canContinue={d.weight_kg >= 20} onContinue={() => goNext(6)}>
      <h2 style={{ fontSize: 30, fontWeight: 800, marginBottom: 8, letterSpacing: "-.02em" }}>What's your weight?</h2>
      <p style={{ color: "var(--t2)", fontSize: 15, marginBottom: 24 }}>This will be used to calibrate your custom plan.</p>
      <UnitToggle options={[["kg", "kg"], ["lbs", "lbs"]]} value={weightUnit} onChange={u => {
        setWeightUnit(u);
        if (u === "kg") setD(prev => ({ ...prev, weight_kg: 40 + weightKgIdx }));
        else setD(prev => ({ ...prev, weight_kg: Math.round((90 + weightLbsIdx) / 2.20462 * 10) / 10 }));
      }} />
      {weightUnit === "kg"
        ? <ScrollPicker items={kgItems} selectedIndex={weightKgIdx} onChange={i => { setWeightKgIdx(i); setD(prev => ({ ...prev, weight_kg: 40 + i })); }} />
        : <ScrollPicker items={lbsItems} selectedIndex={weightLbsIdx} onChange={i => { setWeightLbsIdx(i); setD(prev => ({ ...prev, weight_kg: Math.round((90 + i) / 2.20462 * 10) / 10 })); }} />
      }
    </OnboardingShell>
  );

  // --- Step 6: Training Frequency ---
  if (step === 6) return (
    <OnboardingShell key={animKey} step={6} total={TOTAL_STEPS} onBack={goBack} canContinue={!!d.activityFactor} onContinue={() => goNext(7)}>
      <h2 style={{ fontSize: 30, fontWeight: 800, marginBottom: 8, letterSpacing: "-.02em" }}>How many times do you train per week?</h2>
      <p style={{ color: "var(--t2)", fontSize: 15, marginBottom: 28 }}>This helps us estimate your activity level.</p>
      <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
        {[
          { factor: 1.2, label: "0–2", desc: "Workouts now and then" },
          { factor: 1.55, label: "3–5", desc: "A few workouts per week" },
          { factor: 1.725, label: "6+", desc: "Dedicated athlete" },
        ].map(opt => <OptionCard key={opt.label} id={opt.factor} selected={d.activityFactor === opt.factor} onSelect={v => setD(prev => ({ ...prev, activityFactor: v }))} label={opt.label} desc={opt.desc} />)}
      </div>
    </OnboardingShell>
  );

  // --- Step 7: Motivation Graph ---
  if (step === 7) return <OnboardingGraph onContinue={() => goNext(8)} />;

  // --- Step 8: Social Motivation (multi-select) ---
  if (step === 8) return (
    <OnboardingShell key={animKey} step={8} total={TOTAL_STEPS} onBack={goBack} canContinue={d.motivation.length > 0}
      onContinue={() => {
        const targets = calcTargets(d);
        setD(prev => ({ ...prev, ...targets }));
        goNext(9);
      }}>
      <h2 style={{ fontSize: 30, fontWeight: 800, marginBottom: 8, letterSpacing: "-.02em" }}>How could involving others help you?</h2>
      <p style={{ color: "var(--t2)", fontSize: 15, marginBottom: 28 }}>We'll tailor your social features.</p>
      <div style={{ display: "flex", flexDirection: "column", gap: 10 }}>
        {["Keep me accountable", "Help me stay consistent", "Make the journey more fun", "Push me to improve", "Check in together", "Other"].map(m => (
          <OptionCard key={m} id={m} selected={d.motivation.includes(m)} multi
            onSelect={id => setD(prev => ({ ...prev, motivation: prev.motivation.includes(id) ? prev.motivation.filter(x => x !== id) : [...prev.motivation, id] }))}
            label={m}
          />
        ))}
      </div>
    </OnboardingShell>
  );

  // --- Step 9: Daily Targets ---
  if (step === 9) {
    const custom = isCustom();
    return (
      <OnboardingShell key={animKey} step={9} total={TOTAL_STEPS} onBack={goBack} canContinue={true} onContinue={() => goNext(10)}>
        <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: 8 }}>
          <h2 style={{ fontSize: 30, fontWeight: 800, letterSpacing: "-.02em" }}>Your daily targets</h2>
          <span style={{ fontSize: 9, fontWeight: 700, fontFamily: "var(--fm)", letterSpacing: ".06em", padding: "4px 10px", borderRadius: 20, background: custom ? "rgba(255,255,255,.06)" : "rgba(255,23,68,.1)", color: custom ? "var(--t3)" : "var(--acc)", border: custom ? "1px solid var(--bdr)" : "1px solid rgba(255,23,68,.2)" }}>{custom ? "CUSTOM" : "RECOMMENDED"}</span>
        </div>
        <p style={{ color: "var(--t2)", fontSize: 15, marginBottom: 22 }}>Calculated based on your stats. Adjust if needed.</p>
        <div style={{ background: "var(--card)", borderRadius: 16, border: "1px solid var(--bdr)", padding: 16, marginBottom: 10 }}>
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "baseline", marginBottom: 10 }}>
            <span style={{ fontSize: 11, fontWeight: 700, color: "var(--t3)", letterSpacing: ".1em", textTransform: "uppercase", fontFamily: "var(--fm)" }}>Calories</span>
            <span style={{ fontSize: 26, fontWeight: 900, color: "var(--acc)", fontFamily: "var(--fm)" }}>{d.calories}</span>
          </div>
          <input type="range" min="1200" max="4500" step="50" value={d.calories} onChange={e => { const cal = Number(e.target.value); setD(prev => ({ ...prev, calories: cal, ...calcMacros(prev.goal, prev.weight_kg, cal) })); }} style={{ width: "100%", accentColor: "#FF1744", cursor: "pointer" }} />
          <div style={{ display: "flex", justifyContent: "space-between", marginTop: 4 }}>
            <span style={{ fontSize: 10, color: "var(--t3)", fontFamily: "var(--fm)" }}>1200</span>
            <span style={{ fontSize: 10, color: "var(--t3)", fontFamily: "var(--fm)" }}>4500</span>
          </div>
        </div>
        {[
          { key: "protein", label: "Protein", unit: "g", color: "#00E5FF", min: 50, max: 400 },
          { key: "carbs", label: "Carbs", unit: "g", color: "#FFD700", min: 0, max: 600 },
          { key: "fat", label: "Fat", unit: "g", color: "#B388FF", min: 20, max: 200 },
        ].map(m => (
          <div key={m.key} style={{ background: "var(--card)", borderRadius: 16, border: "1px solid var(--bdr)", padding: 16, marginBottom: 10 }}>
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "baseline", marginBottom: 10 }}>
              <span style={{ fontSize: 11, fontWeight: 700, color: "var(--t3)", letterSpacing: ".1em", textTransform: "uppercase", fontFamily: "var(--fm)" }}>{m.label}</span>
              <span style={{ fontSize: 26, fontWeight: 900, color: m.color, fontFamily: "var(--fm)" }}>{d[m.key]}<span style={{ fontSize: 13, fontWeight: 600 }}>{m.unit}</span></span>
            </div>
            <input type="range" min={m.min} max={m.max} step="5" value={d[m.key]} onChange={e => setD(prev => ({ ...prev, [m.key]: Number(e.target.value) }))} style={{ width: "100%", accentColor: m.color, cursor: "pointer" }} />
            <div style={{ display: "flex", justifyContent: "space-between", marginTop: 4 }}>
              <span style={{ fontSize: 10, color: "var(--t3)", fontFamily: "var(--fm)" }}>{m.min}{m.unit}</span>
              <span style={{ fontSize: 10, color: "var(--t3)", fontFamily: "var(--fm)" }}>{m.max}{m.unit}</span>
            </div>
          </div>
        ))}
      </OnboardingShell>
    );
  }

  // --- Step 10: Username ---
  if (step === 10) return (
    <OnboardingShell key={animKey} step={10} total={TOTAL_STEPS} onBack={goBack} canContinue={d.username.length >= 3} onContinue={() => goNext(11)}>
      <h2 style={{ fontSize: 30, fontWeight: 800, marginBottom: 8, letterSpacing: "-.02em" }}>Choose your username</h2>
      <p style={{ color: "var(--t2)", fontSize: 15, marginBottom: 28 }}>This is how friends will find you.</p>
      <div style={{ background: "var(--card)", borderRadius: 16, border: "1px solid var(--bdr)", padding: "4px 18px", display: "flex", alignItems: "center", gap: 10 }}>
        <span style={{ color: "var(--t3)", fontSize: 20, fontWeight: 700 }}>@</span>
        <input type="text" placeholder="username" value={d.username} onChange={e => setD(prev => ({ ...prev, username: e.target.value.toLowerCase().replace(/[^a-z0-9_]/g, "").slice(0, 16) }))} style={{ background: "none", border: "none", outline: "none", color: "var(--t1)", fontSize: 22, fontWeight: 700, padding: "16px 0", width: "100%", fontFamily: "var(--fd)" }} autoCapitalize="none" autoCorrect="off" />
      </div>
      {d.username.length > 0 && (
        <p style={{ fontSize: 12, color: "var(--t3)", fontFamily: "var(--fm)", marginTop: 12, textAlign: "center" }}>
          macroranked.app/@<span style={{ color: "var(--t2)" }}>{d.username}</span>
        </p>
      )}
    </OnboardingShell>
  );

  // --- Step 11: Start ---
  return (
    <div style={{ minHeight: "100vh", display: "flex", flexDirection: "column", justifyContent: "center", alignItems: "center", padding: "40px 24px", animation: "popIn .4s cubic-bezier(0.22,1.2,.36,1) both" }}>
      <div style={{ animation: "sf 3s ease-in-out infinite", marginBottom: 24 }}>
        <img src={LOGO_IMAGE} alt="MacroRanked" style={{ width: 120, height: 120, objectFit: "contain", filter: "drop-shadow(0 0 40px rgba(255,23,68,0.65))", mixBlendMode: "screen" }} />
      </div>
      <h1 style={{ fontSize: 38, fontWeight: 900, letterSpacing: "-.03em", marginBottom: 10, textAlign: "center" }}>You're all set</h1>
      <p style={{ fontSize: 16, color: "var(--t2)", marginBottom: 52, textAlign: "center" }}>Time to earn your rank.</p>
      <div style={{ width: "100%", maxWidth: 380 }}>
        <button onClick={() => onDone({ ...d, activity: d.activityFactor })} style={{ width: "100%", padding: "18px 0", background: "var(--acc)", color: "#fff", border: "none", borderRadius: 14, fontSize: 18, fontWeight: 800, cursor: "pointer", boxShadow: "0 0 40px var(--accG)", letterSpacing: "-.01em" }}>
          Start Ranking
        </button>
      </div>
    </div>
  );
};

// --- MAIN ---
export default function App() {
  const [scr, setScr] = useState("auth");
  const [user, setUser] = useState(null);
  const [sel, setSel] = useState(null);

  // Called by AuthScreen after a successful login or signup.
  // isNewUser = true  → show onboarding so they can set up their profile.
  // isNewUser = false → build a minimal profile from auth data and go home.
  const handleAuthSuccess = (authData, isNewUser) => {
    if (isNewUser) {
      setScr("onboarding");
    } else {
      setUser({
        username: authData.email?.split("@")[0] ?? "user",
        email:    authData.email,
        goal:     "maintain",
        calories: 2000,
        protein:  150,
        carbs:    200,
        fat:      65,
      });
      setScr("home");
    }
  };

  return (
    <div className="shell">
      {scr === "auth"       && <AuthScreen onSuccess={handleAuthSuccess} />}
      {scr === "onboarding" && <Onboarding onDone={d => { setUser(d); setScr("home"); }} />}
      {scr === "home"       && user && <Home user={user} go={setScr} setSel={setSel} />}
      {scr === "mr"         && <MealResult meal={sel} go={setScr} />}
      {scr === "upload"     && <Upload go={setScr} user={user} setSel={setSel} />}
      {scr === "profile"    && user && <Profile user={user} />}
      {scr === "leaderboard"&& <Leaderboard />}
      {scr === "share"      && user && <Share user={user} />}
      {scr !== "onboarding" && scr !== "auth" && <Nav active={scr} go={setScr} />}
    </div>
  );
}
