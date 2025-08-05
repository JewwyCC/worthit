#!/usr/bin/env python3
"""
YouTube Blocking Diagnostic Tool

This script helps distinguish between:
1. YouTube IP blocking
2. Transcript API issues  
3. Video-specific problems
4. Network/proxy issues
"""

import requests
import time
from youtube_search import YoutubeSearch
from youtube_transcript_api import YouTubeTranscriptApi
# PyTube removed - using search metadata instead

def test_basic_connectivity():
    """Test basic internet connectivity"""
    print("🌐 Testing Basic Connectivity...")
    
    try:
        response = requests.get("https://httpbin.org/ip", timeout=10)
        print(f"✅ Internet connectivity: OK")
        print(f"   Your IP: {response.json().get('origin', 'Unknown')}")
        return True
    except Exception as e:
        print(f"❌ Internet connectivity failed: {e}")
        return False

def test_youtube_accessibility():
    """Test if YouTube is accessible"""
    print("\n🎯 Testing YouTube Accessibility...")
    
    try:
        # Test YouTube homepage
        response = requests.get("https://www.youtube.com", timeout=10)
        if response.status_code == 200:
            print("✅ YouTube homepage: Accessible")
        else:
            print(f"⚠️ YouTube homepage: Status {response.status_code}")
    except Exception as e:
        print(f"❌ YouTube homepage: Failed - {e}")
    
    try:
        # Test YouTube API endpoint
        response = requests.get("https://www.googleapis.com/youtube/v3/search", timeout=10)
        print(f"✅ YouTube API endpoint: Accessible (status {response.status_code})")
    except Exception as e:
        print(f"❌ YouTube API endpoint: Failed - {e}")

def test_youtube_search():
    """Test if YouTube search is working"""
    print("\n🔍 Testing YouTube Search...")
    
    try:
        search = YoutubeSearch("basketball shoes", max_results=3)
        videos = search.videos
        
        if videos and len(videos) > 0:
            print(f"✅ YouTube search: Found {len(videos)} videos")
            for i, video in enumerate(videos[:2], 1):
                print(f"   Video {i}: {video.get('title', 'Unknown')[:50]}...")
            return videos[0] if videos else None
        else:
            print("⚠️ YouTube search: No videos found")
            return None
            
    except Exception as e:
        print(f"❌ YouTube search failed: {e}")
        return None

def test_specific_video_access(video_id):
    """Test access to a specific YouTube video"""
    print(f"\n📺 Testing Video Access: {video_id}")
    
    # Test direct video URL
    video_url = f"https://www.youtube.com/watch?v={video_id}"
    try:
        response = requests.get(video_url, timeout=10)
        if response.status_code == 200:
            print(f"✅ Direct video URL: Accessible")
            if "Video unavailable" in response.text:
                print("⚠️ Video shows as unavailable")
            elif "This video is private" in response.text:
                print("⚠️ Video is private")
            else:
                print("✅ Video appears to be available")
        else:
            print(f"⚠️ Direct video URL: Status {response.status_code}")
    except Exception as e:
        print(f"❌ Direct video URL failed: {e}")

def test_search_metadata_access(video_id, description):
    """Test getting video metadata from search results"""
    print(f"\n📹 Testing Search Metadata Access: {video_id}")
    
    try:
        # Search for the specific video
        search = YoutubeSearch(f"{description} {video_id}", max_results=5)
        videos = search.videos
        
        # Look for our specific video ID
        target_video = None
        for video in videos:
            if video.get('id') == video_id:
                target_video = video
                break
        
        if target_video:
            print(f"✅ Found video in search results:")
            print(f"   Title: {target_video.get('title', 'Unknown')[:50]}...")
            print(f"   Channel: {target_video.get('channel', 'Unknown')}")
            print(f"   Duration: {target_video.get('duration', 'Unknown')}")
            print(f"   Views: {target_video.get('views', 'Unknown')}")
            return True
        else:
            print(f"⚠️ Video not found in search results (but this is normal for specific IDs)")
            return False
            
    except Exception as e:
        print(f"❌ Search metadata failed: {e}")
        return False

