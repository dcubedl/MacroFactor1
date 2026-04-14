import { getRank, RANK_IMAGES } from '../data/ranks';

const RankBadge = ({ rank, size = "md", animated = false, showLabel = true }) => {
  const r = typeof rank === "string" ? getRank(rank === "Bronze" ? 0 : rank === "Silver" ? 40 : rank === "Gold" ? 55 : rank === "Platinum" ? 70 : rank === "Diamond" ? 80 : 90) : getRank(rank);
  const s = { xs: 44, sm: 56, md: 76, lg: 100, xl: 160 }[size] || 76;
  const img = RANK_IMAGES[r.name];

  return (
    <div style={{ display: "inline-flex", flexDirection: "column", alignItems: "center", gap: 3 }}>
      <div style={{
        animation: animated ? "gp 2.5s ease infinite" : "none",
        "--gc": r.glow,
      }}>
        <img
          src={img}
          alt={r.name}
          style={{
            width: s,
            height: s,
            objectFit: "contain",
            filter: animated ? `drop-shadow(0 0 ${s * 0.2}px ${r.glow})` : "none",
            mixBlendMode: "screen",
          }}
        />
      </div>
      {showLabel && (
        <span style={{
          fontSize: Math.max(8, s * 0.17),
          fontWeight: 700,
          color: r.color,
          letterSpacing: ".06em",
          textTransform: "uppercase",
          fontFamily: "var(--fm)",
        }}>
          {r.name}
        </span>
      )}
    </div>
  );
};

export default RankBadge;
