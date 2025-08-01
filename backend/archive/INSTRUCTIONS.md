ok here's what we gotta do

when we ended up on the whole "index every video and pull embeddings" we ended up recreating a shitty version of tl-playground, lets keep it simple and stick to basics

on our landing;
- a place to enter tl-key
- upload place for 2 local vids
- perhaps it shows both vids thumbnails or some filler stuff
- comparison button
    - ON CLICK --V
    - we then call the required functions from @NEW_FUNCTION_REQS.py and retrieve our newly created embeddings and then store it in to memory; no long term embed storage
    - we also then run the actual comparison logic and take it to the analysis tab
        - we DONT use the app.py, but rather very literally re-write compare_embeds to take our local vids based on the new_function_reqs file-generated-embeds; then use that for comparison, we dont have to use Iconik assets or Pinecone storage at all

analysis page:
- We then try to reimplement the current analysis page; both videos be able to play with a custom track player to show markers where there are diffs, and also a list of segment diffs