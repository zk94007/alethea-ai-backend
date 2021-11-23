import os

from django.core.wsgi import get_wsgi_application
import socketio

from django.contrib.staticfiles.handlers import StaticFilesHandler

from server.socket_script import sio

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "server.settings")
django_app = StaticFilesHandler(get_wsgi_application())

application = socketio.Middleware(sio, wsgi_app=django_app, socketio_path='socket.io')

import eventlet
import eventlet.wsgi
eventlet.wsgi.server(eventlet.listen(('', 8001)), application)
