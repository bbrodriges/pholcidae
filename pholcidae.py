# -*- coding: UTF-8 -*-

import sys
import re
import heapq
import sqlite3
import os
import mimetypes
import tempfile

# importing modules corresponding to Python version
if sys.version_info < (3, 0, 0):
    import urlparse
    import urllib2
else:
    from urllib import request as urllib2
    from urllib import parse as urlparse

class Pholcidae:

    """" Pholcidae is a small and fast web crawler. """

    def __init__(self):

        """
            @return void

            Creates Pholcidae instance and updates default settings dict.
        """

        # extending settings with given values
        self._extend_settings()
        # compiling regular expressions
        self._compile_regexs()

        # autostart crawler if settings allows
        if self._settings.autostart:
            self.start()

    ############################################################################
    # PUBLIC METHODS                                                           #
    ############################################################################

    def crawl(self, response):

        """
            @type response AttrDict
            @return void

            Dummy method which can be overrided by inheriting Pholcidae class.
            Use it to get html page and parse it as you want to.
        """

        pass

    def start(self):

        """
            @return void

            Simple crawler start trigger.
        """

        # trying to call precrawl function
        self._call_precrawl()
        # start crawling
        self._get_page()

    ############################################################################
    # PRIVATE METHODS                                                          #
    ############################################################################

    ############################ INIT METHODS ##################################

    def _extend_settings(self):

        """
            @return void

            Extends default settings with given settings.
        """

        # creating default settings object
        self._settings = AttrDict({
            # do we need to follow HTTP redirects?
            'follow_redirects': True,
            # what should we append to all links?
            'append_to_links': '',
            # what page links do we need to parse?
            'valid_links': ['(.*)'],
            # what URLs must be excluded
            'exclude_links': [],
            # what is an entry point for crawler?
            'start_page': '/',
            # which domain should we parse?
            'domain': '',
            # should we ignor pages outside of the given domain?
            'stay_in_domain': True,
            # which protocol do we need to use?
            'protocol': 'http://',
            # autostart crawler right after initialization?
            'autostart': False,
            # cookies to be added to each request
            'cookies': {},
            # custom headers to be added to each request
            'headers': {},
            # precrawl function to execute
            'precrawl': None,
            # postcrawl fucntion to execute
            'postcrawl': None,
            # custom callbacks list
            'callbacks': {},
            # support proxy
            'proxy': {}
        })

        # updating settings with given values
        self._settings.update(self.settings)

        # creating urllib2 opener
        self._create_opener()
        # compiling cookies
        self._compile_cookies()
        # compiling headers
        self._compile_headers()

        # adding start point into unparsed list
        start_url = '%s%s%s' % (self._settings.protocol, self._settings.domain,
                                self._settings.start_page)

        # creating new PriorityList for URLs
        self._unparsed_urls = PriorityList()
        # adding start url to priority list with lesser priority
        self._unparsed_urls.add(start_url, matches=[], priority=0)

    def _compile_regexs(self):

        """
            @return void

            Compiles regular expressions for further use.
        """

        # setting default flags
        flags = re.I | re.S
        # compiling regexs
        self._regex = AttrDict({
            # collects all links across given page
            'href_links': re.compile(r'<a\s(.*?)href="(.*?)"(.*?)>',
                                     flags=flags),
            # valid links regexs
            'valid_link': [],
            # invalid links regexs
            'invalid_link': []
        })

        # complinig valid links regexs
        for regex in self._settings.valid_links:
            self._regex.valid_link.append(re.compile(regex, flags=flags))

        # compiling invalid links regexs
        for regex in self._settings.exclude_links:
            self._regex.invalid_link.append(re.compile(regex, flags=flags))

    def _compile_cookies(self):

        """
            @return void

            Compiles given dict of cookies to string.
        """

        compiled = []
        for name, value in self._settings.cookies.items():
            compiled.append('%s=%s' % (name, value))
        self._settings.cookies = ','.join(compiled)
        self._opener.addheaders.append(('Cookie', self._settings.cookies))

    def _compile_headers(self):

        """
            @return void

            Adds given dict of headers to urllib2 opener.
        """

        for header_name, header_value in self._settings.headers.items():
            self._opener.addheaders.append((header_name, header_value))

    def _create_opener(self):

        """
            @return void

            Creates local urllib2 opener and extends it with custom
            redirect handler if needed.
        """

        handlers = []
        if self._settings.proxy:
            proxy_handler = urllib2.ProxyHandler(self._settings.proxy)
            handlers.append(proxy_handler)

        if not self._settings.follow_redirects:
            handlers.extend([PholcidaeRedirectHandler, urllib2.HTTPCookieProcessor()])

        self._opener = urllib2.build_opener(*handlers)

    ############## PRE, POST CRAWL AND CUSTOM CALLBACK METHODS CALLERS ##################

    def _call_precrawl(self):

        """
            @return void

            Calls given precrawl function if given.
        """

        # if precrawl function given - execute it
        precrawl = self._settings.precrawl
        if precrawl:
            getattr(self, precrawl)()

    def _call_postcrawl(self):

        """
            @return void

            Calls given postcrawl function if given.
        """

        # if postcrawl function given - execute it
        postcrawl = self._settings.postcrawl
        if postcrawl:
            getattr(self, postcrawl)()

    def _call_custom_callback(self, url_pattern, data):

        """
            @type url_pattern string
            @return void

            Calls custom callback function for current URL pattern, if given.
        """

        # if postcrawl function given - execute it
        if url_pattern in self._settings.callbacks:
            callback = self._settings.callbacks[url_pattern]
            if callback:
                getattr(self, callback)(data)
                return
        self.crawl(data)

    ########################## CRAWLING METHODS ################################

    def _get_page(self):

        """
            @return void

            Fetches page by URL.
        """

        valid_statuses = range(200, 299)

        # iterating over unparsed links
        while self._unparsed_urls.heap:
            # getting link to get
            priority, url, matches = self._unparsed_urls.get()

            # fetching page
            page = self._fetch_url(url)
            if page.status in valid_statuses:
                # parsing only valid urls (with higher priority)
                if priority == 0:
                    # adding regex match to page object
                    page.match = matches
                    # determining regex pattern for current url
                    url_pattern = self._get_link_pattern(page.url)
                    # sending collected data to custom or crawl function
                    self._call_custom_callback(url_pattern, page)
                # collecting links from page
                self._get_page_links(page.body, page.url)

        # calls postcrawl after heap looping
        self._call_postcrawl()

    def _get_page_links(self, raw_html, url):

        """
            @type raw_html str
            @type url str
            @return void

            Parses out all links from crawled web page.
        """

        # only trying to extract links from HTML pages
        # not images, audio, etc.
        url_type = mimetypes.guess_type(url, True)[0]
        if url_type not in ['text/html', None]:
            return

        links_groups = self._regex.href_links.findall(str(raw_html))
        links = [group[1] for group in links_groups]
        for link in links:
            # default priority
            priority = None
            # is link not excluded?
            if not self._is_excluded(link):
                # getting link parts
                link_info = urlparse.urlparse(link)
                # if link not relative
                if link_info.scheme or link_info.netloc:
                    # link is outside of domain scope
                    if self._settings.domain not in link_info.netloc:
                        # stay_in_domain enabled
                        if self._settings.stay_in_domain:
                            continue  # throwing out invalid link
                        else:
                            # 2 (lowest) priority for "out-of-domain" links
                            priority = 2
                        # average priority for "in-domain" links
                # converting relative link into absolute
                link = urlparse.urljoin(url, link)
                # stripping unnecessary elements from link string
                link = link.strip()
                # if matches found - writing down and calcutaing priority
                matches = self._is_valid_link(link)
                # the "int(not bool(matches))" will produce 0 (higher) priority
                # for valid links and 1 (lower) priority to invalid links
                priority = int(not bool(matches)) if not priority else priority
                # adding link to heap
                self._unparsed_urls.add(link, matches, priority)

    def _is_valid_link(self, link):

        """
            @type link str
            @return list

            Compares link with given regex to decide if we need to parse that
            page.
        """

        # if hash in URL - assumimg anchor or AJAX
        if link and '#' not in link:
            for regex in self._regex.valid_link:
                    matches = regex.findall(link)
                    if matches:
                        return matches
        return []

    def _is_excluded(self, link):

        """
            @type link str
            @return bool

            Checks if link matches exluded regex.
        """

        for regex in self._regex.invalid_link:
            if regex.search(link):
                return True
        return False

    def _get_link_pattern(self, link):

        """
            @type link str
            @return str

            Returns pattern for link.
        """

        if link and '#' not in link:
            for regex in self._regex.valid_link:
                    matches = regex.findall(link)
                    if matches:
                        return regex.pattern
        return ''

    ######################### URL FETCHING METHODS #############################

    def _fetch_url(self, url):

        """
            @type url str
            @return AttrDict

            Fetches given URL and returns data from it.
        """

        # empty page container
        page = AttrDict()

        try:
            # getting response from given URL plus text to append
            resp = self._opener.open(url + self._settings.append_to_links)
            page = AttrDict({
                'body': resp.read(),
                'url': re.sub(re.escape(self._settings.append_to_links) + '$', '', resp.geturl()),
                'headers': AttrDict(dict(resp.headers.items())),
                'cookies': self._parse_cookies(dict(resp.headers.items())),
                'status': resp.getcode()
            })
        except:
            # drop invalid page with 500 HTTP error code
            page = AttrDict({'status': 500})
        return page

    def _parse_cookies(self, headers):

        """
            @type headers dict
            @return AttrDict

            Parses cookies from response headers.
        """

        cookies = AttrDict()
        # lowering headers keys
        headers = {k.lower(): v for k,v in headers.items()}
        if 'set-cookie' in headers:
            # splitting raw cookies
            raw_cookies = headers['set-cookie'].split(';')
            # cookie parts to throw out
            throw_out = ['expires', 'path', 'domain', 'secure', 'HttpOnly']
            for cookie in raw_cookies:
                cookie = cookie.split('=')
                if cookie[0].strip() not in throw_out and len(cookie) > 1:
                    cookies.update({cookie[0]: cookie[1]})
        return cookies


