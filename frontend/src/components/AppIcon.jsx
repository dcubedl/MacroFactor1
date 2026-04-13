import { LOGO_IMAGE } from '../data/ranks';

const AppIcon = ({ size = 40 }) => (
  <div style={{
    width: size,
    height: size,
    borderRadius: size * 0.22,
    background: "linear-gradient(145deg, #0E0E14, #141420)",
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
    border: "1px solid rgba(255,23,68,0.15)",
    boxShadow: "0 4px 20px rgba(0,0,0,0.4), 0 0 20px rgba(255,23,68,0.1)",
    overflow: "hidden",
  }}>
    <img
      src={LOGO_IMAGE}
      alt="MacroRanked"
      style={{ width: size * 0.9, height: size * 0.9, objectFit: "contain", mixBlendMode: "screen" }}
    />
  </div>
);

export default AppIcon;
