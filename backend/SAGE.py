### BARE MINIMUM OF ALL FILES COMBINED INTO ONE CHILD THING

from twelvelabs import TwelveLabs
from twelvelabs.models.embed import EmbeddingsTask, SegmentEmbedding
from twelvelabs.models.task import Task
import os
from dotenv import load_dotenv
import threading
from typing import List

load_dotenv()

tl_client = TwelveLabs(api_key=os.environ['TWELVELABS_API_KEY'])

##### FRONTEND

# the frontend overall (landing and analysis) will be comprised of a nextjs
#       using nextjs react server components to have basic authorization for the twelvelabs key
#               when user enters key on frontend it encrypts and sends to backend to decrypt and verify its a valid key and store in a sqlite db in backend
#       will also be written in typescript
#       will be minimal and easy to use
#       the git repo will be deployed on vercel

    # for our landing page: --V
    # we need some small config button to add in the twelvelabs API key
    # a cool visualizer that populates with all the indexes based on a key's access 
    #       (i.e. one key has access to whatever indexes are on that account)
    #       in the index visualizer also an option to make a new index for that account 
    #       option to select index
    # a cool video visualizer when an index is selected which populates with all the videos (with a thumbnail) of all videos in that index
    #       in the video visualizer an option to upload a new video from local or youtube link (uses then yt dlp to get the video and upload) 
    #               when a new video (local/yt) uploaded imediately index with twelvelabs platform.
    #       option to (in the video visualizer) to select 2 videos for our semantic comparison
    # also an option to skip the whole GUI process for index selection and video selection and just give an index ID and video ID(s) which work with that key
    # a button to run the comparison which only works when 2 videos are uploaded

    # for our analysis page: --V
    # it will be a new page on the same site where it redirects when semantic comparison is completed
    # the main space of the video will be taken by a video player
    #       the video player has many options, it can play video A or video B, or both side by side
    #               if playing individual videos the track scrollbar for the video will have highlighted areas where there are semantic diffs
    #               if playing side by side then the track scrollbar in both videos next to one another will have diffs highlighted on the track
    # on the left of the video player there'll be a list of all the diffs (as time ranged segments as a result of our main semantic diff checker)
    # an option to export a generated report as pdf or as OTIO format


##### BACKEND

# the backend will be comprised of existing twelvelabs functions to work
# will use core functionalities
#       1. make a new index (ONLY MARENGO BECACUSE EMBED STUFF ONLY MARENGO 2.7)
#       2. retrieve list of all indexes
#       3. list all videos in an index
#       4. upload video to an index
#       5. retrieve embeds from videos in an index
# all the index id and video id stuff has to be authorized by the tlk

####### ALL INDEX-RELATED FUNCTIONS WE NEED
def create_index():
    """
    This method creates a new index based on the provided parameters.
    Parameters

    Name	Type	Required	Description
    name	str	Yes	The name of the new index. (REQUIRED)
    options	List[types.IndexModel]	Yes	A list of IndexModel objects specifying the video understanding models and the model options you want to enable for this index. Each object is a dictionary with two keys: name and options.
    addons	Optional[List[str]]	No	A list specifying which add-ons should be enabled.
    **kwargs	dict	No	Additional keyword arguments for the request.
    Return value: Returns a models.Index object representing the newly created index.

    REMEMBER THAT WE'RE ONLY USING MARENGO 2.7 FOR ALL INDEXES FOR THIS APP

    """

    models = [
            {
            "name": "marengo2.7",
            "options": ["visual", "audio"]
            },

        ]
    created_index = tl_client.index.create(
        name="<YOUR_INDEX_NAME>",
        models=models,
        addons=["thumbnail"]
    )
    print(f"ID: {created_index.id}")
    print(f"Name: {created_index.name}")
    print("Models:")
    for i, model in enumerate(created_index.models, 1):
        print(f"  Model {i}:")
        print(f"    Name: {model.name}")
        print(f"    Options: {model.options}")
    print(f"Video count: {created_index.video_count}")
    print(f"Total duration: {created_index.total_duration} seconds")
    print(f"created At: {created_index.created_at}")
    if created_index.updated_at:
        print(f"Updated at: {created_index.updated_at}")
