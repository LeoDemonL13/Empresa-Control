import os

if os.environ.get('SOCKETIO_ASYNC_MODE') == 'gevent':
    from gevent import monkey
    monkey.patch_all()

from app import create_app, socketio

app = create_app()

if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=5000, debug=False, allow_unsafe_werkzeug=True)
