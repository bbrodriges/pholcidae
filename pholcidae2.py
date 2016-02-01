# -*- coding: UTF-8 -*-

import re
import mimetypes
import sys

import threading
from threading import Thread, Lock
from hashlib import sha1

if sys.version_info < (3, 0, 0):
    import urlparse as parse
    import urllib2 as request
else:
    from urllib import request
    from urllib import parse

version_info = (2, 0, 2)
__version__ = '.'.join(map(str, version_info))

__author__ = 'bbrodriges'


class Pholcidae(object):

    """" Pholcidae is a small and fast web crawler. """

    DEFAULT_CALLBACK = 'crawl'

    _settings = {
        'follow_redirects': True,
        'append_to_links':  '',
        'valid_links':      ['(.*)'],
        'exclude_links':    [],
        'silent_links':     [],
        'start_page':       '/',
        'domain':           '',
        'stay_in_domain':   True,
        'protocol':         'http://',
        'cookies':          {},
        'headers':          {},
        'precrawl':         None,
        'postcrawl':        None,
        'callbacks':        {},
        'proxy':            {},
        'valid_mimes':      [],
        'threads':          1,
        'with_lock':        True,
        'hashed':           False,
    }

    def extend(self, settings):

        """
        Extends default settings using given settings.
        """

        self._settings.update(settings)

    def start(self):

        """
        Prepares everything and starts
        """

        self.__prepare()

        # trying to call precrawl function
        precrawl = self._settings['precrawl']
        getattr(self, precrawl)() if precrawl else None

        self.__fetch_pages()

        # trying to call postcrawl function
        postcrawl = self._settings['postcrawl']
        getattr(self, postcrawl)() if postcrawl else None

    def crawl(self, response):

        """
        You may override this method in a subclass.
        Use it to get page content and parse it as you want to.
        """

        pass

    def __prepare(self):

        """
        Prepares everything before start.
        """

        # creating new SyncStorage instance
        self._storage = SyncStorage()

        # adding start point into storage
        start_url = '%(protocol)s%(domain)s%(start_page)s' % self._settings
        self._storage.add(start_url.strip(), SyncStorage.PRIORITY_LOW)

        # creating HTTP opener instance
        handlers = []
        if self._settings['proxy']:
            proxy_handler = request.ProxyHandler(self._settings['proxy'])
            handlers.append(proxy_handler)

        if not self._settings['follow_redirects']:
            handlers.extend([RedirectHandler, request.HTTPCookieProcessor()])

        self._opener = request.build_opener(*handlers)

        # adding headers to opener
        self._opener.addheaders.extend(self._settings['headers'])

        # adding cookies to opener
        if self._settings['cookies']:
            compiled_cookies = []
            for name, value in self._settings['cookies'].items():
                compiled_cookies.append('%s=%s' % (name, value))
            cookies_string = ','.join(compiled_cookies)
            self._opener.addheaders.append(('Cookie', cookies_string))

        # compiling regexes
        self._regexes = {
            'valid_links': [],
            'exclude_links': [],
            'silent_links': [],
        }

        flags = re.I | re.S
        for regex_type in self._regexes.keys():
            for regex in self._settings[regex_type]:
                self._regexes[regex_type].append(re.compile(regex, flags=flags))
        self._regexes['href_links'] = re.compile(r'<a\s+(?:[^>]*?\s+)?href="([^"]*)"', flags=flags)

        # compiling callbacks
        self._callbacks = {}
        for regex, callback_name in self._settings['callbacks'].items():
            compiled_regex = re.compile(regex, flags=flags)
            self._callbacks[compiled_regex] = callback_name

    def __fetch_pages(self):

        """
        Main fetching loop
        """

        # getting initial page
        urls = self._storage.pop(self._settings['threads'])
        # creating lock
        lock = Lock() if self._settings['with_lock'] else DummyLock()

        while urls:

            active_threads = []

            for url in urls:
                fetcher = Fetcher()
                fetcher.setup({
                    'url': url,
                    'lock': lock,
                    'parent': self
                })
                fetcher.start()
                active_threads.append(fetcher)

            for fetcher in active_threads:
                fetcher.join()

            # getting next portion of urls
            urls = self._storage.pop(self._settings['threads'])


