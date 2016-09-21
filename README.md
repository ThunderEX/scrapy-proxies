Random proxy middleware for Scrapy (http://scrapy.org/)
=======================================================

Processes Scrapy requests using a random proxy from list to avoid IP ban and
improve crawling speed.

Get your proxy list from sites like http://proxylist.hidemyass.com/ (copy-paste into text file
and reformat to http://host:port format)

Install
--------

The quick way:

    pip install git+https://github.com/ThunderEX/scrapy-proxies.git@master

Or checkout the source and run

    python setup.py install


settings.py
-----------

    # Retry many times since proxies often fail
    RETRY_TIMES = 10
    # Retry on most error codes since proxies fail for different reasons
    RETRY_HTTP_CODES = [500, 503, 504, 400, 403, 404, 408]
    # Priority better > 500 to override built-in HttpProxyMiddleware
    DOWNLOADER_MIDDLEWARES = {
        'scrapy_proxies.RandomProxy': 543,
    }

    # Proxy list containing entries like
    # http://host1:port
    # http://username:password@host2:port
    # http://host3:port
    # ...
    PROXY_LIST = '/path/to/proxy/list.txt'


For older versions of Scrapy (before 1.0.0) you have to use
scrapy.contrib.downloadermiddleware.retry.RetryMiddleware and
scrapy.contrib.downloadermiddleware.httpproxy.HttpProxyMiddleware
middlewares instead.


Your spider
-----------

In each callback ensure that proxy /really/ returned your target page by
checking for site logo or some other significant element.
If not - retry request with dont_filter=True

    if not hxs.select('//get/site/logo'):
        yield Request(url=response.url, dont_filter=True)
