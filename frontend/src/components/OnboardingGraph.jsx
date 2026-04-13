import { useState, useEffect } from "react";

/*  ── MacroRanked Onboarding Graph ───────────────────────────
 *  Drop this file into  src/components/OnboardingGraph.jsx
 *
 *  Usage in onboarding (as a step between training frequency and social):
 *    import OnboardingGraph from "./components/OnboardingGraph";
 *    ...
 *    <OnboardingGraph onContinue={() => nextStep()} />
 *
 *  No extra dependencies — pure React + inline SVG + CSS keyframes.
 *  ──────────────────────────────────────────────────────────── */

const STYLE_ID = "mr-graph-keyframes";
function injectKeyframes() {
  if (document.getElementById(STYLE_ID)) return;
  const style = document.createElement("style");
  style.id = STYLE_ID;
  style.textContent = `
    @keyframes mrDrawLine {
      0%   { stroke-dashoffset: 600; }
      100% { stroke-dashoffset: 0; }
    }
    @keyframes mrFillFade {
      0%   { opacity: 0; }
      100% { opacity: 1; }
    }
    @keyframes mrLabelPop {
      0%   { opacity: 0; transform: translateY(8px); }
      100% { opacity: 1; transform: translateY(0); }
    }
    @keyframes mrDotPulse {
      0%, 100% { r: 5; opacity: 1; }
      50%      { r: 7; opacity: 0.8; }
    }
    @keyframes mrStatCount {
      0%   { opacity: 0; transform: scale(0.8); }
      100% { opacity: 1; transform: scale(1); }
    }
  `;
  document.head.appendChild(style);
}

