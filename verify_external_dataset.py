import json
from pathlib import Path
import httpx

file_path = Path(r'c:/Users/Angga/Documents/Percodingan Duniawi/hackathon/steps_tracker_dataset.csv')

with file_path.open('rb') as f:
    files = {'file': ('steps_tracker_dataset.csv', f, 'text/csv')}
    data = {'style': 'dramatic'}
    response = httpx.post('http://127.0.0.1:8000/api/analyze', files=files, data=data, timeout=120)

print('STATUS', response.status_code)
print('BODY_KEYS', sorted(response.json().keys()))
result = response.json()
print('ARC', result.get('arc'))
print('STYLE', result.get('style'))
print('STORY_LENGTH', len(result.get('story', '')))
print('CITATIONS', len(result.get('citations', [])))
print('SEGMENTS', len(result.get('segments', [])))
print('GROUNDING', result.get('grounding', {}).get('arc_confidence'))
print('STORY_PREVIEW', result.get('story', '')[:500])