class AttrDict(dict):

    """ A dict that allows for object-like property access syntax. """

    def __init__(self, new_dict=None):
        dict.__init__(self)
        if new_dict:
            self.update(new_dict)

    def __getattr__(self, name):
        try:
            return self[name]
        except KeyError:
            raise AttributeError(name)

    def __setattr__(self, key, value):
        self.update({key: value})


class PholcidaeRedirectHandler(urllib2.HTTPRedirectHandler):

    """ Custom URL redirects handler. """

    def http_error_302(self, req, fp, code, msg, headers):
        return fp

    http_error_301 = http_error_303 = http_error_307 = http_error_302


class PriorityList(object):

    """ List with priority. """

    def __init__(self):
        self.heap = []
        self._set = set()

        self._set_disk_sync_freq = 10000
        self._sync_storage = SyncStorage()

    def __repr__(self):
        return str(self.heap)

    def add(self, element, matches, priority):

        """
            @type element mixed
            @type matches list
            @type priority int
            @return void

            Appends element to list with priority.
        """

        # ignore the fragment
        element = element.split('#', 1)[0]
        if not self.is_parsed(element):
            heapq.heappush(self.heap, (priority, element, matches))

            self._set.add(element)
            self.sync_list()

    def is_parsed(self, element):

        """
            @return bool

            Checks if given URL has ever been added to priority list.
        """

        if element not in self._set and not self._sync_storage.find(element):
            return False
        return True

    def sync_list(self):

        """
            @return void

            Syncs list to persistent storage.
        """

        if len(self._set) % self._set_disk_sync_freq == 0:
            sync_list = []
            for x in range(0, self._set_disk_sync_freq - 1):
               sync_list.append(self._set.pop())
            self._sync_storage.write(sync_list)

    def get(self):

        """
            @return tuple

            Pops element out from list.
        """

        return heapq.heappop(self.heap)

