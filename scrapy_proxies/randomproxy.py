import os
import random
import logging
from scrapy import Request
from scrapy.exceptions import NotConfigured
from scrapy.downloadermiddlewares.httpproxy import HttpProxyMiddleware
from scrapy.downloadermiddlewares.retry import RetryMiddleware
from scrapy.utils.httpobj import urlparse_cached

logger = logging.getLogger(__name__)

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

        self.retry_midware = RetryMiddleware(crawler.settings)
        self.discarded_proxies = []

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

        # retry request may have a obsolete proxy
        if request.meta.get('proxy') in self.discarded_proxies:
            del request.meta['proxy']
        midware.process_request(request, spider)
        logger.debug('Using proxy <%s>, %d %s proxies left' % (
            midware.proxies[scheme], len(self.pool[scheme]), scheme))

    def process_response(self, request, response, spider):
        # if retry middleware decides to retry, alter proxy
        ret = self.retry_midware.process_response(request, response, spider)
        if isinstance(ret, Request):
            self.alter_proxy(request)
        return response

    def process_exception(self, request, exception, spider):
        self.alter_proxy(request)

    def alter_proxy(self, request):
        if 'proxy' not in request.meta:
            return

        err_proxy = request.meta['proxy']
        for scheme in self.pool:
            for midware in self.pool[scheme]:
                creds, proxy = midware.proxies[scheme]
                if err_proxy == proxy:
                    self.pool[scheme].remove(midware)
                    self.discarded_proxies.append(err_proxy)

                    logger.warning('Removing failed proxy <%s>, %d %s proxies left' % (
                        proxy, len(self.pool[scheme]), scheme))
