################

# Better version of gen_embeds; simpler usage, more modular, refactored to remove Iconik, add in simple filepath support

################


from twelvelabs import TwelveLabs
from pinecone import Pinecone
from dotenv import load_dotenv
import os
import json
from typing import List, Optional
from twelvelabs.models.embed import EmbeddingsTask, SegmentEmbedding
from datetime import datetime

# Load environment variables
load_dotenv()

# Initialize clients
tl_client = TwelveLabs(api_key=os.environ['TWELVELABS_API_KEY'])
pc = Pinecone(api_key=os.environ['PINECONE_API_KEY'])

def create_embedding_task(filepath: str, clip_length: int = 2) -> EmbeddingsTask:
    """
    Create an embedding task for a video file.
    
    Args:
        filepath: Path to the video file
        clip_length: Length of video clips in seconds
        
    Returns:
        EmbeddingsTask object
    """
    print(f"🔄 Creating embedding task for: {filepath}")
    
    task = tl_client.embed.task.create(
        model_name="Marengo-retrieval-2.7",
        video_file=filepath,
        video_clip_length=clip_length,
        video_embedding_scopes=["clip", "video"]
    )
    
    print(f"✅ Task created with ID: {task.id}")
    return task

def on_task_update(task: EmbeddingsTask) -> None:
    """
    Callback function for task status updates.
    
    Args:
        task: The embedding task
    """
    print(f"📊 Status: {task.status}")

def wait_for_embedding_completion(task: EmbeddingsTask, sleep_interval: int = 5) -> EmbeddingsTask:
    """
    Wait for embedding task to complete with status updates.
    
    Args:
        task: The embedding task
        sleep_interval: Seconds between status checks
        
    Returns:
        Completed EmbeddingsTask
    """
    print("⏳ Waiting for embedding to complete...")
    print(f"📋 Task ID: {task.id}")
    
    # Wait for completion
    task.wait_for_done(
        sleep_interval=sleep_interval, 
        callback=on_task_update
    )
    
    print("✅ Embedding completed successfully!")
    
    # Retrieve the updated task to get final results
    updated_task = tl_client.embed.task.retrieve(task.id)
    return updated_task

def save_embeddings_to_json(task: EmbeddingsTask, output_dir: str = "embeddings") -> str:
    """
    Save full embeddings to a JSON file.
    
    Args:
        task: The completed embedding task
        output_dir: Directory to save the JSON file
        
    Returns:
        Path to the saved JSON file
    """
    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)
    
    # Generate filename with timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"embeddings_{task.id}_{timestamp}.json"
    filepath = os.path.join(output_dir, filename)
    
    # Prepare data structure
    embedding_data = {
        "task_id": task.id,
        "status": task.status,
        "model_name": task.model_name,
        "created_at": str(task.created_at),
        "video_embedding": None,
        "metadata": {
            "total_segments": 0,
            "embedding_dimensions": 0,
            "exported_at": timestamp
        }
    }
    
    # Extract video embedding data
    if task.video_embedding and task.video_embedding.segments:
        segments_data = []
        total_dimensions = 0
        
        for i, segment in enumerate(task.video_embedding.segments):
            segment_data = {
                "segment_index": i,
                "embedding_scope": segment.embedding_scope,
                "embedding_option": segment.embedding_option,
                "start_offset_sec": segment.start_offset_sec,
                "end_offset_sec": segment.end_offset_sec,
                "duration_sec": segment.end_offset_sec - segment.start_offset_sec,
                "embeddings_float": segment.embeddings_float if hasattr(segment, 'embeddings_float') else [],
                "embeddings_int8": segment.embeddings_int8 if hasattr(segment, 'embeddings_int8') else [],
                "embeddings_uint8": segment.embeddings_uint8 if hasattr(segment, 'embeddings_uint8') else []
            }
            
            # Track embedding dimensions
            if hasattr(segment, 'embeddings_float') and segment.embeddings_float:
                total_dimensions = len(segment.embeddings_float)
            
            segments_data.append(segment_data)
        
        embedding_data["video_embedding"] = {
            "segments": segments_data
        }
        embedding_data["metadata"]["total_segments"] = len(segments_data)
        embedding_data["metadata"]["embedding_dimensions"] = total_dimensions
    
    # Save to JSON file
    with open(filepath, 'w') as f:
        json.dump(embedding_data, f, indent=2, default=str)
    
    print(f"💾 Embeddings saved to: {filepath}")
    print(f"📊 Total segments: {embedding_data['metadata']['total_segments']}")
    print(f"🔢 Embedding dimensions: {embedding_data['metadata']['embedding_dimensions']}")
    
    return filepath

