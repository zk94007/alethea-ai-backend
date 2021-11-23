# set async_mode to 'threading', 'eventlet', 'gevent' or 'gevent_uwsgi' to
# force a mode else, the best mode is selected automatically from what's
# installed
import socketio
from utils.gpt3_functions import gpt3_vader_api

async_mode = None
thread = None
sio = socketio.Server(async_mode=async_mode, cors_allowed_origins='*')


@sio.event
def gpt_vader(sid, message):
    # sio.emit('my_response', {'data': message['data']}, room=sid)
    response = gpt3_vader_api(message)
    sio.emit("vader_response", response)


@sio.event
def disconnect_request(sid):
    sio.disconnect(sid)


@sio.event
def connect(sid, environ):
    sio.emit('my_response', {'data': 'Connected', 'count': 0}, room=sid)


@sio.event
def disconnect(sid):
    print('Client disconnected')