def test_transcript_methods(video_id):
    """Test all transcript methods"""
    print(f"\n📄 Testing Transcript Methods: {video_id}")
    
    methods_tested = 0
    methods_successful = 0
    
    # Method 1: Direct fetch
    try:
        print("   Testing Method 1: Direct fetch()")
        ytt_api = YouTubeTranscriptApi()
        fetched_transcript = ytt_api.fetch(video_id)
        transcript_text = " ".join([snippet.text for snippet in fetched_transcript])
        print(f"   ✅ Method 1 Success: {len(transcript_text)} chars")
        methods_successful += 1
    except Exception as e:
        print(f"   ❌ Method 1 Failed: {e}")
        if "blocked" in str(e).lower() or "ip" in str(e).lower():
            print("   🔍 Error suggests IP blocking")
    methods_tested += 1
    
    # Method 2: List then fetch
    try:
        print("   Testing Method 2: list() then fetch()")
        ytt_api = YouTubeTranscriptApi()
        transcript_list = ytt_api.list(video_id)
        
        # Find English transcript
        transcript = None
        try:
            transcript = transcript_list.find_manually_created_transcript(['en'])
            print("   📝 Found manual English transcript")
        except:
            try:
                transcript = transcript_list.find_generated_transcript(['en'])
                print("   🤖 Found auto-generated English transcript")
            except:
                if len(list(transcript_list)) > 0:
                    transcript = list(transcript_list)[0]
                    print(f"   🌐 Using first available transcript")
        
        if transcript:
            fetched_data = transcript.fetch()
            transcript_text = " ".join([snippet['text'] for snippet in fetched_data])
            print(f"   ✅ Method 2 Success: {len(transcript_text)} chars")
            methods_successful += 1
        else:
            print("   ⚠️ Method 2: No transcripts available")
            
    except Exception as e:
        print(f"   ❌ Method 2 Failed: {e}")
        if "blocked" in str(e).lower() or "ip" in str(e).lower():
            print("   🔍 Error suggests IP blocking")
    methods_tested += 1
    
    return methods_successful, methods_tested

def test_multiple_videos():
    """Test multiple videos to see if it's video-specific"""
    print("\n🎬 Testing Multiple Videos...")
    
    # Test different types of videos
    test_videos = [
        ("0RpYQvtf790", "Nike LeBron 21 Performance Review"),  # Basketball shoe review
        ("dQw4w9WgXcQ", "Rick Astley - Never Gonna Give You Up"),  # Popular music video
        ("M7lc1UVf-VE", "YouTube Tutorial"),  # Educational content
    ]
    
    results = {}
    
    for video_id, description in test_videos:
        print(f"\n   Testing: {description}")
        
        # Test search metadata
        metadata_success = test_search_metadata_access(video_id, description)
        
        # Test transcripts
        transcript_success, transcript_total = test_transcript_methods(video_id)
        
        results[video_id] = {
            'description': description,
            'metadata': metadata_success,
            'transcript_success': transcript_success,
            'transcript_total': transcript_total
        }
        
        # Add delay between tests
        time.sleep(2)
    
    return results

def test_with_proxy():
    """Test with SwiftShadow proxy"""
    print("\n🔀 Testing with SwiftShadow Proxy...")
    
    try:
        from swiftshadow import QuickProxy
        
        proxy_manager = QuickProxy()
        if len(proxy_manager) >= 2:
            proxy_address = proxy_manager[0]  # ip:port
            proxy_protocol = proxy_manager[1]  # http/https
            proxy_url = f"{proxy_protocol}://{proxy_address}"
            proxy_dict = {'http': proxy_url, 'https': proxy_url}
            
            print(f"   Using proxy: {proxy_url}")
            
            # Test with proxy
            response = requests.get("https://httpbin.org/ip", proxies=proxy_dict, timeout=10)
            proxy_ip = response.json().get('origin', 'Unknown')
            print(f"   ✅ Proxy IP: {proxy_ip}")
            
            # Test YouTube with proxy
            response = requests.get("https://www.youtube.com", proxies=proxy_dict, timeout=10)
            if response.status_code == 200:
                print(f"   ✅ YouTube via proxy: Accessible")
            else:
                print(f"   ⚠️ YouTube via proxy: Status {response.status_code}")
                
            return proxy_dict
        else:
            print("   ⚠️ No proxy available from SwiftShadow")
            return None
            
    except Exception as e:
        print(f"   ❌ Proxy test failed: {e}")
        return None

