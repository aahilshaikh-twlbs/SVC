from twelvelabs import TwelveLabs
from pinecone import Pinecone
import os
import json
import logging
import hashlib
from typing import List
from Iconik.SDK.Iconik import Iconik
from twelvelabs.models.embed import EmbeddingsTask, SegmentEmbedding
from dotenv import load_dotenv

load_dotenv()

tl_client = TwelveLabs(api_key=os.environ['TWELVELABS_API_KEY'])
pc = Pinecone(api_key=os.environ['PINECONE_API_KEY'])
ik = Iconik()

# Setup logger
logger = logging.getLogger('Embeddings creation starting')
logger.setLevel('DEBUG')

index = pc.Index("ffmpeg-test")

def parse_event(event):
    logger.info('Parsing event data...')
    event_data = json.loads(event['body'])

    # Extract collection_id and object_id from data
    data = event_data.get('data', {})
    asset_id = data.get('object_id')


    if not asset_id:
        logger.error('Object ID not found in event data.')
        raise KeyError('Object ID not found in event data.')

    return asset_id

def print_segments(segments: List[SegmentEmbedding], max_elements: int = 5):
    for segment in segments:
        print(
            f"  embedding_scope={segment.embedding_scope} start_offset_sec={segment.start_offset_sec} end_offset_sec={segment.end_offset_sec}"
        )
        print(f"  embeddings: {segment.embeddings_float[:max_elements]}")


def fetch_embeddings_and_upload(video_url):
    try:
        # Create an embedding task
        task = tl_client.embed.task.create(
            engine_name="Marengo-retrieval-2.6",
            video_url=video_url,
            video_clip_length=2,
            video_embedding_scopes=["clip","video"]
        )
        print(f"Created task: id={task.id} for video_url={video_url}")

        # Wait for task completion
        task.wait_for_done(sleep_interval=60, callback=lambda t: print(f"  Status={t.status}"))

        # Retrieve the task result
        task_result = tl_client.embed.task.retrieve(task.id)

        # If embeddings are available, process each segment and upload to Pinecone
        if task_result.video_embedding is not None and task_result.video_embedding.segments is not None:
            print_segments(task_result.video_embedding.segments)
            for segment in task_result.video_embedding.segments:
                embedding_vector = segment.embeddings_float
                metadata = {
                    "iconik_id": asset_id,
                    "tl_index_id": tl_index_id,
                    "tl_video_id": tl_video_id,
                    "start_offset_sec": segment.start_offset_sec,
                    "end_offset_sec": segment.end_offset_sec,
                    "embedding_scope": segment.embedding_scope
                }

                # Ensure consistent data types
                hash_input = f"{asset_id}_{float(segment.start_offset_sec)}_{float(segment.end_offset_sec)}"
                unique_id = hashlib.md5(hash_input.encode()).hexdigest()
                print(f"Generated unique_id during insertion: {unique_id}")

                # Upsert the vector to Pinecone with unique ID
                index.upsert([(unique_id, embedding_vector, metadata)])
                print(f"Upserted segment to Pinecone with ID: {unique_id} and scope: {segment.embedding_scope}")

    except Exception as e:
        print(f"Failed to fetch embeddings for {video_url}: {e}")

# New function to generate the unique ID
def generate_unique_id(iconik_id, start_offset_sec, end_offset_sec):
    hash_input = f"{iconik_id}_{float(start_offset_sec)}_{float(end_offset_sec)}"
    unique_id = hashlib.md5(hash_input.encode()).hexdigest()
    return unique_id

# Function to retrieve the vector from Pinecone
def retrieve_vector(iconik_id, start_offset_sec, end_offset_sec):
    unique_id = generate_unique_id(iconik_id, start_offset_sec, end_offset_sec)
    print(f"Generated unique_id during retrieval: {unique_id}")
    response = index.fetch(ids=[unique_id])
    if unique_id in response.vectors:
        vector_data = response.vectors[unique_id]
        vector = vector_data.values
        return vector
    else:
        print(f"Vector with ID {unique_id} not found in Pinecone index.")
        return None

# Function to perform similarity search
def perform_similarity_search(vector, top_k=5):
    results = index.query(
        vector=vector,
        top_k=top_k,
        filter={'embedding_scope': 'clip'},
        include_values=False,
        include_metadata=True
    )
    print("Query Results:", results)
    return results

# Function to get similar vectors with metadata
def get_similar_vectors(iconik_id, start_offset_sec, end_offset_sec, top_k=5):
    vector = retrieve_vector(iconik_id, start_offset_sec, end_offset_sec)
    if vector is None:
        print("No vector found for the provided parameters.")
        return None
    results = perform_similarity_search(vector, top_k)
    similar_vectors = []
    for match in results.matches:
        metadata = match.metadata
        similar_vectors.append({
            'iconik_id': metadata.get('iconik_id'),
            'start_offset_sec': metadata.get('start_offset_sec'),
            'end_offset_sec': metadata.get('end_offset_sec'),
            'score': match.score
        })
    return similar_vectors


event = {
    'body': '''
    {
      "system_domain_id": "86729aec-7ff0-11ef-a5cc-2e53d2c327db",
      "event_type": "collections",
      "object_id": "43b738dc-a6d5-11ef-859e-be5be1c7bfe0",
      "user_id": "8951f88e-7ff0-11ef-b7ae-4664fc99c07f",
      "realm": "contents",
      "operation": "create",
      "data": {
        "collection_id": "8ffdc442-8018-11ef-b615-0267038c3c9b",
        "date_created": "2024-10-02T17:06:00.314064+00:00",
        "object_id": "43b738dc-a6d5-11ef-859e-be5be1c7bfe0",
        "object_type": "assets",
        "parents": [
          "8712308e-8018-11ef-9f1f-0283d642dc0c",
          "8a48ede2-8018-11ef-8ef9-a2414cf6b678"
        ]
      },
      "request_id": "e2f3b065cba1b882f0fe8fa6efd6f3fd"
    }
    '''
}


asset_id = parse_event(event)
metadata_view_id = "15a799fc-801d-11ef-924a-ae3533ca58e0"
response = ik.get_asset_metadata(object_type='assets', object_id=asset_id, view_id=metadata_view_id)
print(f"Metadata: {response}")

tl_video_id = response["metadata_values"]["TL_VIDEO_ID"]["field_values"][0]["value"]
tl_index_id = response["metadata_values"]["TL_INDEX_ID"]["field_values"][0]["value"]

signed_url = ik.get_signed_url(asset_id)
print(asset_id)
print(signed_url)

fetch_embeddings_and_upload(signed_url)

# Now retrieve the vector and perform similarity search
start_offset_sec = 0.0  # Replace with actual value
end_offset_sec = 2.0    # Replace with actual value

similar_vectors = get_similar_vectors(asset_id, start_offset_sec, end_offset_sec, top_k=5)
if similar_vectors:
    print("Similar Vectors:")
    for vec in similar_vectors:
        print(vec)
else:
    print("No similar vectors found.")