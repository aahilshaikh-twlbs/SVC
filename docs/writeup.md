# SAGE Development Issues & Problem-Solving Journey

## Problem Origins
- Had a working demo with all requested base features for comparing scenes between 2 similar assets
- Recently discovered that assets don't need to be the same length (still processing this)
- Danger noted certain videos don't work, particularly with larger files - and it crapped itself

## Problem Analysis

### Initial Investigation
- Started with frontend solutions for larger file sizes (to no avail)
- Checked backend - wasn't the issue (TL-embed API handles 2GB vids and/or <2hr content)
- Test videos were <1GB and <1hr, so backend wasn't the bottleneck

### Platform Limitations

#### Vercel is... challenging
- Discovered Vercel's upload limits: 4.5MB (free), 1GB (pro)
- Attempted various frontend/backend workarounds
- Realized this approach wasn't going anywhere

#### DigitalOcean is miserably hard to manage

**Single Server Issues**
- Attempted to entirely scrap Vercel, host frontend on existing backend server
- Had to spend time avoiding IP issues and rewriting routes
- BOOM: **CORS fuck-you** - had no idea what was going on with the CORS stuff

**Multi-Server Setup**
- Created separate droplets for frontend/backend in DO SAGE project
- Constant stream of new errors and screw-ups
- More CORS issues and no-nos
- Terribly hard to manage since SSHing into each server to modify components separately was really hard

**Back to Vercel**
- Decided to go back to Vercel as the only viable option
- Focused on finding workarounds for the 1GB limit

### Incorrect Chunking Approach
- Thought I could implement chunking to fix the 1GB issues
- Implemented it wrong (explained further down)
- Wasn't able to chunk because I thought it had to upload first to get access to the video, then chunk the whole thing
- Realized the problem: we can't upload it since Vercel is where we're uploading from

### Technical Discussion with Kingston
**Key Points from Slack Discussion:**
- TL API generates embeddings at fixed clip lengths (e.g., 10 seconds)
- Cannot retrieve embeddings at different clip lengths (e.g., 2 seconds)
- Only option: re-embed video directly for desired clip length
- Kingston suggested using TL to pull indexed video links for video_url param
- Counter-argument: treating TL like Google Drive/S3 storage
- Conclusion: Better to handle videos locally

**File Size Bottleneck Discussion:**
- Problem isn't upload destination (S3 vs direct API)
- Bottleneck is Vercel's 4.5MB/1GB limits
- Need 2GB functionality to maximize API usage
- Alternative: set limit to 1GB to work with Vercel

### Stuck and crying... but
- We've determined the problem and know what it is, just not how to fix it
- Vercel is the bottleneck here and I've got no clue how to get around it

## Solution Development

### Breakthrough with Mohit
- Solution came up today in discussion with good buddy Mohit and I pieced the rest together

### Video Upload Process Understanding
- Video upload = stream of bytes ready for backend transmission
- What if on the upload modal you chunk the bytes and send it through to the backend that way? No Vercel issues

### Chunking but right this time
- You might be thinking "oh no, you already tried chunking"
- I was on the wrong path - we want to chunk the file into byte files BEFORE they get really "uploaded" to frontend (Vercel)
- Instead of uploading and chunking, we chunk before uploading

## Proposed Architecture

### Goals
- More modularized frontend
- Better code pipelines for debugging

### Upload Pipeline
**Default Configuration**
- Pro plan Vercel: 1GB upload limit

**Fat Checker**
- Checks how fat a given file is (filesize) - will be used in multiple places
- First check input file sizes for both videos

**Sub-Upload Pipeline: Frontend to Backend**
1. Upload modal takes incoming bytestream and saves to byte file
2. Save until content reaches 1GB, then save as `video_A/B_chunk_X`
3. Immediately send chunk to backend to save locally in a folder, then delete chunk from frontend
4. Next set of incoming bytes (should start saving after deletion of chunkA since Vercel browser/localstore is limited)
5. Save to video_chunk file, repeat until whole video chunked into bytestream objects

**Backend Processing**
- Concatenate all byte chunks into single bytefile via Python file concat with `wb+`
- Rename file to MP4
- If video >7200s or >2GB: chunk into acceptable segments
- Call embed API multiple times
- Concatenate all embeds from one video into single dict object

### Embed Pipeline
- Call embed API `x_chunks` times
- Concatenate all embeds from one video into single dict object
- Pass to comparison logic

### Comparison Pipeline
- Wait for complete dict/JSON objects from both videos
- Run comparison
- Save to RAM/cache for threshold adjustments and reruns