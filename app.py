import logging
import subprocess
import re

from multiprocessing import Process, Array

from aiohttp import web, request as send_request


HOST = 'localhost'
PORT = 9999

PROXY_SERVER_HOST = 'serveo.net'


log = logging.getLogger(__name__)
log.addHandler(logging.StreamHandler())
log.setLevel(logging.DEBUG)

SSH_COMMUNICATION_PIPE = 'ssh_communication_pipe'

PROXY_LINK_PARAM = 'proxy_link'
PROXY_LINK_TEMPLATE = f'http(s|)?:\/\/.*.{PROXY_SERVER_HOST}'
START_FORWARDING_TEXT_TEMPLATE = f'.*Forwarding HTTP traffic from (?P<{PROXY_LINK_PARAM}>{PROXY_LINK_TEMPLATE})'
START_FORWARDING_TEXT_REGEX = re.compile(START_FORWARDING_TEXT_TEMPLATE)


ALLOWED_REL_URLS = {}


async def redirect_payment_url(request):
    transition_url = request.match_info['transition_url']

    if transition_url not in ALLOWED_REL_URLS:
        return web.json_response({'code': 403})
    else:
        url_to_transit = f'{ALLOWED_REL_URLS[transition_url]}/{transition_url}'
        params = dict(request.query)
        data = dict(await request.post())
        async with send_request(request.method, url_to_transit, params=params, data=data) as resp:
            text = await resp.text()
            log.info(f'Got response: {text}')
            return web.json_response({'code': 200})


async def get_host_for_payment(request):
    url_to_allow = request.match_info['url_to_allow']
    hostname_for_transition = request.match_info['hostname_for_transition']
    protocol = request.match_info['protocol']

    ALLOWED_REL_URLS[url_to_allow] = f'{protocol}://{hostname_for_transition}'

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

    app.router.add_get(
        r'/proxy_link/{protocol}/{hostname_for_transition}/{url_to_allow:.*}',
        get_host_for_payment,
    )

    app.router.add_get(r'/{transition_url:.*}', redirect_payment_url)

    log.debug('Application configured.')

    web.run_app(
        app,
        host=HOST,
        port=PORT,
    )


def main():
    proxy_link = Array('c', 50)

    port_forwarding_proc = Process(target=run_port_forwarding, args=(proxy_link,))
    port_forwarding_proc.start()

    app_proc = Process(target=run_app, args=(proxy_link,))
    app_proc.start()


if __name__ == '__main__':
    main()
