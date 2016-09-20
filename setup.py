#!/usr/bin/env python
from distutils.core import setup

setup(
    name='scrapy-proxies',
    version='0.3',
    description='Scrapy Proxies: random proxy middleware for Scrapy',
    author='Aivars Kalvans',
    author_email='aivars.kalvans@gmail.com',
    url='https://github.com/aivarsk/scrapy-proxies',
    packages=['scrapy_proxies'],
    install_requires=['Scrapy'],
)
