# coding=utf-8

from tiny_engine import TinyEngine

import requests
import js2py


class TinyRequestsEngine(TinyEngine):  # TODO

    DEFAULT_USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/62.0.3202.75 Safari/537.36"
    DEFAULT_HEADERS = {
        "User-Agent": DEFAULT_USER_AGENT,
    }
    DEFAULT_REQUEST_TIMEOUT = 10
    DEFAULT_ENCODING = "utf-8"
    DEFAULT_GET_BYTES = False

    CMD_GET_ = "get_"
    CMD_POST_ = "post_"
    CMD_SESSION = "session"
    CMD_COOKIES = "cookies"
    CMD_EVAL_JS = "eval_js"

    ARG_SESSION = "session"
    ARG_COOKIES = "cookies"
    ARG_URL = "url"
    ARG_HEADERS = "headers"
    ARG_ARGS = "args"
    ARG_DATA = "data"
    ARG_TIMEOUT = "timeout"
    ARG_ENCODING = "encoding"
    ARG_GET_BYTES = "get_bytes"

    def __init__(self, fp=None, script=None, encoding=None, data_encoding=None, logger=None, args=None, callback=None,
                 **kwargs):
        super(TinyRequestsEngine, self).__init__(fp=fp, script=script, encoding=encoding, data_encoding=data_encoding,
                                                 logger=logger, args=args, callback=callback,
                                                 **kwargs)

        self._session = requests.session()
        self._cookies = requests.cookies.RequestsCookieJar()

        # Register runners for Requests and js2py
        self.register_runners({
            self.CMD_GET_: self.run_get_d,
            self.CMD_POST_: self.run_post_d,
            # TODO js2py
        })

    def session_get(self, url, headers=DEFAULT_HEADERS, timeout=DEFAULT_REQUEST_TIMEOUT, encoding="utf-8",
                    get_bytes=False):
        session = self._session

        # 获取页面数据
        req = session.get(url, headers=headers, timeout=timeout)
        if not get_bytes:
            req.encoding = encoding
            result = req.text
        else:
            result = req.content
        return result

    def session_post(self, url, headers=DEFAULT_HEADERS, data=None, timeout=DEFAULT_REQUEST_TIMEOUT, encoding="utf-8",
                     get_bytes=False):
        session = self._session

        # 获取页面数据
        req = session.post(url, headers=headers, data=data, timeout=timeout)
        if not get_bytes:
            req.encoding = encoding
            result = req.text
        else:
            result = req.content
        return result

    def run_get_d(self, sobj, args, depth=0):
        logger = self._logger
        cmd = sobj[0]
        cargs = sobj[1] if len(sobj) > 1 else None
        csub = sobj[2] if len(sobj) > 2 else None

        vars = args.vars
        var = cargs.get(self.ARG_VAR)  # save result data to variable
        url = vars.get(cargs.get(self.ARG_URL, ""), "")
        headers = vars.get(cargs.get(self.ARG_HEADERS, ""), self.DEFAULT_HEADERS)
        timeout = vars.get(cargs.get(self.ARG_TIMEOUT, ""), self.DEFAULT_REQUEST_TIMEOUT)
        encoding = vars.get(cargs.get(self.ARG_ENCODING, ""), self.DEFAULT_ENCODING)
        get_bytes = vars.get(cargs.get(self.ARG_GET_BYTES, ""), self.DEFAULT_GET_BYTES)
        args = cargs.get(self.ARG_ARGS)  # to args string

        # TODO do session_get(), and auto parse result json string to object

    def run_post_d(self, sobj, args, depth=0):
        logger = self._logger
        cmd = sobj[0]
        cargs = sobj[1] if len(sobj) > 1 else None
        csub = sobj[2] if len(sobj) > 2 else None

        vars = args.vars
        var = cargs.get(self.ARG_VAR)  # save result data to variable
        url = vars.get(cargs.get(self.ARG_URL, ""), "")
        headers = vars.get(cargs.get(self.ARG_HEADERS, ""), self.DEFAULT_HEADERS)
        timeout = vars.get(cargs.get(self.ARG_TIMEOUT, ""), self.DEFAULT_REQUEST_TIMEOUT)
        encoding = vars.get(cargs.get(self.ARG_ENCODING, ""), self.DEFAULT_ENCODING)
        get_bytes = vars.get(cargs.get(self.ARG_GET_BYTES, ""), self.DEFAULT_GET_BYTES)
        data = cargs.get(self.ARG_DATA)  # to data string or data dict

        # TODO do session_post(), and auto parse result json string to object
