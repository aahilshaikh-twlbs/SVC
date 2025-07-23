#!/bin/bash

#### HOW THIS WORKS WITH FFMPEG ####
# 1. call ffmpeg ^
# 2.
    # -f lavfi is libavfilter virtual file source (creates the fake inputs)
    # -i is input deets
    # c is color (in this case we specified hexes)
    # duration is self explanatory
    # s is resolution
    # r is fps
# 3. 
    # this is the concatenation part
    # [0:v][1:v][2:v] == take video streams from inputs 0, 1, and 2
    # v=1 include vid
    # a=0 means no audio
    # tempname the output stream as [out]
# 4. 
    # maps temp-out to final file
# 5. 
    # choose video codec as h.264 for compression
# 6.
    # final output file


ffmpeg \
-f lavfi -i color=c=#000000:duration=2:s=1080x720:r=30 \
-f lavfi -i color=c=#808080:duration=2:s=1080x720:r=30 \
-f lavfi -i color=c=#000000:duration=6:s=1080x720:r=30 \
-filter_complex "[0:v][1:v][2:v]concat=n=3:v=1:a=0[out]" \
-map "[out]" \
-c:v libx264 \
2b2g6b.mp4