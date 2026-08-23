from flask import Flask, request, jsonify
from flask_cors import CORS
import programsetup as ps
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv(override=True)

app = Flask(__name__)
CORS(app)  # Enable CORS for Chrome extension

@app.route('/generate-brochure', methods=['POST'])
def generate_brochure():
    """
    Generate a company brochure based on the provided company name and URL
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        company_name = data.get('company_name')
        url = data.get('url')
        
        if not company_name or not url:
            return jsonify({'error': 'Missing company_name or url'}), 400
        
        # Validate URL format
        if not url.startswith('http://') and not url.startswith('https://'):
            url = 'https://' + url
        
        print(f"Generating brochure for {company_name} at {url}")
        
        # Generate the brochure using existing logic
        brochure = ps.create_brochure(company_name, url)
        
        return jsonify({
            'success': True,
            'brochure': brochure,
            'company_name': company_name,
            'url': url
        })
    
    except Exception as e:
        print(f"Error generating brochure: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/health', methods=['GET'])
def health_check():
    """
    Simple health check endpoint
    """
    return jsonify({'status': 'healthy', 'message': 'Brochure Generator API is running'})

@app.route('/', methods=['GET'])
def home():
    """
    Home endpoint with API information
    """
    return jsonify({
        'name': 'Company Brochure Generator API',
        'version': '1.0',
        'endpoints': {
            '/generate-brochure': 'POST - Generate a company brochure',
            '/health': 'GET - Health check'
        }
    })

if __name__ == '__main__':
    # Check for OpenAI API key
    api_key = os.getenv('OPENAI_API_KEY')
    if not api_key:
        print("WARNING: OPENAI_API_KEY not found in environment variables!")
        print("Please create a .env file with your OpenAI API key")
    else:
        print("OpenAI API key loaded successfully")
    
    print("Starting Flask server on http://localhost:5000")
    print("Make sure to load the Chrome extension and use it to generate brochures!")
    app.run(debug=True, port=5000, host='localhost')
