# -*- coding: UTF-8 -*-

import sys
import re
import heapq

# importing modules corresponding to Python version
if sys.version_info < (3,0,0):
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

        # default local urllib2 opener
        self._opener = None
        # creating new PriorityList for URLs
        self._unparsed_urls = PriorityList()
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
            'postcrawl': None
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

        self._opener = urllib2.build_opener()
        if not self._settings.follow_redirects:
            self._opener = urllib2.build_opener(PholcidaeRedirectHandler,
                                                urllib2.HTTPCookieProcessor())

    ################### PRE AND POST CRAWL METHODS CALLERS #####################

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

    ########################## CRAWLING METHODS ################################

    def _get_page(self):

        """
            @return bool

            Fetches page by URL.
        """

        # iterating over unparsed links
        while self._unparsed_urls.heap:
            # getting link to get
            priority, url, matches = self._unparsed_urls.get()

            # fetching page
            page = self._fetch_url(url)
            if page.status not in [500, 404, 502]:
                # parsing only valid urls (with higher priority)
                if priority == 0:
                    # adding regex match to page object
                    page.match = matches
                    # sending collected data to crawl function
                    self.crawl(page)
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
            # getting response from given URL
            resp = self._opener.open(url)
            page = AttrDict({
                'body': resp.read(),
                'url': resp.geturl(),
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
                if cookie[0].strip() not in throw_out:
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

        if element not in self._set:
            heapq.heappush(self.heap, (priority, element, matches))
            self._set.add(element)

    def get(self):

        """
            @return tuple

            Pops element out from list.
        """

        return heapq.heappop(self.heap)