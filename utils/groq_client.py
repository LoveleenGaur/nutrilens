"""
Groq API client for food image analysis using Llama 4 Scout vision model.
"""

import json
from groq import Groq


SYSTEM_PROMPT = """You are a world-class nutritionist AI with deep expertise in global cuisines — Indian, South Asian, Mediterranean, East Asian, Mexican, American, European, African, Middle Eastern, and more. You are especially knowledgeable about vegetarian and vegan foods.

Analyze the food image and return ONLY a valid JSON object (no markdown fences, no explanation, no preamble).

Return this exact structure:
{
    "foods": [
        {
            "name": "Food item name (use the specific common name, e.g. 'Paneer Butter Masala' not just 'curry', 'Masala Dosa' not just 'crepe')",
            "emoji": "relevant emoji",
            "portion": "estimated portion (e.g. '1 katori / 150ml bowl', '2 rotis', '1 cup rice', '1 medium plate')",
            "calories": <number>,
            "protein": <number in grams>,
            "carbs": <number in grams>,
            "fat": <number in grams>
        }
    ],
    "totals": {
        "calories": <number>,
        "protein": <number>,
        "carbs": <number>,
        "fat": <number>
    },
    "micronutrients": [
        {"name": "Nutrient name", "amount": "estimated amount with unit"}
    ],
    "notes": "One brief, specific health tip about this meal"
}

Cuisine Recognition Guide:
- INDIAN: dal (toor, moong, masoor, chana, urad), sabzi, roti/chapati/naan/paratha/puri/bhature, rice/pulao/biryani/jeera rice, paneer dishes, dosa/idli/vada/uttapam, sambar, rasam, chutney (coconut, mint, tamarind), raita, papad, pickle/achaar, curd/dahi, kheer, gulab jamun, ladoo, halwa, barfi, poha, upma, chole, rajma, kadhi, pakora, samosa, kachori, pav bhaji, aloo gobi, baingan bharta, malai kofta, palak paneer, mix veg, thali items
- EAST ASIAN: sushi, ramen, dim sum, stir-fry, tofu, rice bowls, noodles, spring rolls, miso
- MEDITERRANEAN: hummus, falafel, pita, shawarma, tabbouleh, dolma, grilled vegetables
- MEXICAN: tacos, burritos, enchiladas, quesadilla, guacamole, rice & beans
- AMERICAN/EUROPEAN: burgers, pasta, pizza, salads, steaks, sandwiches, soups
- And ALL other global cuisines — be specific with names, never generic

Rules:
- Identify ALL visible food items — list each separately, even small items like pickle, papad, chutney
- For vegetarian protein sources: paneer, dal/lentils, chickpeas, kidney beans, soy, curd/yogurt, nuts, seeds, tofu, tempeh
- Account for cooking oils, ghee, butter, cream in calorie estimates (Indian food often uses generous ghee/oil)
- Use regional portion references where appropriate (katori, roti count, cups)
- Be realistic with calories — don't underestimate fried or oil-rich dishes
- Include 4-6 key micronutrients relevant to the cuisine (iron, calcium, fiber, B12, vitamin C, folate, zinc, vitamin A, potassium)
- If you cannot identify food, return: {"error": "Could not identify food items in this image."}
- Return ONLY the JSON object, nothing else"""


def analyze_food_image(
    api_key: str,
    image_base64: str,
    model: str = "meta-llama/llama-4-scout-17b-16e-instruct",
    meal_name: str = "",
    portion_size: str = "regular",
) -> str:
    """
    Send a food image to Groq's vision model and get nutritional analysis.

    Args:
        api_key: Groq API key
        image_base64: Base64-encoded image string
        model: Groq model ID
        meal_name: Optional name of the meal
        portion_size: small / regular / large

    Returns:
        Raw text response from the model
    """
    client = Groq(api_key=api_key)

    user_text = f"Analyze this meal image. Portion size: {portion_size}."
    if meal_name:
        user_text += f' This meal is called "{meal_name}".'
    user_text += " Return the nutritional breakdown as JSON."

    messages = [
        {
            "role": "system",
            "content": SYSTEM_PROMPT,
        },
        {
            "role": "user",
            "content": [
                {
                    "type": "text",
                    "text": user_text,
                },
                {
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:image/jpeg;base64,{image_base64}",
                    },
                },
            ],
        },
    ]

    completion = client.chat.completions.create(
        model=model,
        messages=messages,
        temperature=0.3,
        max_completion_tokens=1024,
    )

    return completion.choices[0].message.content
