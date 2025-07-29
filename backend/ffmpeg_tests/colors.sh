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

#b3d64b - 843
#954bd6 - 1217
#d66e4b - 932
#d64b87 - 1084
#4b4dd6 - 719
#000000 - 865
#808080 - 673
#4bd6af - 867

ffmpeg \
-f lavfi -i color=c=#b3d64b:duration=843:s=1080x720:r=24 \
-f lavfi -i color=c=#954bd6:duration=1217:s=1080x720:r=24 \
-f lavfi -i color=c=#d66e4b:duration=932:s=1080x720:r=24 \
-f lavfi -i color=c=#d64b87:duration=1084:s=1080x720:r=24 \
-f lavfi -i color=c=#4b4dd6:duration=719:s=1080x720:r=24 \
-f lavfi -i color=c=#000000:duration=865:s=1080x720:r=24 \
-f lavfi -i color=c=#808080:duration=673:s=1080x720:r=24 \
-f lavfi -i color=c=#4bd6af:duration=867:s=1080x720:r=24 \
-filter_complex "[0:v][1:v][2:v][3:v][4:v][5:v][6:v][7:v]concat=n=8:v=1:a=0[out]" \
-map "[out]" \
-c:v libx264 \
ffmpeg_movie_color.mp4