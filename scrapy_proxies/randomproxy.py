import os
import random
import logging
from scrapy.exceptions import NotConfigured
from scrapy.downloadermiddlewares.httpproxy import HttpProxyMiddleware
from scrapy.utils.httpobj import urlparse_cached

log = logging.getLogger(__name__)

class RandomProxy(object):

    def __init__(self, crawler):
        auth_encoding = crawler.settings.get('HTTPPROXY_AUTH_ENCODING', 'latin-1')
        randomproxy_pool = crawler.settings.getdict('RANDOMPROXY_POOL', {})

        self.pool = {}
        backup = os.environ.get('HTTP_PROXY')
        try:
            for url in randomproxy_pool:
                os.environ['HTTP_PROXY'] = url
                midware = HttpProxyMiddleware(auth_encoding)
                proxy_type = next(iter(midware.proxies))
                self.pool.setdefault(proxy_type, [])
                self.pool[proxy_type].append(midware)
        finally:
            if backup:
                os.environ['HTTP_PROXY'] = backup

        if not self.pool:
            raise NotConfigured

    @classmethod
    def from_crawler(cls, crawler):
        return cls(crawler)

    def process_request(self, request, spider):
        parsed = urlparse_cached(request)
        scheme = parsed.scheme

        try:
            midware = random.choice(self.pool[scheme])
        except (IndexError, KeyError):
            raise ValueError('No available proxy, cannot proceed')

        log.debug('Using proxy <%s>, %d %s proxies left' % (
            midware.proxies[scheme], len(self.pool[scheme]), scheme))
        midware.process_request(request, spider)

    def process_exception(self, request, exception, spider):
        if 'proxy' not in request.meta:
            return

        err_proxy = request.meta['proxy']
        for scheme in self.pool:
            for midware in self.pool[scheme]:
                creds, proxy = midware.proxies[scheme]
                if err_proxy == proxy:
                    self.pool[scheme].remove(midware)

                    log.warning('Removing failed proxy <%s>, %d %s proxies left' % (
                        proxy, len(self.pool[scheme]), scheme))
