export const MOCK_MEALS = [
  { id: 1, name: "Grilled Chicken & Rice Bowl", foods: ["Chicken Breast 200g", "Basmati Rice 150g", "Broccoli 100g", "Olive Oil 10ml"], photo: "🍗", cal: 620, protein: 52, carbs: 68, fat: 14, score: 88, time: "12:30 PM" },
  { id: 2, name: "Salmon & Sweet Potato", foods: ["Atlantic Salmon 180g", "Sweet Potato 200g", "Asparagus 80g", "Lemon Butter 5g"], photo: "🐟", cal: 580, protein: 44, carbs: 52, fat: 18, score: 82, time: "7:15 PM" },
  { id: 3, name: "Overnight Oats & Berries", foods: ["Rolled Oats 80g", "Greek Yogurt 150g", "Blueberries 60g", "Honey 15g", "Chia Seeds 10g"], photo: "🥣", cal: 440, protein: 28, carbs: 62, fat: 10, score: 74, time: "8:00 AM" },
  { id: 4, name: "Steak & Eggs Breakfast", foods: ["Sirloin Steak 150g", "Eggs x3", "Sourdough Toast 2 slices", "Avocado 50g"], photo: "🥩", cal: 710, protein: 58, carbs: 34, fat: 36, score: 67, time: "9:30 AM" },
  { id: 5, name: "Protein Shake & Banana", foods: ["Whey Protein 30g", "Banana 1 medium", "Almond Milk 250ml", "Peanut Butter 15g"], photo: "🥤", cal: 380, protein: 36, carbs: 38, fat: 12, score: 71, time: "3:00 PM" },
];

export const MOCK_LEADERBOARD = [
  { username: "rxnaldo_", rank: "Crimson", score: 94, streak: 42, avatar: "😤" },
  { username: "macr0king", rank: "Crimson", score: 92, streak: 38, avatar: "👑" },
  { username: "fuelqueen", rank: "Diamond", score: 87, streak: 31, avatar: "💅" },
  { username: "dom_mr", rank: "Diamond", score: 85, streak: 27, avatar: "🔥" },
  { username: "lifteatrepeat", rank: "Platinum", score: 78, streak: 22, avatar: "💪" },
  { username: "carbsnotcardio", rank: "Platinum", score: 76, streak: 19, avatar: "🍝" },
  { username: "prtnqueen", rank: "Gold", score: 68, streak: 15, avatar: "✨" },
  { username: "bulkszn", rank: "Gold", score: 64, streak: 12, avatar: "🏋️" },
  { username: "mealprepmonday", rank: "Silver", score: 52, streak: 8, avatar: "📦" },
  { username: "newbie_gains", rank: "Bronze", score: 35, streak: 3, avatar: "🌱" },
];

export const UPLOAD_DETECT_FOODS = [
  { name: "Chicken Breast", amount: "200g", cal: 330, protein: 62, carbs: 0, fat: 7, confidence: 96 },
  { name: "Jasmine Rice", amount: "180g", cal: 234, protein: 4, carbs: 52, fat: 0.4, confidence: 93 },
  { name: "Broccoli", amount: "120g", cal: 41, protein: 3.4, carbs: 8, fat: 0.4, confidence: 91 },
  { name: "Olive Oil Drizzle", amount: "10ml", cal: 88, protein: 0, carbs: 0, fat: 10, confidence: 85 },
];