def list_indexes_direct_pagination():

    """
    The list method retrieves a paginated list of indexes based on the provided parameters. 
    Choose this method mainly when the total number of items is manageable or you must fetch a single page of results. 
    By default, the platform returns your indexes sorted by creation date, with the newest at the top of the list.
    
    Parameters

    Name	Type	Required	Description
    id	Optional[str]	No	Filter by the unique identifier of an index. (OPTIONAL, IF USER PROVIDES THEN YOU REFER TO THAT SPECIFIC INDEX OTHERWISE SHOW ALL RESULTS AND LET THEM PICK)
    name	Optional[str]	No	Filter by the name of an index. (DO NOT ADD THIS ITS LATENCY FOR NO REASON)
    model_options	Optional [Literal["visual", "audio"]] = None	No	Filter by model options. (WE DONT NEED THIS PARAM)
    model_family	Optional[Literal["marengo", "pegasus"]] = None	No	Filter by model family. (WE DONT NEED THIS PARAM; ONLY USING MARENGO-INDEXES ANYWAY SO SPECIFY MARENGO IN THE CALL DONT LET USER DECIDE)
    page	Optional[int]	No	Page number for pagination. Defaults to 1. (NO PAGINATION REQUIRED REALISTICALLY SINCE WE'RE DISPLAYING THIS OURSELF ON OUR UI)
    page_limit	Optional[int]	No	Number of items per page. Defaults to 10. (CHECK PAGINATION OPTIONS)
    sort_by	Optional[str]	No	Field to sort by (“created_at” or “updated_at”). Defaults to “created_at”. (WE DONT NEED THIS PARAM)
    sort_option	Optional[str]	No	Sort order (“asc” or “desc”). Defaults to “desc”. (PICK EITHER)
    created_at	Optional[Union[str, Dict[str, str]]] = None	No	Filter by creation date. This parameter can be a string or a dictionary for range queries. (DONT NEED THIS PARAM)
    updated_at	Optional[Union[str, Dict[str, str]]] = None	No	Filter by update date. This parameter can be a string or a dictionary for range queries. (DONT NEED THIS PARAM)
    **kwargs	dict	No	Additional keyword arguments for the request. (GENERALLY NONE)
    
    
    WE AREN'T USING ALL THESE OPTIONS, WE JUST WANT TO SHOW ALL INDEXES WHICH ARE MARENGO MODEL FAMILY THAT SHOULD BE OUR ONLY PARAM, ALONG WITH ASC/DESC
    MAYBE IMPLEMENT THE SPECIFIC INDEX ID SEARCH HERE INSTEAD OF THE RETRIEVE FUNCTION UP TO YOU


    """

    indexes = tl_client.index.list(
        id="<YOUR_INDEX_ID>",
        name="<YOUR_INDEX_NAME>",
        page=1,
        page_limit=5,
        model_options=["visual", "audio"],
        model_family="marengo",
        sort_by = "updated_at",
        sort_option="asc",
        created_at="2024-09-17T07:53:46.365Z",
        updated_at="2024-09-17T07:53:46.365Z"
    )
    for index in indexes:
        print(f"ID: {index.id}")
        print(f"  Name: {index.name}")
        print("  Models:")
        for i, model in enumerate(index.models, 1):
            print(f"    Model {i}:")
            print(f"      Name: {model.name}")
            print(f"      Options: {model.options}")
        print(f"  Video count: {index.video_count}")
        print(f"  Total duration: {index.total_duration} seconds")
        print(f"  Created at: {index.created_at}")
        if index.updated_at:
            print(f"  Updated at: {index.updated_at}")
def rename_index():
    """
    Literally rename index use this perhaps"""
    tl_client.index.update(id="<INDEX_ID>", name="<NEW_INDEX_NAME>")

def delete_index():
    """"Pretty damn simple and it deletes an index"""
    tl_client.index.delete(id="<YOUR_INDEX_ID>")

####### ALL VIDEO-RELATED FUNCTIONS WE NEED
def upload_video():
    """
    This method creates a new video indexing (not to be confused with indexes where the videos are stored this is processing) task that uploads and indexes a video.
    
    Parameters:

    Name	Type	Required	Description
    index_id	str	Yes	The unique identifier of the index to which the video will be uploaded. (THIS IS GOTTEN WHEN YOU SELECT THE INDEX; YOU CAN ONLY UPLOAD NEW VIDEO WHEN INDEX IS SELECTED
    file	Union[str, BinaryIO, None]	No	Path to the video file or a file-like object. (THIS WILL BE A LOCAL FILEPATH SENT TO THIS FUNCTION CALL)
    url	Optional[str]	No	The publicly accessible URL of the video you want to upload. (YT LINK PERHAPS)
    enable_video_stream	Optional[str]	No	Indicates if the platform stores the video for streaming. (NOT REQUIRED)
    **kwargs	dict	No	Additional keyword arguments for the request. (GENERALLY NONE)
    """
    task = tl_client.task.create(
        index_id="<YOUR_INDEX_ID>",
        file="<YOUR_FILE_PATH>"
    )
    print(f"Task id={task.id}")
    # Utility function to print the status of a video indexing task
    def on_task_update(task: Task):
        print(f"  Status={task.status}")
    task.wait_for_done(sleep_interval=5, callback=on_task_update)
    if task.status != "ready":
        raise RuntimeError(f"Indexing failed with status {task.status}")
    print(f"Video ID: {task.video_id}")
