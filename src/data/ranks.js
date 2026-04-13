// Import your PNG rank badge images here
// Drop your PNGs into src/assets/ranks/ and uncomment the imports below

import bronzeImg from '../assets/ranks/bronze.png';
import silverImg from '../assets/ranks/silver.png';
import goldImg from '../assets/ranks/gold.png';
import platinumImg from '../assets/ranks/platinum.png';
import diamondImg from '../assets/ranks/diamond.png';
import crimsonImg from '../assets/ranks/crimson.png';
import logoImg from '../assets/brand/logo-main.png';

export const RANK_IMAGES = {
  Bronze: bronzeImg,
  Silver: silverImg,
  Gold: goldImg,
  Platinum: platinumImg,
  Diamond: diamondImg,
  Crimson: crimsonImg,
};

export const LOGO_IMAGE = logoImg;

export const RANKS = [
  { name: "Bronze", min: 0, color: "#CD7F32", glow: "rgba(205,127,50,0.4)", bg: "linear-gradient(135deg,#CD7F32,#8B5E3C)" },
  { name: "Silver", min: 40, color: "#C0C0C0", glow: "rgba(192,192,192,0.4)", bg: "linear-gradient(135deg,#C0C0C0,#808080)" },
  { name: "Gold", min: 55, color: "#FFD700", glow: "rgba(255,215,0,0.4)", bg: "linear-gradient(135deg,#FFD700,#B8860B)" },
  { name: "Platinum", min: 70, color: "#00E5FF", glow: "rgba(0,229,255,0.4)", bg: "linear-gradient(135deg,#00E5FF,#0091EA)" },
  { name: "Diamond", min: 80, color: "#B388FF", glow: "rgba(179,136,255,0.45)", bg: "linear-gradient(135deg,#B388FF,#7C4DFF)" },
  { name: "Crimson", min: 90, color: "#FF1744", glow: "rgba(255,23,68,0.5)", bg: "linear-gradient(135deg,#FF1744,#D50000)" },
];

export const getRank = (score) => [...RANKS].reverse().find(r => score >= r.min) || RANKS[0];
