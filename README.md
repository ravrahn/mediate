# Mediate
Web app for casting videos from a local media server (that runs unix).

## Requirements

### Python Libraries
 - flask
 - pychromecast
 - sh
 - natsort

### Command line tools
 - ffmpeg (to generate thumbnails)

### Other
 - A web server such as nginx, to stream the video files.
 
## Setup
 - Download Mediate on your media server.
 - Configure the web server to serve video files using your server's directory structure, on an unused port (not 80).
 - Change the base_dir in mediate.py to the root your file server serves from.
 - Change the raw_url in mediate.py to <server ip>:<port>.
 - Configure the web server to serve mediate with wsgi on port 80.
