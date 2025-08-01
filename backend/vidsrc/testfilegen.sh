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

#b3d64b - 422
#954bd6 - 609
#d66e4b - 466
#d64b87 - 542
#4b4dd6 - 360
#000000 - 433
#808080 - 337
#4bd6af - 434

ffmpeg \
-f lavfi -i color=c=#b3d64b:duration=3:s=1080x720:r=24 \
-f lavfi -i color=c=#000000:duration=3:s=1080x720:r=24 \
-f lavfi -i color=c=#954bd6:duration=3:s=1080x720:r=24 \
-f lavfi -i color=c=#d66e4b:duration=3:s=1080x720:r=24 \
-f lavfi -i color=c=#000000:duration=3:s=1080x720:r=24 \
-f lavfi -i color=c=#d64b87:duration=3:s=1080x720:r=24 \
-f lavfi -i color=c=#4b4dd6:duration=3:s=1080x720:r=24 \
-f lavfi -i color=c=#000000:duration=3:s=1080x720:r=24 \
-f lavfi -i color=c=#808080:duration=3:s=1080x720:r=24 \
-f lavfi -i color=c=#4bd6af:duration=3:s=1080x720:r=24 \
-filter_complex "[0:v][1:v][2:v][3:v][4:v][5:v][6:v][7:v][8:v][9:v]concat=n=10:v=1:a=0[out]" \
-map "[out]" \
-c:v libx264 \
colors.mp4 && \
ffmpeg \
-f lavfi -i color=c=#000000:duration=30:s=1080x720:r=30 \
-c:v libx264 \
black.mp4