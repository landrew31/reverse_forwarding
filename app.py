import logging

import subprocess

from multiprocessing import Process
from aiohttp import web


HOST = 'localhost'
PORT = 9090

PROXY_SERVER_HOST = 'serveo.net'


log = logging.getLogger(__name__)
log.addHandler(logging.StreamHandler())
log.setLevel(logging.DEBUG)


async def redirect_payment_url(request):
    return web.json_response({
        'status': 'OK',
        'code': 200,
    })


async def get_host_for_payment(request):
    pass


def run_port_forwarding(current_port=PORT):
    log.debug('Try to run port forwarding.')
    with subprocess.Popen(
        [
            'ssh',
            '-R',
            '80:localhost:%s' % current_port,
            PROXY_SERVER_HOST,
        ],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    ) as ssh:
        log.debug('Run port forwarding.')
        print(ssh.stdout.readline())


def run_app():
    log.debug('Try to run application.')
    app = web.Application()

    app.router.add_get('/', redirect_payment_url)
    app.router.add_get('/response_url/', get_host_for_payment)

    log.debug('Application configured.')

    web.run_app(
        app,
        host=HOST,
        port=PORT,
    )


def main():
    port_forwarding_proc = Process(target=run_port_forwarding)
    port_forwarding_proc.start()

    app_proc = Process(target=run_app)
    app_proc.start()


if __name__ == '__main__':
    main()