export default function OnboardingGraph({ onContinue }) {
  const [visible, setVisible] = useState(false);

  useEffect(() => {
    injectKeyframes();
    const t = setTimeout(() => setVisible(true), 200);
    return () => clearTimeout(t);
  }, []);

  // Graph dimensions
  const W = 320;
  const H = 200;
  const baseY = 170; // bottom baseline for area fills

  // Both lines start from the same point, then diverge
  const startX = 0;
  const startY = 118;

  // Green: starts flat, then sweeps upward in a flowing S-curve (Cal AI style)
  const greenEndX = 320;
  const greenEndY = 28;
  const greenLine = `M${startX},${startY} C88,116 195,58 ${greenEndX},${greenEndY}`;
  const greenArea = `M${startX},${startY} C88,116 195,58 ${greenEndX},${greenEndY} L${greenEndX},${baseY} L${startX},${baseY} Z`;

  // Red: dips slightly (initial "it's working" bump), small plateau, then curves down
  const redEndX = 320;
  const redEndY = 155;
  const redLine = `M${startX},${startY} C55,104 108,100 168,116 C218,128 268,143 ${redEndX},${redEndY}`;
  const redArea = `M${startX},${startY} C55,104 108,100 168,116 C218,128 268,143 ${redEndX},${redEndY} L${redEndX},${baseY} L${startX},${baseY} Z`;

  const fadeUp = (delay) => ({
    opacity: visible ? 1 : 0,
    transform: visible ? "translateY(0)" : "translateY(24px)",
    transition: `opacity 0.8s cubic-bezier(0.22,1.2,0.36,1) ${delay}s, transform 0.8s cubic-bezier(0.22,1.2,0.36,1) ${delay}s`,
  });

  return (
    <div
      style={{
        minHeight: "100vh",
        background: "#0A0A0F",
        display: "flex",
        flexDirection: "column",
        fontFamily: "'Outfit', sans-serif",
        padding: "0 24px",
        paddingTop: 80,
        paddingBottom: 100,
      }}
    >
      {/* Title */}
      <h1
        style={{
          ...fadeUp(0.1),
          fontSize: 28,
          fontWeight: 800,
          color: "#F0F0F5",
          margin: 0,
          lineHeight: 1.2,
        }}
      >
        Tracking macros<br />
        <span style={{ color: "#FF1744" }}>changes everything</span>
      </h1>

      {/* Subtitle */}
      <p
        style={{
          ...fadeUp(0.25),
          color: "#8888A0",
          fontSize: 14,
          fontWeight: 400,
          margin: "12px 0 0 0",
          lineHeight: 1.5,
        }}
      >
        People who track their macros consistently see better results and keep them long-term.
      </p>

      {/* Graph card */}
      <div
        style={{
          ...fadeUp(0.4),
          background: "#13131C",
          borderRadius: 16,
          border: "1px solid rgba(255,255,255,0.06)",
          padding: "24px 20px 16px 20px",
          marginTop: 32,
        }}
      >
        {/* Legend */}
        <div style={{ display: "flex", gap: 20, marginBottom: 16 }}>
          <div style={{ display: "flex", alignItems: "center", gap: 6 }}>
            <div style={{ width: 10, height: 3, borderRadius: 2, background: "#00E676" }} />
            <span style={{ fontSize: 12, color: "#00E676", fontFamily: "'JetBrains Mono', monospace", fontWeight: 600 }}>
              Tracks macros
            </span>
          </div>
          <div style={{ display: "flex", alignItems: "center", gap: 6 }}>
            <div style={{ width: 10, height: 3, borderRadius: 2, background: "#FF5252" }} />
            <span style={{ fontSize: 12, color: "#FF5252", fontFamily: "'JetBrains Mono', monospace", fontWeight: 600 }}>
              Doesn't track
            </span>
          </div>
        </div>

        {/* SVG Chart */}
        <svg
          viewBox={`0 0 ${W} ${H}`}
          width="100%"
          style={{ overflow: "visible" }}
        >
          <defs>
            <linearGradient id="greenGrad" x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stopColor="#00E676" stopOpacity={0.18} />
              <stop offset="100%" stopColor="#00E676" stopOpacity={0} />
            </linearGradient>
            <linearGradient id="redGrad" x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stopColor="#FF5252" stopOpacity={0.12} />
              <stop offset="100%" stopColor="#FF5252" stopOpacity={0} />
            </linearGradient>
          </defs>

          {/* Horizontal grid lines */}
          {[0.25, 0.5, 0.75].map((pct, i) => {
            const y = 20 + 150 * (1 - pct);
            return (
              <line key={i} x1={0} y1={y} x2={W} y2={y} stroke="rgba(255,255,255,0.04)" strokeWidth={1} />
            );
          })}

          {/* Area fills */}
          <path d={greenArea} fill="url(#greenGrad)" style={{ animation: visible ? "mrFillFade 2s ease 6.5s both" : "none", opacity: 0 }} />
          <path d={redArea} fill="url(#redGrad)" style={{ animation: visible ? "mrFillFade 2s ease 6.6s both" : "none", opacity: 0 }} />

          {/* Green line — curves upward */}
          <path
            d={greenLine}
            fill="none"
            stroke="#00E676"
            strokeWidth={3}
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeDasharray={700}
            strokeDashoffset={visible ? 0 : 700}
            style={{ transition: "stroke-dashoffset 6s linear 0.6s" }}
          />

          {/* Red line — dips, bumps, falls */}
          <path
            d={redLine}
            fill="none"
            stroke="#FF5252"
            strokeWidth={3}
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeDasharray={700}
            strokeDashoffset={visible ? 0 : 700}
            style={{ transition: "stroke-dashoffset 6s linear 0.6s" }}
          />

          {/* Shared start dot (hollow) */}
          <circle
            cx={startX}
            cy={startY}
            r={5}
            fill="none"
            stroke="#888899"
            strokeWidth={2}
            style={{ opacity: visible ? 1 : 0, transition: "opacity 0.3s ease 0.6s" }}
          />

          {/* End dots */}
          <circle
            cx={greenEndX}
            cy={greenEndY}
            r={5}
            fill="#00E676"
            style={{
              animation: visible ? "mrDotPulse 2s ease-in-out infinite 6.7s" : "none",
              opacity: visible ? 1 : 0,
              transition: "opacity 0.3s ease 6.7s",
            }}
          />
          <circle
            cx={redEndX}
            cy={redEndY}
            r={5}
            fill="#FF5252"
            style={{
              animation: visible ? "mrDotPulse 2s ease-in-out infinite 6.7s" : "none",
              opacity: visible ? 1 : 0,
              transition: "opacity 0.3s ease 6.7s",
            }}
          />

          {/* End labels */}
          <text
            x={greenEndX - 10}
            y={greenEndY - 11}
            fill="#00E676"
            fontSize={11}
            fontFamily="'JetBrains Mono', monospace"
            fontWeight={700}
            textAnchor="end"
            style={{ animation: visible ? "mrLabelPop 0.5s ease 6.8s both" : "none" }}
          >
            MacroRanked
          </text>
          <text
            x={redEndX - 10}
            y={redEndY + 18}
            fill="#FF5252"
            fontSize={11}
            fontFamily="'JetBrains Mono', monospace"
            fontWeight={700}
            textAnchor="end"
            style={{ animation: visible ? "mrLabelPop 0.5s ease 6.9s both" : "none" }}
          >
            No tracking
          </text>

          {/* X-axis labels */}
          <text x={startX} y={H - 4} fill="#55556A" fontSize={10} fontFamily="'JetBrains Mono', monospace" textAnchor="start">Month 1</text>
          <text x={W} y={H - 4} fill="#55556A" fontSize={10} fontFamily="'JetBrains Mono', monospace" textAnchor="end">Month 6</text>
        </svg>
      </div>

      {/* Stat callout */}
      <div
        style={{
          ...fadeUp(0.7),
          textAlign: "center",
          marginTop: 24,
          padding: "16px",
          background: "rgba(0,230,118,0.06)",
          borderRadius: 12,
          border: "1px solid rgba(0,230,118,0.12)",
        }}
      >
        <span style={{
          fontSize: 28,
          fontWeight: 900,
          color: "#00E676",
          fontFamily: "'JetBrains Mono', monospace",
          animation: visible ? "mrStatCount 0.6s ease 1.2s both" : "none",
        }}>
          80%
        </span>
        <p style={{ color: "#8888A0", fontSize: 13, margin: "4px 0 0 0", lineHeight: 1.4 }}>
          of MacroRanked users hit their goals<br />within 3 months of consistent tracking
        </p>
      </div>

      {/* Continue button */}
      <button
        onClick={onContinue}
        style={{
          ...fadeUp(0.9),
          marginTop: 32,
          width: "100%",
          padding: "16px 0",
          borderRadius: 14,
          border: "none",
          background: "#FF1744",
          color: "#fff",
          fontSize: 16,
          fontWeight: 700,
          fontFamily: "'Outfit', sans-serif",
          cursor: "pointer",
          boxShadow: "0 0 25px rgba(255,23,68,0.35)",
          transition: "transform 0.15s cubic-bezier(0.22,1.2,0.36,1)",
        }}
        onMouseDown={(e) => (e.currentTarget.style.transform = "scale(0.96)")}
        onMouseUp={(e) => (e.currentTarget.style.transform = "scale(1)")}
        onTouchStart={(e) => (e.currentTarget.style.transform = "scale(0.96)")}
        onTouchEnd={(e) => (e.currentTarget.style.transform = "scale(1)")}
      >
        Continue
      </button>
    </div>
  );
}