class SyncStorage(object):

    """ Storage to sync parsed URLs set to persistent storage. """

    def __init__(self):
        self._storage_file = tempfile.NamedTemporaryFile()
        self._connection = sqlite3.connect(self._storage_file.name)
        self._cursor = self._connection.cursor()

        self.prepare_sqlite_commands()
        self.prepare_storage()

    def __del__(self):
        self._cursor.close()
        self._connection.close()
        self._storage_file.close()

    def prepare_sqlite_commands(self):

        """
            @return void

            Prepares SQLite commands.
        """

        self._sqlite_commands = AttrDict({
            'create':    'CREATE TABLE `parsed_urls` (`url` VARCHAR(3000) NOT NULL);',
            'add_index': 'CREATE UNIQUE INDEX `url_UNIQUE` ON `parsed_urls` (`url` ASC);',
            'insert':    'INSERT OR IGNORE INTO `parsed_urls` (`url`) VALUES (?);',
            'select':    'SELECT url FROM `parsed_urls` WHERE url = ?;'
        })

    def prepare_storage(self):

        """
            @return void

            Prepares storage.
        """

        # creating table to store URLs
        self._cursor.execute(self._sqlite_commands.create)
        self._cursor.execute(self._sqlite_commands.add_index)
        self._connection.commit()

    def write(self, elements):

        """
            @type elements mixed
            @return void

            Writes element into storage.
        """

        if not isinstance(elements, (list, set, dict)):
            elements = [elements]

        for element in elements:
            self._cursor.execute(self._sqlite_commands.insert, (element,))

        self._connection.commit()

    def find(self, element):

        """
            @type element string
            @return bool

            Finds element in storage.
        """

        self._cursor.execute(self._sqlite_commands.select, (element,))
        self._connection.commit()

        return bool(self._cursor.fetchone())
