#!/usr/bin/env python3
"""
Test script to verify TwelveLabs API integration
"""

import os
from twelvelabs import TwelveLabs

def test_twelve_labs_connection(api_key: str):
    """Test the connection to TwelveLabs API"""
    try:
        # Initialize client
        tl_client = TwelveLabs(api_key=api_key)
        print("✅ Successfully connected to TwelveLabs API")
        
        # Test listing indexes
        print("\n📋 Testing index listing...")
        indexes = tl_client.index.list(
            model_family="marengo",
            sort_by="created_at",
            sort_option="desc"
        )
        
        print(f"Found {len(indexes)} indexes:")
        for index in indexes:
            print(f"  - {index.name} (ID: {index.id}) - {index.video_count} videos")
        
        # Test creating an index
        print("\n➕ Testing index creation...")
        models = [
            {
                "name": "marengo2.7",
                "options": ["visual", "audio"]
            }
        ]
        
        test_index = tl_client.index.create(
            name="Test Index from SVC",
            models=models,
            addons=["thumbnail"]
        )
        print(f"✅ Created test index: {test_index.name} (ID: {test_index.id})")
        
        # Test listing videos in the new index
        print(f"\n🎥 Testing video listing for index {test_index.id}...")
        videos = tl_client.index.video.list(
            index_id=test_index.id,
            sort_by="created_at",
            sort_option="desc"
        )
        print(f"Found {len(videos)} videos in test index")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return False

if __name__ == "__main__":
    # Get API key from environment or user input
    api_key = os.environ.get('TWELVELABS_API_KEY')
    
    if not api_key:
        api_key = input("Enter your TwelveLabs API key: ").strip()
    
    if not api_key:
        print("❌ No API key provided")
        exit(1)
    
    print("🧪 Testing TwelveLabs API integration...")
    success = test_twelve_labs_connection(api_key)
    
    if success:
        print("\n✅ All tests passed! The backend should work with your API key.")
    else:
        print("\n❌ Tests failed. Please check your API key and try again.") 