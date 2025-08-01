####### important functions from TwelveLabs API and SDK

from twelvelabs import TwelveLabs
from twelvelabs.models.embed import EmbeddingsTask, SegmentEmbedding
import os
from dotenv import load_dotenv
from typing import List

load_dotenv()

tl_client=TwelveLabs(api_key=os.environ['TWELVELABS_API_KEY'])

# generate embeds on non indexed videos
def create_embed_task(filepath):
    """
    Parameters:

    Name	                Type	                                    Required	Description
    model_name	            Literal["Marengo-retrieval-2.7"]	        Yes	        The name of the video understanding model to use. Example: “Marengo-retrieval-2.7”.
    video_file	            Union[str, BinaryIO, None]	                No	        Path to the video file or a file-like object.
    video_url	            Optional[str]	                            No	        The publicly accessible URL of the video.
    video_start_offset_sec	Optional[float]	                            No	        The start offset in seconds from the beginning of the video where processing should begin.
    video_end_offset_sec	Optional[float]	                            No	        The end offset in seconds from the beginning of the video where processing should stop.
    video_clip_length	    Optional[int]	                            No	        The desired duration in seconds for each clip for which the platform generates an embedding.
    video_embedding_scopes	Optional[List[Literal["clip", "video"]]]	No	        Specifies the embedding scope. Valid values are ["clip"] OR ["clip", "video"]
    
    - Return value: Returns a models.EmbeddingsTask object representing the new video embedding task.
    """

    task=tl_client.embed.task.create(
        model_name="Marengo-retrieval-2.7",
        video_file=filepath,
        # video_url="<YOUR_VIDEO_URL>",
        # video_start_offset_sec=0,
        # video_end_offset_sec=10,
        video_clip_length=2,
        video_embedding_scopes=["clip", "video"]
    )

    print(task)

# get task status of creation of embeds
def get_task_status(taskid):
    """
    ^^ for the taskid param i just ran the create task first and got the id from that for the moment; we'll assimilate this later
    
    Parameters:

    Name        Type	Required    Description
    task_id	    string	Yes	        The unique identifier of the video embedding task.
    **kwargs	dict	No	        Additional keyword arguments for the request.
    
    - Return value: Returns a models.EmbeddingsTaskStatus object containing the current status of the embedding task.
    
    """
    task = tl_client.embed.task.status(task_id=taskid)
    print(f"Task ID: {task.id}")
    print(f"Model Name: {task.model_name}")
    print(f"Status: {task.status}")

# callback checker to see if its complete
def check_complete():
    """
    Parameters

    Name	        Type	                                    Required	Description
    sleep_interval	float	                                    No	        Sets the time in seconds to wait between status checks. Must be greater than 0. Default is 5.0.
    callback	    Optional[Callable[[EmbeddingsTask], None]]	No	        Provides an optional function to call after each status check. The function receives the current task object. Use this to monitor progress.
    **kwargs	    dict	                                    No	        Passes additional keyword arguments to the update_status method when checking the task status.

    - Return value: Returns a string representing the status of the task.
    """
    def on_task_update(task: EmbeddingsTask):
        print(f"  Status={task.status}")
    status = task.wait_for_done(sleep_interval=5, callback=on_task_update)
    print(f"Embedding done: {status}")

# retrieve the final embed object
def retrieve_embed_object():
    """
    Parameters:

    Name	    Type	Required	Description
    **kwargs	dict	No	        Additional keyword arguments for the request.
    
    - Return value: Returns a models.EmbeddingsTask object containing the details of the embedding task, including the embeddings if available. The video_embeddings property of the returned object is a RootModelList of VideoEmbedding objects when the task is completed, or None if the embeddings are not yet available.
    """
    def print_segments(segments: List[SegmentEmbedding], max_elements: int = 5):
        for segment in segments:
            print(
                f"  embedding_scope={segment.embedding_scope} embedding_option={segment.embedding_option} start_offset_sec={segment.start_offset_sec} end_offset_sec={segment.end_offset_sec}"
            )
            print(f"  embeddings: {segment.embeddings_float[:max_elements]}")
    
    task = tl_client.embed.task.retrieve(embedding_option=["visual-text"])
    if task.video_embedding is not None and task.video_embedding.segments is not None:
        print_segments(task.video_embedding.segments)


# create_embed_task("/Users/ashaikh/Documents/Code/SAGE/backend/ffmpeg_tests/black.mp4")
# get_task_status("688cfcc1a2418328058e280a")