def print_segments(segments: List[SegmentEmbedding], max_elements: int = 5) -> None:
    """
    Print formatted segment information.
    
    Args:
        segments: List of segment embeddings
        max_elements: Maximum number of embedding elements to display
    """
    print(f"\n📊 Embedding Segments ({len(segments)} total):")
    print("=" * 60)
    
    for i, segment in enumerate(segments, 1):
        print(f"\n🔹 Segment {i}:")
        print(f"   Scope: {segment.embedding_scope}")
        print(f"   Option: {segment.embedding_option}")
        print(f"   Time: {segment.start_offset_sec:.2f}s - {segment.end_offset_sec:.2f}s")
        print(f"   Duration: {segment.end_offset_sec - segment.start_offset_sec:.2f}s")
        
        if hasattr(segment, 'embeddings_float') and segment.embeddings_float:
            embedding_preview = segment.embeddings_float[:max_elements]
            print(f"   Embedding preview: {embedding_preview}")
            print(f"   Embedding dimensions: {len(segment.embeddings_float)}")
        else:
            print("   ⚠️  No embedding data available")

def retrieve_embedding_task(task_id: str) -> Optional[EmbeddingsTask]:
    """
    Retrieve an existing embedding task by ID.
    
    Args:
        task_id: The task ID to retrieve
        
    Returns:
        EmbeddingsTask if found, None otherwise
    """
    try:
        print(f"🔍 Retrieving task: {task_id}")
        task = tl_client.embed.task.retrieve(task_id)
        print("✅ Task retrieved successfully")
        return task
    except Exception as e:
        print(f"❌ Error retrieving task: {e}")
        return None

def analyze_embedding_task(task: EmbeddingsTask) -> None:
    """
    Analyze and display comprehensive information about an embedding task.
    
    Args:
        task: The embedding task to analyze
    """
    print("\n📋 Task Analysis:")
    print("=" * 40)
    print(f"Task ID: {task.id}")
    print(f"Status: {task.status}")
    print(f"Model: {task.model_name}")
    print(f"Created: {task.created_at}")
    
    if task.video_embedding and task.video_embedding.segments:
        print_segments(task.video_embedding.segments)
    else:
        print("⚠️  No video embedding segments found")

def main():
    """
    Main function demonstrating the embed generation and retrieval workflow.
    """
    print("🎬 TwelveLabs Embedding Tool")
    print("=" * 40)
    
    # Example usage - replace with your actual file path
    filepath = input("Enter video file path: ").strip()
    
    if not filepath or not os.path.exists(filepath):
        print("❌ Invalid file path provided")
        return
    
    try:
        # Create embedding task
        task = create_embedding_task(filepath)
        
        # Wait for completion
        completed_task = wait_for_embedding_completion(task)
        
        # Analyze results
        analyze_embedding_task(completed_task)
        
        # Save embeddings to JSON
        json_filepath = save_embeddings_to_json(completed_task)
        
        print("\n🎉 Process completed successfully!")
        print(f"📁 Embeddings saved to: {json_filepath}")
        
    except Exception as e:
        print(f"❌ Error during embedding process: {e}")

if __name__ == "__main__":
    main()