def list_videos_direct_pagination():
    """
    This method returns a paginated list of the videos in the specified index based on the provided parameters.
    Choose this method mainly when the total number of items is manageable, or you must fetch a single page of results.
    By default, the platform returns your videos sorted by their upload date, with the newest at the top of the list.

    Parameters:

    Name	Type	Required	Description
    index_id	str	Yes	The unique identifier of the index for which the API will retrieve the videos. (SHOULD BE NON-CHANGABLE BY USER, SET TO THE CURRENT INDEX WHICH YOU'RE IN, THIS LISTS ALL VIDEOS IN THE SELECTED INDEX)
    id	Optional[str]	No	Filter by the unique identifier of a video. (ALLOWED, USER CAN SELECT 2 VIDEOS SO 1 ID SLOT AND YOU HIT CONFIRM THEN ONE VIDEO IN THAT INDEX IS SELECTED (HIGHLIGHTED OR WHATEVER))
    filename	Optional[str]	No	Filter by the name of the video file. (DONT NEED THIS PARAM)
    size	Optional[Union[int, Dict[str, int]]]	No	Filter by the size of the video file. This parameter can be an integer or a dictionary for range queries. (DONT NEED THIS PARAM)
    width	Optional[Union[int, Dict[str, int]]]	No	Filter by the width of the video. This parameter can be an integer or a dictionary for range queries.(DONT NEED THIS PARAM)
    height	Optional[Union[int, Dict[str, int]]]	No	Filter by the height of the video. This parameter can be an integer or a dictionary for range queries.(DONT NEED THIS PARAM)
    duration	Optional[Union[int, Dict[str, int]]]	No	Filter by the duration of the video. This parameter can be an integer or a dictionary for range queries.(DONT NEED THIS PARAM)
    fps	Optional[Union[int, Dict[str, int]]]	No	Filter by the number frames per second. This parameter can be an integer or a dictionary for range queries.(DONT NEED THIS PARAM)
    user_metadata	Optional[Dict[str, Any]]	No	Filter by user metadata.(DONT NEED THIS PARAM)
    created_at	Optional[Union[str, Dict[str, str]]]	No	Filter by the creation date. This parameter can be a string or a dictionary for range queries.(DONT NEED THIS PARAM)
    updated_at	Optional[Union[str, Dict[str, str]]]	No	Filter by the last update date. This parameter can be a string or a dictionary for range queries.(DONT NEED THIS PARAM)
    page	Optional[int]	No	Page number for pagination.(DONT NEED THIS PARAM)
    page_limit	Optional[int]	No	Number of items per page.(DONT NEED THIS PARAM)
    sort_by	Optional[str]	No	Field to sort by.(DONT NEED THIS PARAM)
    sort_option	Optional[str]	No	Sort order. You can specify one of the following values: “asc” or “desc”.(DONT NEED THIS PARAM)
    **kwargs	dict	No	Additional keyword arguments for the request.(DONT NEED THIS PARAM)
    """
    videos = tl_client.index.video.list(
        index_id="<YOUR_INDEX_ID>",
        id="<YOUR_VIDEO_ID>",
        filename="<YOUR_FILENAME>",
        size=1024,
        width=920,
        height=1080,
        duration=100,
        fps=30,
        user_metadata={"category": "nature"},
        user_created_at="2024-09-17T07:53:46.365Z",
        updated_at="2024-09-17T07:53:46.365Z",
        page=1,
        page_limit=5,
        sort_by="created_at",
        sort_option="desc"
    )
    for video in videos:
        print(f"ID: {video.id}")
        print(f"  Created at: {video.created_at}")
        print(f"  Updated at: {video.updated_at}")
        print("   System metadata:")
        print(f"    Filename: {video.system_metadata.filename}")
        print(f"    Duration: {video.system_metadata.duration}")
        print(f"    FPS: {video.system_metadata.fps}")
        print(f"    Width: {video.system_metadata.width}")
        print(f"    Height: {video.system_metadata.height}")
        print(f"  Size: {video.system_metadata.size}")
        if video.user_metadata:
            print("User metadata:")
            for key, value in video.user_metadata.items():
                print(f"{key}: {value}")
        if video.hls:
            print("  HLS:")
            print(f"    Video URL: {video.hls.video_url}")
            print("    Thumbnail URLs:")
            for url in video.hls.thumbnail_urls or []:
                print(f"      {url}")
            print(f"    Status: {video.hls.status}")
            print(f"    Updated At: {video.hls.updated_at}")
        if video.source:
            print("  Source:")
            print(f"    Type: {video.source.type}")
            print(f"    Name: {video.source.name}")
            print(f"    URL: {video.source.url}")
def delete_vid():
    """
    deletes video when index selected
    """
    tl_client.task.delete(index_id="<YOUR_INDEX_ID>",id="<YOUR_VIDEO_ID>")


###### RETRIEVAL COMMANDS
def retrieve_embeds():
    """retrieves embeds based on video id i think
    
    This method retrieves embeddings for a specific video embedding task. Ensure the task status is ready before retrieving your embeddings.
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
def check_if_done(task: EmbeddingsTask):
    """"
    This method waits until a video embedding task is completed by periodically checking its status. If you provide a callback function, it calls the function after each status update with the current task object, allowing you to monitor progress."""
    def on_task_update(task: EmbeddingsTask):
        print(f"  Status={task.status}")
    status = task.wait_for_done(sleep_interval=5, callback=on_task_update)
    print(f"Embedding done: {status}")