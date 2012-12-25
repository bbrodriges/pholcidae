# -*- coding: UTF-8 -*-

import re
import urlparse
import urllib2


class Pholcidae:

    """" Pholcidae is a small and fast web crawler. """

    def __init__(self):

        """
            @return void

            Creates Pholcidae instance and updates default settings dict.
        """

        # default local urllib2 opener
        self._opener = None
        # creating new lists of unparsed, alerady parsed and invalid URLs
        self._unparsed_urls = set()
        self._parsed_urls = set()
        # extending settings with given values
        self._extend_settings()
        # compiling regular expressions
        self._compile_regexs()
        # autostart crawler if settings allows
        if self._settings.autostart:
            self.start()

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

        # creating settings object
        self._settings = AttrDict()

        # filling up default settings
        # do we need to follow HTTP redirects?
        self._settings.follow_redirects = True
        # what page links do we need to parse?
        self._settings.valid_link = '(.*)'
        # what is an entry point for crawler??
        self._settings.start_page = '/'
        # which domain should we parse?
        self._settings.domain = ''
        # should we ignor pages outside of the given domain?
        self._settings.stay_in_domain = True
        # which protocol do we need to use?
        self._settings.protocol = 'http://'
        # autostart crawler right after initialization?
        self._settings.autostart = False
        # cookies to be added to each request
        self._settings.cookies = {}
        # custom headers to be added to each request
        self._settings.headers = {}


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
        self._unparsed_urls.add(start_url)

    def _compile_regexs(self):

        """
            @return void

            Compiles regular expressions for further use.
        """

        # regexs container
        self._regex = AttrDict()
        # compiling regexs
        flags = re.I | re.S  # setting common flags
        # collects all links across given page
        self._regex.href_links = re.compile(r'<a\s(.*?)href="(.*?)"(.*?)>',
                                            flags=flags)
        self._regex.valid_link = re.compile(self._settings.valid_link,
                                            flags=flags)
        self._regex.split_header = re.compile(r'^(.*?):(.*)$', flags=flags)

    def _compile_cookies(self):

        """
            @return void

            Compiles given dict of cookies to string.
        """

        compiled = []
        for name, value in self._settings.cookies.iteritems():
            compiled.append('%s=%s' % (name, value))
        self._settings.cookies = ','.join(compiled)
        self._opener.addheaders.append(('Cookie', self._settings.cookies))

    def _compile_headers(self):

        """
            @return void

            Adds given dict of headers to urllib2 opener.
        """

        for header_name, header_value in self._settings.headers.iteritems():
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

    ########################## CRAWLING METHODS ################################

    def _get_page(self):

        """
            @return bool

            Fetches page by URL.
        """

        if not self._unparsed_urls:
            # exiting out from recursion
            return True

        # getting link to get
        url = self._unparsed_urls.pop()
        # moving url from unparsed to parsed list
        self._parsed_urls.add(url)

        # fetching page
        page = self._fetch_url(url)
        if page.status not in ['500, 404, 502']:
            # collecting links from page
            self._get_page_links(page.body, page.url)
            # sending raw HTML to crawl function
            self.crawl(page)

        # trying next URL
        self._get_page()

    def _get_page_links(self, raw_html, url):

        """
            @type raw_html str
            @type url str
            @return void

            Parses out all links from crawled web page.
        """

        links_groups = self._regex.href_links.findall(raw_html)
        links = [group[1] for group in links_groups]
        for link in links:
            # comparing link with given pattern
            if self._is_valid_link(link):
                # getting link parts
                link_info = urlparse.urlparse(link)
                # if link not relative
                if link_info.scheme or link_info.netloc:
                    # if stay_in_domain enabled and link outside of domain scope
                    if self._settings.stay_in_domain:
                        if self._settings.domain not in link:
                            continue  # throwing out invalid link
                else:
                    # converting relative link into absolute
                    link = urlparse.urljoin(url, link)
                # if link was not previously parsed
                if link not in self._parsed_urls:
                    self._unparsed_urls.add(link)

    def _is_valid_link(self, link):

        """
            @type link str
            @return bool

            Compares link with given regex to decide if we need to parse that
            page.
        """

        if link and '#' not in link:
            matches = self._regex.valid_link.search(link)
            if matches:
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
            page.body = resp.read()
            page.url = resp.geturl()
            page.headers = self._parse_headers(resp.info().headers)
            page.cookies = self._parse_cookies(page.headers)
            page.status = resp.getcode()
        except urllib2.HTTPError as error:
            page.body = error.read()
            page.status = error.code
            page.url = url

        return page

    def _parse_headers(self, raw_headers):

        """
            @type raw_headers list
            @return AttrDict

            Parses headers returned by page.
        """

        # empty headers container
        headers = AttrDict()

        for header in raw_headers:
            # removing extra characters
            header = self._regex.split_header.search(header)
            key = header.group(1)
            value = header.group(0).split(':', 1)[1].strip()
            headers.__setattr__(key, value)
        return headers

    def _parse_cookies(self, headers):

        """
            @type headers AttrDict
            @return AttrDict

            Parses cookies from response headers.
        """

        cookies = AttrDict()
        for key, value in headers.iteritems():
            if key == 'Set-Cookie':
                name, content = value.split(';', 1)[0].split('=')
                cookies.__setattr__(name, content)
        return cookies

class AttrDict(dict):

    """ A dict that allows for object-like property access syntax. """

    def __getattr__(self, name):
        try:
            return self[name]
        except KeyError:
            raise AttributeError(name)

    def __setattr__(self, key, value):
        self.update({key:value})


class PholcidaeRedirectHandler(urllib2.HTTPRedirectHandler):

    """ Custom URL redirects handler. """

    def http_error_302(self, req, fp, code, msg, headers):
        return fp

    http_error_301 = http_error_303 = http_error_307 = http_error_302