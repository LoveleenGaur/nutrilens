"""
Groq API client for food image analysis using Llama 4 Scout vision model.
"""

import json
from groq import Groq


SYSTEM_PROMPT = """You are a professional nutritionist AI. Analyze the food image provided and return ONLY a valid JSON object (no markdown fences, no explanation, no preamble).

Return this exact structure:
{
    "foods": [
        {
            "name": "Food item name",
            "emoji": "relevant emoji",
            "portion": "estimated portion description",
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
    "notes": "One brief health tip about this meal"
}

Rules:
- Identify ALL visible food items in the image
- Estimate portions based on visual cues (plate size, utensil comparison, etc.)
- Be realistic with calorie estimates — use USDA-standard values where possible
- Include 3-6 key micronutrients (vitamins, minerals, fiber)
- If you cannot identify food in the image, return: {"error": "Could not identify food items in this image."}
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
