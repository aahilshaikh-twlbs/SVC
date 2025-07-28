### test pinecone integ from docs article


from twelvelabs import TwelveLabs
from twelvelabs.models.embed import EmbeddingsTask
from dotenv import load_dotenv
import os
from pinecone import Pinecone

# Load environment variables
load_dotenv()

# Initialize clients
tl_client = TwelveLabs(api_key=os.environ['TWELVELABS_API_KEY'])
pc = Pinecone(api_key=os.environ['PINECONE_API_KEY'])

def generate_embedding(video_file, engine="Marengo-retrieval-2.7"):
    """
    Generate embeddings for a video file using TwelveLabs API.
    
    Args:
        video_file (str): Path to the video file
        engine (str): Embedding engine name
        
    Returns:
        tuple: Embeddings and metadata
    """
    # Create an embedding task
    task = tl_client.embed.task.create(
        model_name=engine,
        video_file=video_file
    )
    print(f"Created task: id={task.id} engine_name={task.model_name} status={task.status}")
    
    # Monitor task progress
    def on_task_update(task: EmbeddingsTask):
        print(f"  Status={task.status}")
    
    status = task.wait_for_done(
        sleep_interval=2,
        callback=on_task_update
    )
    print(f"Embedding done: {status}")
    
    # Retrieve results
    task_result = tl_client.embed.task.retrieve(task.id)
    
    # Extract embeddings and metadata
    embeddings = task_result.float
    time_ranges = task_result.time_ranges
    scope = task_result.scope
    # full_embeddings=task_result
    
    return embeddings, time_ranges, scope
    # return full_embeddings

def ingest_data(video_file, index_name="ffmpeg-test"):
    """
    Generate embeddings and store them in Pinecone.
    
    Args:
        video_file (str): Path to the video file
        index_name (str): Name of the Pinecone index
    """
    # Generate embeddings
    embeddings, time_ranges, scope = generate_embedding(video_file)
    
    # Connect to Pinecone index
    index = pc.Index(index_name)
    
    # Prepare vectors for upsert
    vectors = []
    for i, embedding in enumerate(embeddings):
        vectors.append({
            "id": f"{video_file}_{i}",
            "values": embedding,
            "metadata": {
                "video_file": video_file,
                "time_range": time_ranges[i],
                "scope": scope
            }
        })
    
    # Upsert vectors to Pinecone
    index.upsert(vectors=vectors)
    print(f"Successfully ingested {len(vectors)} embeddings into Pinecone")




ingest_data("/Users/ashaikh/Documents/Code/SVC/backend/ffmpeg_tests/2b2g6b.mp4")