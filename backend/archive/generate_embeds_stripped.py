### test pinecone integ from docs article


from twelvelabs import TwelveLabs
from twelvelabs.models.embed import EmbeddingsTask
from dotenv import load_dotenv
import os
from pinecone import Pinecone
import threading

# Load environment variables
load_dotenv()

# Initialize clients
tl_client = TwelveLabs(api_key=os.environ['TWELVELABS_API_KEY'])
pc = Pinecone(api_key=os.environ['PINECONE_API_KEY'])

def generate_embedding(video_file=None, yt_url=None, engine="Marengo-retrieval-2.7"):
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
        video_file=video_file,
        video_url=yt_url,
        video_clip_length=2
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
    
    # Retrieve results (full with all metadata)
    task_result = tl_client.embed.task.retrieve(task.id)
    
    # return on call
    return task_result

def ingest_data(video_file, index_name="ffmpeg-dense-2"):
    """
    Generate embeddings and store them in Pinecone.
    
    Args:
        video_file (str): Path to the video file
        index_name (str): Name of the Pinecone index
    """
    # Generate embeddings
    full_embeddings = generate_embedding(video_file)
    
    # Connect to Pinecone index
    index = pc.Index(index_name)
    
    # Prepare vectors for upsert
    vectors = []
    # Extract segments from video_embedding
    segments = full_embeddings.video_embedding.segments
    for i, segment in enumerate(segments):
        vectors.append({
            "id": f"{video_file}_{i}",
            "values": segment.embeddings_float,
            "metadata": {
                "video_file": video_file,
                "start_offset_sec": segment.start_offset_sec,
                "end_offset_sec": segment.end_offset_sec,
                "scope": segment.embedding_scope,
                "embedding_option": segment.embedding_option
            }
        })
    
    # Upsert vectors to Pinecone
    index.upsert(vectors=vectors)
    print(f"Successfully ingested {len(vectors)} embeddings into Pinecone")

def main(in1, in2):
    """
    Essentially mutlithreads the generate-->upload-to-pinecone process for both videos
    """
    threading.Thread(target=ingest_data, args=(in1,)).start()
    threading.Thread(target=ingest_data, args=(in2,)).start()


main("/Users/ashaikh/Documents/Code/SVC/backend/ffmpeg_tests/2b2g6b.mp4", "/Users/ashaikh/Documents/Code/SVC/backend/ffmpeg_tests/10b.mp4")

### todo
# function to then pull values from the pineconedb for the just-created embeds, separated by video for no mix ups obviously
# then we run @compare_embeds.py with the 