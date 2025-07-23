#!/bin/bash

ffmpeg \
-f lavfi -i color=c=#000000:duration=2:s=1080x720:r=30 \
-f lavfi -i color=c=#ffff80:duration=2:s=1080x720:r=30 \
-f lavfi -i color=c=#000000:duration=6:s=1080x720:r=30 \
-map 0:v -map 1:v -map 2:v \
-c:v libx264 \
2b2g6b.mp4