"""
Inspect the YouTube Transcript API to understand its structure
"""
from youtube_transcript_api import YouTubeTranscriptApi
import inspect

print("="*60)
print("YOUTUBE TRANSCRIPT API INSPECTION")
print("="*60)

# Check if it's a class or instance
print(f"\nType: {type(YouTubeTranscriptApi)}")
print(f"Is class: {inspect.isclass(YouTubeTranscriptApi)}")

# Get all methods
print("\n" + "="*60)
print("ALL METHODS AND ATTRIBUTES:")
print("="*60)
for attr in dir(YouTubeTranscriptApi):
    if not attr.startswith('_'):
        obj = getattr(YouTubeTranscriptApi, attr)
        print(f"\n{attr}:")
        print(f"  Type: {type(obj)}")
        if callable(obj):
            print(f"  Callable: Yes")
            try:
                sig = inspect.signature(obj)
                print(f"  Signature: {sig}")
            except:
                print(f"  Signature: Could not determine")

# Try to understand how to call it
print("\n" + "="*60)
print("TESTING DIFFERENT CALL METHODS:")
print("="*60)

test_video_id = "dQw4w9WgXcQ"

# Test 1: Try as class method
print("\nTest 1: Class method style")
try:
    result = YouTubeTranscriptApi.fetch(test_video_id)
    print(f"✓ Success with class method!")
    print(f"  Result type: {type(result)}")
except Exception as e:
    print(f"✗ Failed: {e}")

# Test 2: Try creating instance
print("\nTest 2: Instance method style")
try:
    api = YouTubeTranscriptApi()
    result = api.fetch(test_video_id)
    print(f"✓ Success with instance method!")
    print(f"  Result type: {type(result)}")
    if isinstance(result, list) and len(result) > 0:
        print(f"  First entry: {result[0]}")
except Exception as e:
    print(f"✗ Failed: {e}")

# Test 3: Check the actual module for other functions
print("\nTest 3: Check module level functions")
import youtube_transcript_api
for name in dir(youtube_transcript_api):
    obj = getattr(youtube_transcript_api, name)
    if callable(obj) and not name.startswith('_'):
        print(f"  {name}: {type(obj)}")

print("\n" + "="*60)
print("INSPECTION COMPLETE")
print("="*60)