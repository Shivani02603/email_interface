#!/usr/bin/env python3
"""
Test script to find available Gemini models
"""

import google.generativeai as genai

# Configure with your API key
genai.configure(api_key="AIzaSyA1lkemx839WTCMxLd6D10T7rwiwvsmGVc")

print("🔍 Finding available Gemini models...")
print("=" * 50)

try:
    available_models = []
    for model in genai.list_models():
        if 'generateContent' in model.supported_generation_methods:
            available_models.append(model.name)
            print(f"✅ Available model: {model.name}")
            
    if available_models:
        print(f"\n🎯 Found {len(available_models)} compatible models")
        print(f"🚀 Testing first model: {available_models[0]}")
        
        # Test the first available model
        test_model = genai.GenerativeModel(available_models[0])
        response = test_model.generate_content("Reply to this email: 'Are you free for coffee?'")
        print(f"\n✅ Test response: {response.text[:100]}...")
        
    else:
        print("❌ No compatible models found!")
        
except Exception as e:
    print(f"❌ Error: {e}")