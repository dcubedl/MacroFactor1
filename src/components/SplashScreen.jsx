import { useState, useEffect } from "react";
import { LOGO_IMAGE } from "../data/ranks";

/*  ── MacroRanked Splash Screen ──────────────────────────────
 *  Drop this file into  src/components/SplashScreen.jsx
 *
 *  Usage in App.jsx (inside the onboarding splash):
 *    import SplashScreen from "./components/SplashScreen";
 *    ...
 *    {scr === "onboarding" && step === 0 && <SplashScreen onStart={() => setStep(1)} />}
 *
 *  No extra dependencies — uses only React + CSS keyframes.
 *  ──────────────────────────────────────────────────────────── */

// ── Keyframe injection (runs once) ──────────────────────────
const STYLE_ID = "mr-splash-keyframes";
function injectKeyframes() {
  if (document.getElementById(STYLE_ID)) return;
  const style = document.createElement("style");
  style.id = STYLE_ID;
  style.textContent = `
    @keyframes mrFloat {
      0%, 100% { transform: translateY(0px); }
      50%      { transform: translateY(15px); }
    }
    @keyframes mrShieldFloat {
      0%, 100% { transform: translateY(0px) scale(1); }
      50%      { transform: translateY(-8px) scale(1.02); }
    }
    @keyframes mrDrift {
      0%   { transform: translate(0, 0) rotate(var(--r)); opacity: var(--o); }
      50%  { transform: translate(var(--dx), var(--dy)) rotate(calc(var(--r) + 4deg)); opacity: calc(var(--o) * 1.3); }
      100% { transform: translate(0, 0) rotate(var(--r)); opacity: var(--o); }
    }
    @keyframes mrParticleRise {
      0%   { transform: translateY(0) translateX(0); opacity: 0; }
      15%  { opacity: var(--po); }
      85%  { opacity: var(--po); }
      100% { transform: translateY(-120px) translateX(var(--px)); opacity: 0; }
    }
    @keyframes mrFadeUp {
      0%   { opacity: 0; transform: translateY(24px); }
      100% { opacity: 1; transform: translateY(0); }
    }
    @keyframes mrGlowPulse {
      0%, 100% { opacity: 0.5; transform: scale(1); }
      50%      { opacity: 0.8; transform: scale(1.05); }
    }
    @keyframes mrButtonPulse {
      0%, 100% { box-shadow: 0 0 25px rgba(255,23,68,0.35); }
      50%      { box-shadow: 0 0 40px rgba(255,23,68,0.55); }
    }
    @keyframes mrDotPop {
      0%   { transform: scale(0); opacity: 0; }
      60%  { transform: scale(1.3); }
      100% { transform: scale(1); opacity: 1; }
    }
  `;
  document.head.appendChild(style);
}

// ── Floating oval shape ─────────────────────────────────────
function FloatingShape({ color, width, height, top, left, right, bottom, rotate, delay, blur }) {
  return (
    <div
      style={{
        position: "absolute",
        top, left, right, bottom,
        width, height,
        "--r": `${rotate}deg`,
        "--dx": `${Math.random() > 0.5 ? 8 : -8}px`,
        "--dy": `${Math.random() > 0.5 ? 12 : -10}px`,
        "--o": "1",
        animation: `mrDrift ${14 + Math.random() * 8}s ease-in-out infinite`,
        animationDelay: `${delay}s`,
        opacity: 0,
        animationFillMode: "both",
      }}
    >
      <div
        style={{
          width: "100%",
          height: "100%",
          borderRadius: "50%",
          background: `radial-gradient(ellipse at 50% 50%, ${color}, transparent 70%)`,
          filter: `blur(${blur || 2}px)`,
          border: "1.5px solid rgba(255,255,255,0.08)",
          boxShadow: `0 8px 32px 0 ${color.replace(")", ",0.15)").replace("rgba", "rgba").replace("rgb", "rgba")}`,
          animation: `mrFloat ${10 + Math.random() * 6}s ease-in-out infinite`,
          animationDelay: `${delay + 0.5}s`,
        }}
      />
    </div>
  );
}

