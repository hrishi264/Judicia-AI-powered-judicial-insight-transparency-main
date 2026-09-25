"""
Direct test of Google Gemini API access
This bypasses langchain to test your API key directly
"""
import os
from dotenv import load_dotenv

print("="*60)
print("GEMINI API KEY DIAGNOSTIC TEST")
print("="*60)

load_dotenv()

api_key = os.getenv("GOOGLE_API_KEY")

if not api_key:
    print("❌ No GOOGLE_API_KEY found in .env file")
    print("   Create a .env file with: GOOGLE_API_KEY=your_key_here")
    exit()

print(f"✅ API Key found: {api_key[:20]}...")

# Test 1: Direct API with google-generativeai
print("\n" + "="*60)
print("TEST 1: Direct Google Generative AI Library")
print("="*60)

try:
    import google.generativeai as genai
    print("✅ google-generativeai package installed")
except ImportError:
    print("❌ google-generativeai not installed")
    print("   Install it: pip install google-generativeai")
    exit()

try:
    genai.configure(api_key=api_key)
    print("✅ API configured")
    
    # List available models
    print("\n📋 Listing available models...")
    models = []
    for m in genai.list_models():
        if 'generateContent' in m.supported_generation_methods:
            models.append(m.name)
            print(f"   ✅ {m.name}")
    
    if not models:
        print("   ❌ No models found!")
        print("   This means your API key doesn't have access to Gemini")
        print("\n   SOLUTION:")
        print("   1. Go to: https://aistudio.google.com/app/apikey")
        print("   2. Create a NEW API key (the free tier)")
        print("   3. Replace your current key in .env file")
        exit()
    
    # Test the first model
    print(f"\n🧪 Testing model: {models[0]}")
    model = genai.GenerativeModel(models[0])
    response = model.generate_content("Say 'Hello'")
    print(f"✅ Model works! Response: {response.text[:50]}")
    
    print("\n" + "="*60)
    print("✅ YOUR API KEY WORKS WITH DIRECT API!")
    print("="*60)
    print(f"\n💡 Working model: {models[0]}")
    print(f"   Use this in your code!")
    
except Exception as e:
    print(f"\n❌ Error: {e}")
    print("\n🔍 Diagnosis:")
    if "API_KEY_INVALID" in str(e):
        print("   Your API key is invalid")
        print("   Get a new one at: https://aistudio.google.com/app/apikey")
    elif "permission" in str(e).lower():
        print("   Your API key doesn't have permission")
        print("   Make sure Gemini API is enabled in Google Cloud Console")
    elif "quota" in str(e).lower():
        print("   You've hit your quota limit")
        print("   Wait or upgrade your plan")
    else:
        print("   Unknown error - check your internet connection")

# Test 2: Langchain integration
print("\n" + "="*60)
print("TEST 2: Langchain Google GenAI")
print("="*60)

try:
    from langchain_google_genai import ChatGoogleGenerativeAI
    print("✅ langchain-google-genai package installed")
    
    # If we got models from Test 1, try to use them
    if models:
        # Extract just the model name (remove 'models/' prefix if present)
        model_name = models[0].replace('models/', '')
        
        print(f"\n🧪 Testing langchain with: {model_name}")
        
        llm = ChatGoogleGenerativeAI(
            model=model_name,
            google_api_key=api_key,
            temperature=0.3
        )
        
        response = llm.invoke("Say 'Hello'")
        print(f"✅ Langchain works! Response: {response.content[:50]}")
        
        print("\n" + "="*60)
        print("✅ LANGCHAIN INTEGRATION WORKS!")
        print("="*60)
        print(f"\n💡 Use this model in your main.py:")
        print(f'   model="{model_name}"')
        
except ImportError:
    print("❌ langchain-google-genai not installed")
    print("   Install it: pip install langchain-google-genai")
except Exception as e:
    print(f"❌ Langchain error: {e}")
    print("\n💡 The direct API works but langchain doesn't.")
    print("   This is a langchain compatibility issue.")
    print("   Try upgrading: pip install --upgrade langchain-google-genai")

print("\n" + "="*60)
print("DIAGNOSTIC COMPLETE")
print("="*60)