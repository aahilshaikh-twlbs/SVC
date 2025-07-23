ffmpeg \
-f lavfi -i color=c=#000000:duration=10:s=1080x720:r=30 \
-c:v libx264 \
10b.mp4

# refer to 2b2g6b.sh for what all this means