class Fetcher(Thread):

    """ Fetches given URL. """

    DEFAULT_HTTP_CODE = 500

    def __init__(self):
        Thread.__init__(self)

    def setup(self, settings):

        """
        Sets up thread
        """

        self._url = settings['url']
        self._lock = settings['lock']
        self._parent = settings['parent']

        self._opener = self._parent._opener
        self._callbacks = self._parent._callbacks
        self._regexes = self._parent._regexes
        self._settings = self._parent._settings

        self._storage = self._parent._storage

    def run(self):

        """
            @return void

            Runs url fetch and parse
        """

        page = {
            'body':    '',
            'url':     self._url,
            'headers': {},
            'cookies': {},
            'status':  self.DEFAULT_HTTP_CODE,
            'matches': [],
        }

        response = None

        try:
            # append user defined string to link before crawl
            prepared_url = self._url + self._settings['append_to_links']

            resp = self._opener.open(prepared_url)
            response = resp
        except request.HTTPError as resp:
            response = resp
        except:
            pass

        if response:
            page['body'] = str(response.read())

            # gather page data and call callback function if not silent
            if not self._is_silent(self._url):
                headers = {h[0]: h[1] for h in response.headers.items()}

                page.update({
                    'headers': headers,
                    'cookies': Cookies.parse(headers),
                    'status': response.getcode(),
                    'matches': self._get_matches(self._url),
                })

                getattr(self._parent, self.__get_callback())(page)

        self.__extract_urls(page['body'])

    def __get_callback(self):

        """
        Returns callback function by url
        """

        # default callback
        callback = self._parent.DEFAULT_CALLBACK

        for regex, callback_name in self._callbacks.items():
            if regex.search(self._url):
                callback = callback_name
                break

        return callback

    def __extract_urls(self, body):

        """
        Extracts valid URLs from page body
        """

        links = self._regexes['href_links'].findall(body)

        for link in links:
            # default priority
            priority = SyncStorage.PRIORITY_LOW

            # removing anchor part
            link = link.split('#', 1)[0]

            # pass if link contains only anchor
            if not link:
                continue

            # combining base url and link part
            link = parse.urljoin(self._url, link)
            link = link.strip()

            # pass if already parsed
            if self._storage.is_parsed(link):
                continue

            # trying to extract links only from valid set of pages MIME types
            url_type = mimetypes.guess_type(link, True)[0]
            allowed_mimes = self._settings['valid_mimes']
            if allowed_mimes and url_type not in allowed_mimes:
                continue

            # pass excluded link
            if self._is_excluded(link):
                continue

            # check "out of domain"
            link_info = parse.urlparse(link)

            # this is not a link
            if not link_info.netloc:
                continue

            if self._settings['domain'] not in link:
                if self._settings['stay_in_domain']:
                    # pass if "stay in domain" enabled
                    continue

            # set highest priority if link matches any regex from "valid_links" list
            if self._is_valid(link):
                priority = SyncStorage.PRIORITY_HIGH

            link_hash = link if not self._settings['hashed'] else sha1(link.encode('utf-8')).hexdigest()[:6]

            # locking
            with self._lock:
                self._storage.add(link, link_hash, priority)

    def _is_excluded(self, link):

        """
        Checks if link matches excluded regex.
        """

        for regex in self._regexes['exclude_links']:
            if regex.match(link):
                return True
        return False

    def _get_matches(self, link):

        """
        Returns matches if link is valid
        """

        for regex in self._regexes['valid_links']:
            matches = regex.findall(link)
            if matches:
                return matches
        return []

    def _is_valid(self, link):

        """
        Checks if link matches any regex from "valid_links" list
        """

        return self._get_matches(link)

    def _is_silent(self, link):

        """
        Checks if link is silent
        """

        for regex in self._regexes['silent_links']:
            is_silent = regex.search(link)
            if is_silent:
                return True
        return False


class Cookies(object):

    """ Handles HTTP cookies parsing """

    # unnecessary cookie fields
    __meta_fields = [
        'expires',
        'path',
        'domain',
        'secure',
        'HttpOnly'
    ]

    @staticmethod
    def parse(headers):

        """
        Parses cookies from response headers.
        """

        cookies = {}
        if 'Set-Cookie' in headers:
            # splitting raw cookies
            raw_cookies = headers['Set-Cookie'].split(';')
            for cookie in raw_cookies:
                cookie = cookie.split('=')
                if cookie[0].strip() not in Cookies.__meta_fields and len(cookie) > 1:
                    cookies.update({cookie[0]: cookie[1]})
        return cookies


class SyncStorage(object):

    """ Stores URLs in persistent storage. """

    PRIORITY_LOW = 0
    PRIORITY_HIGH = 1

    def __init__(self):
        self._set = set()
        self._list = list()

    def add(self, value, value_hash, priority=PRIORITY_LOW):

        """
        Adds value to storage
        """

        if value_hash in self._set:
            return
        self._list.insert(0, value) if priority == self.PRIORITY_HIGH else self._list.append(value)
        self._set.add(value_hash)

    def pop(self, num=1):

        """
        Pops values from storage
        """

        values = []
        for i in range(0, num):
            try:
                values.append(self._list.pop(0))
            except IndexError:
                break

        return values

    def is_parsed(self, value):

        """
        Checks if value has been already parsed
        """

        return value in self._set


class RedirectHandler(request.HTTPRedirectHandler):

    """ Custom URL redirects handler. """

    def http_error_302(self, req, fp, code, msg, headers):
        return fp


class DummyLock(object):

    """ Dummy lock object """

    def __enter__(self):
        pass

    def __exit__(self, exc_type, exc_val, exc_tb):
        pass
