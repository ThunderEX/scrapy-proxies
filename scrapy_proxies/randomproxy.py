import re
import random
import base64
import logging

log = logging.getLogger('scrapy.proxies')

class RandomProxy(object):
    def __init__(self, settings):
        proxy_list = settings.get('PROXY_LIST')

        if proxy_list is None:
            raise KeyError('PROXY_LIST setting is missing')

        fin = open(proxy_list)

        self.proxies = {}
        for line in fin.readlines():
            parts = re.match('(\w+://)(\w+:\w+@)?(.+)', line.strip())
            if not parts:
                continue

            # Cut trailing @
            if parts.group(2):
                user_pass = parts.group(2)[:-1]
            else:
                user_pass = ''

            self.proxies[parts.group(1) + parts.group(3)] = user_pass

        fin.close()

    @classmethod
    def from_crawler(cls, crawler):
        return cls(crawler.settings)

    def process_request(self, request, spider):
        # Don't overwrite with a random one (server-side state for IP)
        if 'proxy' in request.meta:
            return

        if len(self.proxies) == 0:
            raise ValueError('All proxies are unusable, cannot proceed')

        proxy_address = random.choice(list(self.proxies.keys()))
        proxy_user_pass = self.proxies[proxy_address]

        request.meta['proxy'] = proxy_address
        if proxy_user_pass:
            basic_auth = 'Basic ' + base64.encodestring(proxy_user_pass)
            request.headers['Proxy-Authorization'] = basic_auth
        log.debug('Using proxy <%s>, %d proxies left' % (
                    proxy_address, len(self.proxies)))

    def process_exception(self, request, exception, spider):
        if 'proxy' not in request.meta:
            return

        proxy = request.meta['proxy']
        try:
            del self.proxies[proxy]
        except KeyError:
            pass

        log.info('Removing failed proxy <%s>, %d proxies left' % (
                    proxy, len(self.proxies)))
