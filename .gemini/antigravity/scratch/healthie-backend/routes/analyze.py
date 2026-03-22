import os, base64, json, re
from flask import Blueprint, request, jsonify
import google.generativeai as genai
from routes.auth import get_current_user

analyze_bp = Blueprint('analyze', __name__)

NUTRITION_PROMPT = """You are a precise nutritionist and food scientist. Analyze this food image using computer vision.

CRITICAL INSTRUCTIONS:
- Look at the ACTUAL food/product in the image
- Read any visible labels, packaging, or text on the food
- Do NOT guess or use a generic name — identify the exact item shown
- If it is a packaged product, use its exact brand and product name
- Estimate nutritional values based on typical serving size visible in the image

Return ONLY a valid JSON object. No markdown. No explanation. No code blocks. Just raw JSON:
{
  "food_name": "exact name of what you see (e.g. Britannia Cake Gobbles, not Grilled Salmon Bowl)",
  "confidence": "high|medium|low",
  "serving_note": "brief note on serving size assumed",
  "nutrition": {
    "calories": number,
    "protein_g": number,
    "carbs_g": number,
    "fats_g": number,
    "fiber_g": number,
    "sugar_g": number,
    "sodium_mg": number
  },
  "commentary": {
    "immediate_health_impact": "2-3 sentences about what this food does to your body immediately after eating",
    "dietary_fit": "2-3 sentences about how this fits into a balanced diet, who it suits, who should limit it",
    "pro_tips": "2-3 specific actionable tips to make this meal healthier or pair it better"
  }
}"""

@analyze_bp.route('/analyze', methods=['POST'])
def analyze_image():
    user = get_current_user()
    if not user:
        return jsonify({'error': 'Unauthorized'}), 401

    api_key = os.environ.get('GEMINI_API_KEY')
    if not api_key:
        return jsonify({'error': 'Gemini API key not configured'}), 500

    if 'image' not in request.files and 'image_data' not in request.json:
        return jsonify({'error': 'No image provided'}), 400

    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-3-flash-preview')

        if 'image' in request.files:
            img_file = request.files['image']
            img_bytes = img_file.read()
            mime_type = img_file.content_type or 'image/jpeg'
        else:
            data_url = request.json.get('image_data', '')
            header, encoded = data_url.split(',', 1)
            mime_type = header.split(';')[0].split(':')[1]
            img_bytes = base64.b64decode(encoded)

        import PIL.Image
        import io
        pil_image = PIL.Image.open(io.BytesIO(img_bytes))

        response = model.generate_content([NUTRITION_PROMPT, pil_image])
        raw_text = response.text.strip()

        # Strip markdown code fences if present
        raw_text = re.sub(r'^```(?:json)?\s*', '', raw_text)
        raw_text = re.sub(r'\s*```$', '', raw_text)
        raw_text = raw_text.strip()

        result = json.loads(raw_text)

        # Validate required fields
        required = ['food_name', 'nutrition', 'commentary']
        for field in required:
            if field not in result:
                raise ValueError(f"Missing field: {field}")

        nutrition_keys = ['calories', 'protein_g', 'carbs_g', 'fats_g', 'fiber_g', 'sugar_g', 'sodium_mg']
        for key in nutrition_keys:
            if key not in result['nutrition']:
                result['nutrition'][key] = 0
            result['nutrition'][key] = round(float(result['nutrition'][key]), 1)

        return jsonify({'success': True, 'data': result}), 200

    except json.JSONDecodeError as e:
        return jsonify({'error': 'AI returned invalid response. Try again.', 'detail': str(e)}), 422
    except Exception as e:
        return jsonify({'error': f'Analysis failed: {str(e)}'}), 500
