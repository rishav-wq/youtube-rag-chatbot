"""
Quick test script to verify the new API works
"""
from youtube_transcript_api import YouTubeTranscriptApi

# Test with a known video (Rick Astley - Never Gonna Give You Up)
test_video_id = "dQw4w9WgXcQ"

print("Testing YouTube Transcript API...")
print(f"Video ID: {test_video_id}")
print("="*60)

try:
    # Method 1: Direct fetch
    print("\nMethod 1: Direct fetch")
    transcript = YouTubeTranscriptApi.fetch(test_video_id)
    
    if isinstance(transcript, list):
        print(f"✓ Success! Got {len(transcript)} transcript entries")
        print(f"First entry: {transcript[0]}")
        
        # Combine text
        full_text = " ".join([entry.get('text', '') for entry in transcript])
        print(f"Total text length: {len(full_text)} characters")
        print(f"First 200 chars: {full_text[:200]}...")
    else:
        print(f"✓ Got transcript object: {type(transcript)}")
        
except Exception as e:
    print(f"✗ Direct fetch failed: {e}")
    
    # Method 2: List then fetch
    try:
        print("\nMethod 2: List available transcripts")
        transcript_list = YouTubeTranscriptApi.list(test_video_id)
        print(f"✓ Found {len(transcript_list)} available transcripts")
        
        # Fetch first available
        transcript = transcript_list[0].fetch()
        print(f"✓ Fetched first transcript")
        
        if isinstance(transcript, list):
            full_text = " ".join([entry.get('text', '') for entry in transcript])
            print(f"Total text length: {len(full_text)} characters")
            
    except Exception as e2:
        print(f"✗ List fetch also failed: {e2}")

print("\n" + "="*60)
print("Test complete!")