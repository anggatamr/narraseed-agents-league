import httpx
import json

# Read sample CSV
with open('backend/data/sample_gpa.csv', 'rb') as f:
    files = {'file': f}
    data = {'style': 'dramatic'}
    
    # POST to analyze endpoint
    r = httpx.post('http://localhost:8000/api/analyze', files=files, data=data, timeout=30)
    
    if r.status_code == 200:
        result = r.json()
        print("✅ PIPELINE SUCCESSFUL")
        print(f"\nArc Detected: {result.get('arc')}")
        print(f"Style: {result.get('style')}")
        print(f"Confidence: {result.get('grounding', {}).get('arc_confidence', 'N/A')}")
        print(f"\nNarrative Preview (first 200 chars):")
        story = result.get('story', '')
        print(story[:200] + "..." if len(story) > 200 else story)
        print(f"\nCitations Count: {len(result.get('citations', []))}")
    else:
        print(f"❌ Error: {r.status_code}")
        print(r.text)