def analyze_results(results):
    """Analyze test results and provide diagnosis"""
    print("\n" + "="*60)
    print("🔍 DIAGNOSIS RESULTS")
    print("="*60)
    
    # Count successes
    total_videos = len(results)
    metadata_successes = sum(1 for r in results.values() if r['metadata'])
    transcript_successes = sum(r['transcript_success'] for r in results.values())
    transcript_attempts = sum(r['transcript_total'] for r in results.values())
    
    print(f"📊 Summary:")
    print(f"   Videos tested: {total_videos}")
    print(f"   Search metadata success rate: {metadata_successes}/{total_videos} ({metadata_successes/total_videos*100:.0f}%)")
    print(f"   Transcript success rate: {transcript_successes}/{transcript_attempts} ({transcript_successes/transcript_attempts*100:.0f}%)")
    
    # Provide diagnosis
    print(f"\n🎯 Likely Cause:")
    
    if metadata_successes == 0 and transcript_successes == 0:
        print("   🚫 COMPLETE YOUTUBE BLOCKING")
        print("   ➤ Your IP is likely blocked by YouTube")
        print("   ➤ Try using VPN or different network")
        
    elif metadata_successes > 0 and transcript_successes == 0:
        print("   📄 TRANSCRIPT API BLOCKING")
        print("   ➤ YouTube is blocking transcript requests")
        print("   ➤ Search metadata still works - good for our scraper!")
        
    elif metadata_successes == 0 and transcript_successes > 0:
        print("   🔍 SEARCH API ISSUES")
        print("   ➤ Search having problems but transcripts work")
        print("   ➤ Unusual pattern")
        
    elif metadata_successes < total_videos or transcript_successes < transcript_attempts:
        print("   ⚡ PARTIAL BLOCKING / RATE LIMITING")
        print("   ➤ Some requests are getting through")
        print("   ➤ Try longer delays between requests")
        
    else:
        print("   ✅ NO BLOCKING DETECTED")
        print("   ➤ APIs appear to be working normally")
        print("   ➤ Issues might be video-specific")
    
    print(f"\n💡 Recommendations:")
    if metadata_successes > 0:
        print("   ✅ Search metadata working - our PyTube-free approach is correct!")
        print("   • Continue using search results for video metadata")
    
    if transcript_successes == 0:
        print("   • Use video descriptions/metadata as content fallback")
        print("   • Try requests with different user agents")
        print("   • Consider using proxy rotation")
    else:
        print("   ✅ Transcripts working - core functionality intact!")

def main():
    """Run comprehensive YouTube blocking diagnosis"""
    print("🔬 YouTube Blocking Diagnostic Tool")
    print("=" * 50)
    
    # Run all tests
    if not test_basic_connectivity():
        print("❌ Basic connectivity failed. Check your internet connection.")
        return
    
    test_youtube_accessibility()
    
    test_video = test_youtube_search()
    if test_video:
        video_id = test_video.get('id')
        if video_id:
            test_specific_video_access(video_id)
    
    # Test multiple videos
    results = test_multiple_videos()
    
    # Test with proxy
    test_with_proxy()
    
    # Analyze and provide diagnosis
    analyze_results(results)
    
    print(f"\n🏁 Diagnosis complete!")

if __name__ == "__main__":
    main() 