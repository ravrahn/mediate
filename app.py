#!/usr/local/bin/python3
import os, math
from io import BytesIO
import pychromecast
from natsort import natsorted
from sh import ffmpeg # required command line tool
from flask import Flask, abort, request, render_template, Response, send_file

raw_url = 'http://192.168.100.102:5120'
# Note: If this is set to a router-level custom hostname
# casting will fail silently.
# This is because the Chromecast uses the 8.8.8.8 DNS and doesn't
# tell you if it can't resolve the host.

class CastManager(object):
    def __init__(self):
        self.chromecast = None
        self.mc = None
        self.now_playing = None

    def connect(self, chromecast):
        if self.chromecast is None or self.chromecast.device.friendly_name != chromecast:
            self.disconnect()
            self.chromecast = pychromecast.get_chromecast(friendly_name=chromecast)
            self.chromecast.wait()
            self.mc = self.chromecast.media_controller

    def cast(self, path):
        self.mc.play_media(raw_url + '/' + path, 'video/mp4')
        self.now_playing = path

    def get_chromecasts(self):
        return pychromecast.get_chromecasts_as_dict().keys()

    def is_playing(self):
        if self.mc is not None:
            return self.mc.status.player_is_playing and not self.mc.status.player_is_paused
        else:
            return False

    def get_position(self):
        if self.mc is not None:
            return self.mc.status.current_time

    def get_duration(self):
        if self.mc is not None:
            print(self.mc.status.duration)
            return self.mc.status.duration

    def play(self):
        if self.mc is not None and self.mc.status.supports_pause:
            self.mc.play()

    def pause(self):
        if self.mc is not None and self.mc.status.supports_pause:
            self.mc.pause()

    def seek(self, position):
        if self.mc is not None and self.mc.status.supports_seek:
            self.mc.seek(position)

    def stop(self):
        if self.mc is not None:
            self.mc.stop()
            self.now_playing = None

    def disconnect(self):
        if self.mc is not None:
            self.stop()
            self.mc = None
        if self.chromecast is not None:
            self.chromecast.quit_app()
            self.chromecast.disconnect()
            self.chromecast = None

cm = CastManager()

base_dir = '/mnt/storage/'

app = Flask(__name__)
app.jinja_env.globals.update(raw_url=raw_url)

@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def ls(path):
    full_path = base_dir + path
    if os.path.isdir(full_path):
        # show index
        contents = os.listdir(full_path)
        contents = natsorted(contents) # proper alphanumeric ordering is important here
        if path != '':
            path = '/' + path
        contents = [{'name': name, 'isdir': os.path.isdir(full_path + '/' + name)} for name in contents if (name[-3:] in ['mp4', 'mkv'] or os.path.isdir(full_path + '/' + name)) and name[0] != '.']
        has_folders = False
        has_videos = False
        for file in contents:
            if file['isdir']:
                has_folders = True
            else:
                has_videos = True
        return render_template('index.html',
                                contents=contents,
                                path=path,
                                path_arr=path.split('/'),
                                has_folders=has_folders,
                                has_videos=has_videos,
                                casts=cm.get_chromecasts())
    elif os.path.isfile(full_path):
        to_cast = request.args.get('cast')
        if to_cast == 'yes':
            device = request.args.get('device')
            # cast it
            cm.connect(device)
            cm.cast(path)
            return render_template('cast.html',
                                    file=path.split('/')[-1],
                                    path=path,
                                    path_arr=path.split('/'),
                                    device=device)
        else:
            # don't cast it
            return render_template('watch.html',
                                    file=path.split('/')[-1],
                                    path=path,
                                    path_arr=path.split('/'))
    else:
        return abort(404)


@app.route('/playpause')
def playpause():
    if cm.is_playing():
        cm.pause()
        return 'pause'
    else:
        cm.play()
        return 'play'

@app.route('/currenttime')
def time():
    return str(cm.get_position())

@app.route('/duration')
def duration():
    return str(math.floor(cm.get_duration()))

@app.route('/seek')
def seek():
    try:
        time = int(request.args.get('time'))
        cm.seek(time)
        return str(time)
    except:
        return abort(400)

@app.route('/stop')
def stop():
    cm.stop()
    return 'stop'


@app.route('/<path:path>.jpg')
def thumb(path):
    full_path = base_dir + path
    if os.path.isfile(full_path) and not os.path.isdir(full_path):
        if os.path.isfile(full_path + '.jpg'):
            with open(full_path + '.jpg', 'rb') as f:
                img = BytesIO(f.read())
            return send_file(img, mimetype='image/jpeg')
        else:
            img = ffmpeg('-ss', '00:02:00', '-i', full_path, '-frames:v', '1', '-f', 'image2', '-')
            with open(full_path + '.jpg', 'w+b') as f:
                f.write(img.stdout)
            return send_file(BytesIO(img.stdout), mimetype='image/jpeg')
    else:
        return abort(404)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0');
