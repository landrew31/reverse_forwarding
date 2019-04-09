import argparse
import logging
import logging.config

import json
import subprocess
import re

import yaml
from urllib.parse import urlparse

from multiprocessing import Process, Array

from aiohttp import web, request as send_request


HOST = 'localhost'
PORT = 9090

PROXY_SERVER_HOST = 'serveo.net'


config = yaml.load(open('config.yml'))
logging.config.dictConfig(config['logging'])
log = logging.getLogger('app')

SSH_COMMUNICATION_PIPE = 'ssh_communication_pipe'

PROXY_LINK_PARAM = 'proxy_link'
PROXY_LINK_TEMPLATE = f'http(s|)?:\/\/.*.{PROXY_SERVER_HOST}'
START_FORWARDING_TEXT_TEMPLATE = f'.*Forwarding HTTP traffic from (?P<{PROXY_LINK_PARAM}>{PROXY_LINK_TEMPLATE})'
START_FORWARDING_TEXT_REGEX = re.compile(START_FORWARDING_TEXT_TEMPLATE)


ALLOWED_REL_URLS = {}


async def redirect(request):
    transition_url = f'/{request.match_info["transition_url"]}'

    if transition_url not in ALLOWED_REL_URLS:
        return web.json_response({'code': 403})
    else:
        url_to_transit = f'{ALLOWED_REL_URLS[transition_url]}{transition_url}'
        log.info(f'Is going to redirect to {url_to_transit}')
        params = dict(request.query)
        data = dict(await request.post())
        async with send_request(request.method, url_to_transit, params=params, data=data) as resp:
            text = await resp.text()
            log.info(f'Got response: {text}')
            try:
                res = json.loads(text)
                return web.json_response(res)
            except Exception:
                return web.Response(body=text, content_type='text/html')


async def proxify_link(request):
    data = await request.json()
    url = data.get('url')
    if not url:
        raise Exception('Not url in request.')
    parsed = urlparse(url)
    origin = f'{parsed.scheme}://{parsed.netloc}'
    ALLOWED_REL_URLS[parsed.path] = origin
    log.info(f'Allowed reverse forwarding for {origin}{parsed.path}')

    proxy_link = request.app[PROXY_LINK_PARAM].value.decode('utf-8')

    return web.json_response({
        'code': 200,
        'proxy_hostname': proxy_link,
    })


def run_port_forwarding(proxy_link, current_port=PORT):
    log.debug('Try to run port forwarding.')
    command_params = ['ssh', '-R', f'80:localhost:{current_port}', PROXY_SERVER_HOST]
    with subprocess.Popen(command_params, stdout=subprocess.PIPE, stderr=subprocess.PIPE) as ssh_tunnel:
        log.debug('Run port forwarding.')
        output = str(ssh_tunnel.stdout.readline())
        matched = START_FORWARDING_TEXT_REGEX.match(output)
        if matched:
            _link = matched.groupdict()[PROXY_LINK_PARAM]
            log.info(f'Got link: {_link}')
            proxy_link.value = bytes(_link, 'utf-8')


def run_app(proxy_link):
    log.debug('Try to run application.')
    app = web.Application()

    app[PROXY_LINK_PARAM] = proxy_link

    app.router.add_post('/proxify_link', proxify_link)

    app.router.add_get(r'/{transition_url:.*}', redirect)
    app.router.add_post(r'/{transition_url:.*}', redirect)

    log.debug('Application configured.')

    web.run_app(
        app,
        host=HOST,
        port=PORT,
    )


def main():
    parser = argparse.ArgumentParser(description='''
        Accept requests from remote services
        on your local machine during debugging
    ''')
    parser.add_argument('--url', metavar='URL', type=str,
                        help='External URL, if already obtained',
                        default=None, required=False)
    args = parser.parse_args()

    proxy_link = Array('c', 50)

    if args.url:
        proxy_link.value = bytes(args.url, 'utf-8')
    else:
        port_forwarding_proc = Process(target=run_port_forwarding,
                                       args=(proxy_link,))
        port_forwarding_proc.start()

    app_proc = Process(target=run_app, args=(proxy_link,))
    app_proc.start()


if __name__ == '__main__':
    main()
