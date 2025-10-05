"""
Test to understand FetchedTranscript structure
"""
from youtube_transcript_api import YouTubeTranscriptApi

test_video_id = "dQw4w9WgXcQ"

print("Testing FetchedTranscript object...")
print("="*60)

api = YouTubeTranscriptApi()
result = api.fetch(test_video_id)

print(f"Result type: {type(result)}")
print(f"Result class name: {result.__class__.__name__}")

print("\n" + "="*60)
print("Available attributes and methods:")
print("="*60)
for attr in dir(result):
    if not attr.startswith('_'):
        print(f"  {attr}")

print("\n" + "="*60)
print("Testing different ways to get text:")
print("="*60)

# Test 1: Check if it has a 'text' attribute
if hasattr(result, 'text'):
    print(f"✓ Has 'text' attribute")
    print(f"  Type: {type(result.text)}")
    print(f"  Content preview: {str(result.text)[:200]}")

# Test 2: Check if it has 'snippets' or 'entries'
if hasattr(result, 'snippets'):
    print(f"✓ Has 'snippets' attribute")
    snippets = result.snippets
    print(f"  Type: {type(snippets)}")
    if isinstance(snippets, list) and len(snippets) > 0:
        print(f"  Number of snippets: {len(snippets)}")
        print(f"  First snippet: {snippets[0]}")

# Test 3: Check if it's iterable
try:
    print("\nTest 3: Try iterating")
    count = 0
    first_item = None
    for item in result:
        if count == 0:
            first_item = item
        count += 1
    print(f"✓ Is iterable! Found {count} items")
    print(f"  First item: {first_item}")
    print(f"  First item type: {type(first_item)}")
    
    # If first item is a dict or has text
    if isinstance(first_item, dict):
        print(f"  First item keys: {first_item.keys()}")
    elif hasattr(first_item, 'text'):
        print(f"  First item text: {first_item.text}")
        
except Exception as e:
    print(f"✗ Not iterable: {e}")

# Test 4: Try to convert to string
print("\nTest 4: String representation")
print(f"str(result)[:500] = {str(result)[:500]}")

# Test 5: Check __dict__
if hasattr(result, '__dict__'):
    print("\nTest 5: Object __dict__")
    print(f"  Keys: {result.__dict__.keys()}")

print("\n" + "="*60)
print("Test complete!")
print("="*60)