// ── Particle dot ────────────────────────────────────────────
function Particle({ left, delay, duration, opacity, drift }) {
  return (
    <div
      style={{
        position: "absolute",
        bottom: "10%",
        left,
        width: 3,
        height: 3,
        borderRadius: "50%",
        background: "rgba(255,255,255,0.6)",
        "--po": String(opacity),
        "--px": `${drift}px`,
        animation: `mrParticleRise ${duration}s ease-in-out infinite`,
        animationDelay: `${delay}s`,
        opacity: 0,
      }}
    />
  );
}


// ── Rank colour dots ────────────────────────────────────────
const RANK_COLORS = ["#CD7F32", "#C0C0C0", "#FFD700", "#00E5FF", "#B388FF", "#FF1744"];

// ── Main splash component ───────────────────────────────────
export default function SplashScreen({ onStart }) {
  const [visible, setVisible] = useState(false);

  useEffect(() => {
    injectKeyframes();
    // Small delay so the animations feel intentional
    const t = setTimeout(() => setVisible(true), 100);
    return () => clearTimeout(t);
  }, []);

  const fadeUp = (delay) => ({
    opacity: visible ? 1 : 0,
    transform: visible ? "translateY(0)" : "translateY(24px)",
    transition: `opacity 0.9s cubic-bezier(0.22,1.2,0.36,1) ${delay}s, transform 0.9s cubic-bezier(0.22,1.2,0.36,1) ${delay}s`,
  });

  return (
    <div
      style={{
        position: "fixed",
        inset: 0,
        background: "#0A0A0F",
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        flexDirection: "column",
        overflow: "hidden",
        zIndex: 100,
        fontFamily: "'Outfit', sans-serif",
      }}
    >
      {/* ── Background gradient wash ── */}
      <div
        style={{
          position: "absolute",
          inset: 0,
          background: "radial-gradient(ellipse at 60% 30%, rgba(255,23,68,0.06) 0%, transparent 60%), radial-gradient(ellipse at 20% 80%, rgba(179,136,255,0.05) 0%, transparent 55%)",
          pointerEvents: "none",
        }}
      />

      {/* ── Floating shapes ── */}
      <FloatingShape color="rgba(255,23,68,0.12)"  width={420} height={110} top="12%"  left="-8%"              rotate={12}  delay={0.3} blur={3} />
      <FloatingShape color="rgba(179,136,255,0.10)" width={340} height={90}  top="72%"  right="-4%" left={undefined} rotate={-15} delay={0.6} blur={3} />
      <FloatingShape color="rgba(0,229,255,0.09)"   width={220} height={60}  bottom="8%" left="6%"              rotate={-8}  delay={0.5} blur={2} />
      <FloatingShape color="rgba(255,215,0,0.08)"   width={160} height={45}  top="8%"   right="12%" left={undefined} rotate={20}  delay={0.8} blur={2} />
      <FloatingShape color="rgba(205,127,50,0.08)"  width={120} height={35}  top="4%"   left="18%"             rotate={-22} delay={1.0} blur={2} />

      {/* ── Particles ── */}
      <Particle left="15%" delay={0}   duration={18} opacity={0.25} drift={6}  />
      <Particle left="35%" delay={3}   duration={22} opacity={0.18} drift={-8} />
      <Particle left="55%" delay={1.5} duration={16} opacity={0.22} drift={4}  />
      <Particle left="75%" delay={4}   duration={20} opacity={0.15} drift={-5} />
      <Particle left="88%" delay={2.5} duration={24} opacity={0.2}  drift={7}  />

      {/* ── Edge fade overlay ── */}
      <div
        style={{
          position: "absolute",
          inset: 0,
          background: "linear-gradient(to bottom, rgba(10,10,15,0.7) 0%, transparent 20%, transparent 80%, rgba(10,10,15,0.8) 100%)",
          pointerEvents: "none",
        }}
      />

      {/* ── Content ── */}
      <div style={{ position: "relative", zIndex: 10, display: "flex", flexDirection: "column", alignItems: "center", gap: 0, padding: "0 24px", textAlign: "center" }}>

        {/* Beta badge */}
        <div style={{
          ...fadeUp(0.3),
          display: "inline-flex",
          alignItems: "center",
          gap: 6,
          padding: "4px 12px",
          borderRadius: 20,
          background: "rgba(255,23,68,0.08)",
          border: "1px solid rgba(255,23,68,0.25)",
          marginBottom: 20,
        }}>
          <div style={{ width: 6, height: 6, borderRadius: "50%", background: "#FF1744" }} />
          <span style={{ fontSize: 11, fontFamily: "'JetBrains Mono', monospace", color: "rgba(255,23,68,0.8)", letterSpacing: 1.5, fontWeight: 600, textTransform: "uppercase" }}>
            Beta v0.1
          </span>
        </div>

        {/* Shield logo with glow */}
        <div style={{
          ...fadeUp(0.5),
          position: "relative",
          marginBottom: 16,
        }}>
          {/* Glow behind shield */}
          <div style={{
            position: "absolute",
            top: "50%",
            left: "50%",
            transform: "translate(-50%, -50%)",
            width: 200,
            height: 200,
            borderRadius: "50%",
            background: "radial-gradient(circle, rgba(255,23,68,0.2) 0%, transparent 70%)",
            animation: "mrGlowPulse 3s ease-in-out infinite",
          }} />
          <div style={{ animation: "mrShieldFloat 3.5s ease-in-out infinite" }}>
            <img src={LOGO_IMAGE} alt="MacroRanked" style={{ width: 120, height: "auto", objectFit: "contain", mixBlendMode: "screen" }} />
          </div>
        </div>

        {/* Title */}
        <h1 style={{
          ...fadeUp(0.7),
          fontSize: 38,
          fontWeight: 900,
          letterSpacing: -0.5,
          margin: 0,
          lineHeight: 1.1,
        }}>
          <span style={{ color: "#F0F0F5" }}>Macro</span>
          <span style={{ color: "#FF1744" }}>Ranked</span>
        </h1>

        {/* Tagline */}
        <p style={{
          ...fadeUp(0.9),
          color: "#8888A0",
          fontSize: 15,
          fontWeight: 300,
          lineHeight: 1.6,
          margin: "14px 0 0 0",
          maxWidth: 260,
        }}>
          Track your meals. Earn your rank.<br />Compete with friends.
        </p>

        {/* Rank dots */}
        <div style={{
          ...fadeUp(1.1),
          display: "flex",
          gap: 8,
          marginTop: 18,
        }}>
          {RANK_COLORS.map((c, i) => (
            <div
              key={c}
              style={{
                width: 8,
                height: 8,
                borderRadius: "50%",
                background: c,
                boxShadow: `0 0 8px ${c}55`,
                animation: visible ? `mrDotPop 0.4s cubic-bezier(0.22,1.2,0.36,1) ${1.2 + i * 0.08}s both` : "none",
              }}
            />
          ))}
        </div>

        {/* Get Started button */}
        <button
          onClick={onStart}
          style={{
            ...fadeUp(1.4),
            marginTop: 36,
            width: "100%",
            maxWidth: 320,
            padding: "16px 0",
            borderRadius: 14,
            border: "none",
            background: "#FF1744",
            color: "#fff",
            fontSize: 16,
            fontWeight: 700,
            fontFamily: "'Outfit', sans-serif",
            cursor: "pointer",
            animation: visible ? "mrButtonPulse 2.5s ease-in-out infinite 2s" : "none",
            transition: "transform 0.15s cubic-bezier(0.22,1.2,0.36,1)",
          }}
          onMouseDown={(e) => (e.currentTarget.style.transform = "scale(0.96)")}
          onMouseUp={(e) => (e.currentTarget.style.transform = "scale(1)")}
          onTouchStart={(e) => (e.currentTarget.style.transform = "scale(0.96)")}
          onTouchEnd={(e) => (e.currentTarget.style.transform = "scale(1)")}
        >
          Get Started
        </button>
      </div>
    </div>
  );
}
