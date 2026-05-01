"""Rule-based AI chat assistant for farm advice."""
import re
from typing import List, Tuple


KNOWLEDGE_BASE: List[Tuple[List[str], str, List[str]]] = [
    (
        ["feed", "feeding", "what to feed", "diet", "nutrition"],
        "For optimal poultry nutrition, layers (18-20 weeks+) should get 16-18% protein layer mash with calcium-rich supplements like oyster shell. "
        "Broilers need 22-24% protein starter (0-3 weeks), then 18-20% finisher (3-6 weeks). Provide clean fresh water at all times — birds drink "
        "roughly twice the weight of feed they eat. Feed twice a day at consistent times to reduce stress.",
        ["How much feed per bird?", "What about chicks?", "Best layer feed?"],
    ),
    (
        ["chick", "starter", "young", "day old"],
        "Day-old chicks need a brooder kept at 32-35°C in week 1, decreased by 2-3°C each week until matching ambient temperature around week 5. "
        "Use 24-hour lighting initially. Provide chick starter feed (20-22% protein) free-choice and clean water with vitamins for the first 7 days.",
        ["Brooder setup tips?", "First-week vaccinations?"],
    ),
    (
        ["broiler", "meat bird"],
        "Broilers reach market weight (~2 kg) in 6-8 weeks. Maintain a feed conversion ratio (FCR) of around 1.7-1.9. "
        "Provide 23 hours of light, ad-libitum feeding, and good ventilation. Watch for ascites (heart failure) and leg problems from rapid growth.",
        ["Broiler vaccination schedule?", "Reduce FCR?"],
    ),
    (
        ["disease", "sick", "illness", "ill", "infection"],
        "Common poultry diseases include Newcastle, Marek's, Infectious Bronchitis, Coccidiosis, and Avian Influenza. "
        "Watch for: drop in egg production, ruffled feathers, droopy birds, abnormal droppings, respiratory sounds, or sudden deaths. "
        "Isolate sick birds immediately, disinfect houses, and contact a veterinarian for diagnosis before medicating.",
        ["Newcastle symptoms?", "Coccidiosis treatment?", "Vaccination schedule?"],
    ),
    (
        ["newcastle", "ranikhet"],
        "Newcastle disease causes respiratory distress, twisted necks, paralysis, and high mortality. There is no cure — only prevention. "
        "Vaccinate at day 7 (LaSota), week 4 (LaSota booster), and every 3 months for layers. Quarantine new birds for 30 days before introduction.",
        ["Other vaccines?", "How does it spread?"],
    ),
    (
        ["coccidiosis", "bloody droppings"],
        "Coccidiosis causes bloody droppings, weakness, and weight loss in birds 3-8 weeks old. Treat with Amprolium or Toltrazuril in drinking water "
        "for 5-7 days. Prevention: keep litter dry, avoid overcrowding, use coccidiostat in starter feed, and rotate medications.",
        ["Litter management?", "Preventive feed?"],
    ),
    (
        ["vaccine", "vaccination", "vaccinate"],
        "Standard layer vaccination program: Day 1 - Marek's; Day 7 - Newcastle (LaSota) + IB; Day 14 - Gumboro; Day 21 - Gumboro booster; "
        "Day 28 - Newcastle (LaSota) booster; Week 8 - Fowl Pox; Week 16 - Newcastle + IB + EDS killed. Consult your local vet to adapt to regional risks.",
        ["Broiler schedule?", "Storage of vaccines?"],
    ),
    (
        ["egg production", "low eggs", "egg drop", "laying"],
        "Drops in egg production can be caused by: stress, poor lighting (need 14-16h), low protein/calcium, disease (IB, EDS, Newcastle), "
        "old hens (>72 weeks), parasites (mites/lice), or extreme temperatures. Check feed quality first, then disease, then lighting.",
        ["Improve egg size?", "Light schedule?", "Calcium sources?"],
    ),
    (
        ["light", "lighting", "lamp"],
        "Layers need 14-16 hours of light per day for peak production. Use 3-4 watts per square meter. Increase light gradually after 18 weeks "
        "(15 minutes per week) until reaching 16 hours. Never decrease light during lay — it triggers molting.",
        ["When to start lighting?", "Light intensity?"],
    ),
    (
        ["water", "drinking"],
        "Birds need 2x the weight of their feed in water. A laying hen drinks 200-300 ml/day. Water must be clean, cool (10-15°C ideal), "
        "and available 24/7. Sanitize drinkers daily with chlorine (3-5 ppm) and check pH (6.5-7.5).",
        ["Water medication tips?"],
    ),
    (
        ["temperature", "heat", "cold", "ventilation"],
        "Adult birds thrive at 18-24°C. Above 30°C they suffer heat stress: panting, wings spread, drop in production. "
        "Provide good ventilation, cool water with electrolytes, shade, and avoid handling during hot hours. Below 10°C, increase feed and reduce drafts.",
        ["Heat stress signs?", "Cooling tips?"],
    ),
    (
        ["mortality", "death", "dying"],
        "Investigate any mortality above 0.5%/week. Common causes: disease (Newcastle, Gumboro, Coccidiosis), heat stress, predators, "
        "poor ventilation, bad feed, or poisoning. Perform post-mortem on dead birds. Always remove carcasses immediately and disinfect.",
        ["Post-mortem how-to?", "Disinfectants?"],
    ),
    (
        ["biosecurity", "hygiene", "clean"],
        "Biosecurity essentials: 1) Foot dip with disinfectant at every entry, 2) Restrict visitors, 3) Quarantine new birds 30 days, "
        "4) Control rodents and wild birds, 5) Disinfect equipment between batches, 6) All-in/all-out flock management, 7) Dispose of dead birds properly.",
        ["Disinfectant types?", "Rodent control?"],
    ),
    (
        ["profit", "money", "income", "sell"],
        "Maximize profit by: 1) Reducing feed cost (it's 60-70% of expenses) through quality feed and lower FCR; 2) Direct-to-consumer egg sales; "
        "3) Value-added products (organic, free-range); 4) Selling spent layers; 5) Composting manure for sale; 6) Tracking every expense.",
        ["Reduce feed cost?", "Direct sales?"],
    ),
    (
        ["hello", "hi", "hey", "good morning", "good evening"],
        "Hello! I'm your poultry farm assistant. Ask me about feeding, diseases, vaccinations, egg production, biosecurity, or farm management.",
        ["What should I feed layers?", "Vaccination schedule?", "Improve egg production?"],
    ),
    (
        ["thank", "thanks"],
        "You're welcome! Always happy to help with your farm operations.",
        ["Other tips?", "Common diseases?"],
    ),
]


DEFAULT_SUGGESTIONS = [
    "How do I improve egg production?",
    "What is the layer vaccination schedule?",
    "Common poultry diseases?",
    "How much feed per bird per day?",
]


class ChatbotService:
    @staticmethod
    def respond(message: str) -> dict:
        msg = message.lower().strip()
        if not msg:
            return {
                "response": "Please ask me a question about your poultry farm.",
                "suggestions": DEFAULT_SUGGESTIONS,
            }

        best_match = None
        best_score = 0
        for keywords, response, suggestions in KNOWLEDGE_BASE:
            score = sum(1 for kw in keywords if kw in msg)
            # Boost for exact word match
            for kw in keywords:
                if re.search(rf"\b{re.escape(kw)}\b", msg):
                    score += 1
            if score > best_score:
                best_score = score
                best_match = (response, suggestions)

        if best_match and best_score > 0:
            return {"response": best_match[0], "suggestions": best_match[1]}

        return {
            "response": "I'm not sure about that specific topic, but I can help with feeding, diseases, vaccinations, "
                        "egg production, biosecurity, lighting, water management, and farm profitability. "
                        "Try rephrasing your question.",
            "suggestions": DEFAULT_SUGGESTIONS,
        }
