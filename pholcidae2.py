# -*- coding: UTF-8 -*-

import re
import sqlite3
import mimetypes

from threading import Thread
from urllib import request
from urllib import parse


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
    }

    def extend(self, settings):

        """
            @type settings dict
            @return void

            Extends default settings using given settings.
        """

        self._settings.update(settings)

    def start(self):

        """
            @return void

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
            @type response dict
            @return void

            You may override this method in a subclass.
            Use it to get html page and parse it as you want to.
        """

        pass

    def __prepare(self):

        """
            @return void

            Prepares everything before start.
        """

        # creating new SyncStorage instance
        self._storage = SyncStorage()
        self._storage.setup()

        # adding start point into storage
        start_url = '%(protocol)s%(domain)s%(start_page)s' % self._settings
        self._storage.add((start_url.strip(), SyncStorage.PRIORITY_NORMAL))

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
            @return void

            Main fetching loop
        """

        # getting initial page
        urls = self._storage.pop(self._settings['threads'])

        while urls:

            active_threads = []

            for url in urls:
                fetcher = Fetcher()
                fetcher.setup({
                    'url': url['url'],
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
            @type settings dict
            @return void

            Sets up thread
        """

        self._url = settings['url']
        self._parent = settings['parent']

        self._opener = self._parent._opener
        self._callbacks = self._parent._callbacks
        self._regexes = self._parent._regexes
        self._settings = self._parent._settings

        self._storage = SyncStorage()

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
            resp = self._opener.open(self._url)
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
            @return function

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
            @param body str
            @return list

            Extracts valid URLs from page body
        """

        links = self._regexes['href_links'].findall(body)

        for link in links:
            # default priority
            priority = SyncStorage.PRIORITY_NORMAL

            # removing anchor part
            link = link.split('#', 1)[0]

            # pass if link contains only anchor
            if not link:
                continue

            # combining base url and link part
            link = parse.urljoin(self._url, link)
            link = link.strip()

            # trying to extract links only from valid set of pages MIME types
            url_type = mimetypes.guess_type(link, True)[0]
            allowed_mimes = self._settings['valid_mimes']
            if allowed_mimes and url_type not in allowed_mimes:
                continue

            # pass if already parsed
            if self._storage.is_parsed(link, body):
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
                else:
                    # set lowest priority if "stay in domain" disabled
                    priority = SyncStorage.PRIORITY_LOW

            # set highest priority if link matches any regex from "valid_links" list
            if self._is_valid(link):
                priority = SyncStorage.PRIORITY_HIGH

            self._storage.add((link, priority))

        return []

    def _is_excluded(self, link):

        """
            @type link str
            @return bool

            Checks if link matches excluded regex.
        """

        for regex in self._regexes['exclude_links']:
            if regex.match(link):
                return True
        return False

    def _get_matches(self, link):

        """
            @type link str
            @return list

            Returns matches if link is valid
        """

        for regex in self._regexes['valid_links']:
            matches = regex.findall(link)
            if matches:
                return matches
        return []

    def _is_valid(self, link):

        """
            @type link str
            @return bool

            Checks if link matches any regex from "valid_links" list
        """

        return self._get_matches(link)

    def _is_silent(self, link):

        """
            @type link str
            @return list

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
            @type headers dict
            @return dict

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
    PRIORITY_NORMAL = 1
    PRIORITY_HIGH = 2

    _sqlite_commands = {
        'drop': 'DROP TABLE IF EXISTS `links`',
        'create': 'CREATE TABLE `links` (' +
                  ' `url` VARCHAR(2048) NOT NULL UNIQUE,' +
                  ' `priority` UNSIGNED TINYINT(1),' +
                  ' `parsed` UNSIGNED TINYINT(1) DEFAULT 0' +
                  ')',
        'insert': 'INSERT OR IGNORE INTO `links` (`url`, `priority`) VALUES (?, ?)',
        'select': 'SELECT url, priority, parsed FROM `links` WHERE 1',
        'update': 'UPDATE `links` SET parsed=? WHERE url=?',
    }

    _sqlite_schema = ['url', 'priority', 'parsed']

    def __init__(self):
        self._connection_point = 'file:pholcidae?mode=memory&cache=shared'
        self._connection = sqlite3.connect(self._connection_point, check_same_thread=False, uri=True)
        self._cursor = self._connection.cursor()

    def __del__(self):
        self._cursor.close()
        self._connection.close()

    def add(self, values):

        """
            @type values list|tuple
            @return void

            Writes element into storage.
        """

        if not isinstance(values, list):
            values = [values]

        self._cursor.executemany(self._sqlite_commands['insert'], values)
        self._connection.commit()

    def get_all(self, values={}):

        """
            @type values dict
            @return list

            Finds multiple elements in storage.
        """

        sql = self._sqlite_commands['select']
        params = []

        if values:
            for key, value in values.items():
                sql += ' AND ' + key + '=?'
                params.append(value)

        self._cursor.execute(sql, tuple(params))
        self._connection.commit()

        records = self._cursor.fetchall()

        result = []
        if records:
            for record in records:
                record_dict = {}
                for idx, value in enumerate(record):
                    record_dict[self._sqlite_schema[idx]] = value
                result.append(record_dict)

        return result

    def get(self, values={}):

        """
            @type values dict
            @return dict

            Finds one element in storage.
        """

        records = self.get_all(values)
        return records[0] if records else {}

    def update(self, values):

        """
            @type values dict
            @return void

            Deletes element from storage.
        """

        params = (values['parsed'], values['url'])

        self._cursor.execute(self._sqlite_commands['update'], params)
        self._connection.commit()

    def pop(self, num=1):

        """
            @type num int
            @return void

            Pops element(s) from storage.
        """

        sql = self._sqlite_commands['select'] + ' AND parsed = 0 ORDER BY priority DESC LIMIT ?'

        self._cursor.execute(sql, (num,))
        records = self._cursor.fetchall()

        params = [(1, record[0]) for record in records]
        self._cursor.executemany(self._sqlite_commands['update'], params)
        self._connection.commit()

        result = []
        if records:
            for record in records:
                record_dict = {}
                for idx, value in enumerate(record):
                    record_dict[self._sqlite_schema[idx]] = value
                result.append(record_dict)

        return result

    def is_parsed(self, url, body):

        """
            @param url str
            @return bool

            Checks if URL has been already parsed
        """

        try:
            sql = self._sqlite_commands['select'] + ' AND parsed = 1 AND url = \'%s\'' % url
            self._cursor.execute(sql)
            self._connection.commit()

            result = self._cursor.fetchone()
        except:
            result = True

        return bool(result)

    def setup(self):

        """
            @return void

            Sets up storage.
        """

        # creating table to store URLs
        self._cursor.execute(self._sqlite_commands['drop'])
        self._cursor.execute(self._sqlite_commands['create'])
        self._connection.commit()


class RedirectHandler(request.HTTPRedirectHandler):

    """ Custom URL redirects handler. """

    def http_error_302(self, req, fp, code, msg, headers):
        return fp

    http_error_301 = http_error_303 = http_error_307 = http_error_302
