# coding=utf-8

import traceback as tb
import sys
import types
import re
import json
import json5
from copy import deepcopy

import jsonpath_rw as jp
from lxml.etree import fromstring as et_fromstring
from lxml.html import fromstring as html_fromstring

from MiniUtils import get_logger

__version__ = "1.0.190730"


class TinyEngine:
    DEFAULT_ENCODING = 'utf-8'

    CMD_VARS = "vars"
    CMD_ASSIGN = "assign"
    CMD_PRINT = "print"
    CMD_MSG = "msg"
    CMD_CALL = "call"
    CMD_RERUN = "rerun"
    CMD_BREAK = "break"
    CMD_CALLBACK = "callback"
    CMD_ASSERT = "assert"
    CMD_JSONPATH = "jpath"
    CMD_XPATH = "xpath"
    CMD_READ = "read"
    CMD_WRITE = "write"
    CMD_APPEND = "append"

    ARG_FILE_NAME = "file_name"
    ARG_ENCODING = "encoding"
    ARG_VAR = "var"

    AFUNC_RE = "re"
    AFUNC_IN = "in"
    AFUNC_PREFER = [AFUNC_RE, AFUNC_IN]

    class RerunException(Exception):
        """
        For flow controlling - Rerun
        """

        def __init__(self, *args, **kwargs):
            Exception.__init__(self, *args, **kwargs)

    class BreakException(Exception):
        """
        For flow controlling - Break
        """

        def __init__(self, *args, **kwargs):
            Exception.__init__(self, *args, **kwargs)

    class Args:
        """
        For saving current script running environment
        """

        def __init__(self):
            self._args = dict()
            self._vars = dict()

        @property
        def vars(self):
            return self._vars

        def __getitem__(self, item):
            return self._args.get(item)

        def __setitem__(self, key, value):
            self._args[key] = value

        def var_replacer(self, v_str, v_prefix=r"$%", v_suffix=r"%$", re_prefix=r"\$\%", re_suffix=r"\%\$"):
            """
            Replace string in v_str marked with v_prefix as prefix and v_suffix as suffix.
            :param v_str: string need proceeded
            :param v_prefix: prefix of the placeholder
            :param v_suffix: suffix of the placeholder
            :param re_prefix:
            :param re_suffix:
            :return: string proceeded
            """

            return self.var_replacer_raw(self._vars, v_str,
                                         v_prefix=v_prefix, v_suffix=v_suffix, re_prefix=re_prefix,
                                         re_suffix=re_suffix)

        @staticmethod
        def var_replacer_raw(var_dict, v_str, v_prefix=r"$%", v_suffix=r"%$", re_prefix=r"\$\%", re_suffix=r"\%\$"):
            keys = re.findall(re_prefix + r"(.+?)" + re_suffix, v_str)
            d_keys = []
            for i in keys:
                value = var_dict.get(i)
                if value is not None:
                    d_keys.append(i)

            o_str = deepcopy(v_str)
            for i in d_keys:
                o_str = o_str.replace(v_prefix + i + v_suffix, str(var_dict.get(i)))
            return o_str

    def __init__(self, fp=None, script=None, encoding=None, data_encoding=None, logger=None, args=None, callback=None,
                 **kwargs):
        self._fp = None
        self._script = None
        self._encoding = None
        self._data_encoding = data_encoding if data_encoding is not None else self.DEFAULT_ENCODING

        self._logger = logger or get_logger()
        self._args = args or self.Args()
        self._callback = callback

        # map for flow controlling
        self._exceptions_map = {
            self.CMD_RERUN: self.RerunException,
            self.CMD_BREAK: self.BreakException,
        }

        # basis functional runners for nodes in the flow
        self._logger.debug("TinyEngine registering cmd runners...")
        self._cmd_runners = {}
        self.register_runners({
            # vars: quickly store values of variables in args.vars
            self.CMD_VARS: self.run_vars,
            # assign: quickly assign value to variable from each other variables in args.vars
            self.CMD_ASSIGN: self.run_assign,
            # print: print values of variables on screen with logging
            self.CMD_PRINT: self.run_print,
            # print: print message on screen with logging
            self.CMD_MSG: self.run_msg,
            # call: flow control - call a sub script list named in vars
            self.CMD_CALL: self.run_call,
            # rerun: flow control - rerun from the first node of the current script list
            self.CMD_RERUN: self.run_except,
            # rerun: flow control - break out from the current script list
            self.CMD_BREAK: self.run_except,
            # callback: call to a callback if set
            self.CMD_CALLBACK: self.run_callback,
            # assert: check if the specific value in args.vars is available, and run sub script list if existed
            self.CMD_ASSERT: self.run_assert,
            # jpath: get values extracted from a variable via jsonpath
            self.CMD_JSONPATH: self.run_jsonpath,
            # xpath: get values extracted from a variable via xpath
            self.CMD_XPATH: self.run_xpath,
            # read: read from the specific file with specific encoding
            self.CMD_READ: self.run_read,
            # write: write to the specific file with specific encoding
            self.CMD_WRITE: self.run_write,
            # append: append to the specific file with specific encoding
            self.CMD_APPEND: self.run_write,
        })
        self.AFUNC_MAP = {
            self.AFUNC_RE: self.afunc_re,
            self.AFUNC_IN: self.afunc_in,
        }

        # load script file right now
        self._logger.debug("[{}][{}] TinyEngine loading script...".format(self.__class__.__name__,
                                                                          sys._getframe().f_code.co_name))
        self._script_obj = None
        if fp:
            self.load_from_file(fp, encoding)
        else:
            self.load_from_str(script)

        self._logger.debug("[{}][{}] TinyEngine loaded. ({})".format(self.__class__.__name__,
                                                                     sys._getframe().f_code.co_name,
                                                                     __version__))

    def afunc_re(self, a, b):
        return re.search(b, a)

    def afunc_in(self, a, b):
        return a in b

    def register_runner(self, cmd, func):
        if isinstance(cmd, str) and (isinstance(func, types.FunctionType) or isinstance(func, types.MethodType)):
            self._cmd_runners[cmd] = func

    def register_runners(self, cmd_func_map):
        if isinstance(cmd_func_map, dict):
            for k, v in cmd_func_map.items():
                self.register_runner(k, v)

    def load_from_file(self, fp, encoding=None):
        self._fp = fp
        self._encoding = encoding
        with open(fp, mode='r', encoding=encoding) as f:
            self._script = f.read()
            self.load_from_str(self._script)

    def load_from_str(self, script):
        self._script = script
        try:
            self._script_obj = json5.loads(script)
        except Exception as e1:
            err1 = str(e1)
            try:
                self._script_obj = json.loads(script)
            except Exception as e2:
                err2 = str(e2)
                raise RuntimeError(err1 + " | " + err2)

    def run(self, sobj=None):
        """
        Quick start for running script node.
        :param sobj: script node object
        :return: script result from self.execute_script()
        """

        if sobj is None:
            sobj = self._script_obj
        args = self._args
        return self.execute_script(sobj, args)

    def execute_script(self, sobj, args, depth=0):
        """
        Recursively run one node in the script flow.
        :param sobj: script node object
        :param args: script running environment
        :param depth: recursive depth record
        :return: script result of one command, or None
        """

        logger = self._logger

        runners = self._cmd_runners
        if isinstance(sobj, list):
            if len(sobj) >= 1:
                cmd = sobj[0]
                if isinstance(cmd, str):
                    func = runners.get(cmd)
                    if func is not None:
                        logger.debug("[{}][{}] Running cmd: {}".format(self.__class__.__name__,
                                                                       sys._getframe().f_code.co_name,
                                                                       cmd))
                        return func(sobj, args, depth)
                else:
                    logger.debug("[{}][{}] Running sub script (depth={})...".format(self.__class__.__name__,
                                                                                    sys._getframe().f_code.co_name,
                                                                                    depth))
                    rerun_requested = True
                    while rerun_requested:
                        rerun_requested = False
                        try:
                            for sub_sobj in sobj:
                                self.execute_script(sub_sobj, args, depth + 1)
                        except self.RerunException:
                            rerun_requested = True
        return None

    def run_vars(self, sobj, args, depth=0):
        logger = self._logger
        cmd = sobj[0]
        cargs = sobj[1] if len(sobj) > 1 else None
        csub = sobj[2] if len(sobj) > 2 else None

        if isinstance(cargs, dict):
            vars = args.vars
            vars.update(cargs)
            logger.debug("[{}][{}] vars updated! ({})".format(self.__class__.__name__,
                                                              sys._getframe().f_code.co_name,
                                                              len(cargs)))

    def run_assign(self, sobj, args, depth=0):
        logger = self._logger
        cmd = sobj[0]
        cargs = sobj[1] if len(sobj) > 1 else None
        csub = sobj[2] if len(sobj) > 2 else None

        if isinstance(cargs, dict):
            vars = args.vars
            for k, v in cargs.items():
                if v in vars:
                    vars[k] = vars[v]
                    logger.info("[{}][{}] assignment ({} <- {})".format(self.__class__.__name__,
                                                                        sys._getframe().f_code.co_name,
                                                                        repr(k), repr(v)))
                    logger.debug("[{}][{}] (value of {}: {}))".format(self.__class__.__name__,
                                                                      sys._getframe().f_code.co_name,
                                                                      repr(v), repr(vars[v])))
                else:
                    logger.info("[{}][{}] assign failed! ({} is not existed in vars)".format(self.__class__.__name__,
                                                                                             sys._getframe().f_code.co_name,
                                                                                             repr(v)))

    def run_print(self, sobj, args, depth=0):
        logger = self._logger
        cmd = sobj[0]
        cargs = sobj[1] if len(sobj) > 1 else None
        csub = sobj[2] if len(sobj) > 2 else None

        cl = [cargs] if isinstance(cargs, str) else cargs if isinstance(cargs, list) else None
        if cl is not None:
            print_list = []
            for k in cl:
                v = args.vars.get(k)
                print_list.append("{} -> {}".format(repr(k), repr(v)))
            logger.info("[{}][{}] {}".format(self.__class__.__name__,
                                             sys._getframe().f_code.co_name,
                                             ", ".join(print_list)))

        return None

    def run_msg(self, sobj, args, depth=0):
        logger = self._logger
        cmd = sobj[0]
        cargs = sobj[1] if len(sobj) > 1 else None
        csub = sobj[2] if len(sobj) > 2 else None

        msg = cargs
        logger.info("[{}][{}] {}".format(self.__class__.__name__,
                                         sys._getframe().f_code.co_name,
                                         str(msg)))

        return None

    def run_call(self, sobj, args, depth=0):
        logger = self._logger
        cmd = sobj[0]
        cargs = sobj[1] if len(sobj) > 1 else None
        csub = sobj[2] if len(sobj) > 2 else None

        cl = [cargs] if isinstance(cargs, str) else cargs if isinstance(cargs, list) else None
        if cl is not None:
            for k in cl:
                v = args.vars.get(k)
                if isinstance(v, list):
                    logger.info("[{}][{}] calling sub script list {}...".format(self.__class__.__name__,
                                                                                sys._getframe().f_code.co_name,
                                                                                repr(k)))
                    sub_sobj = v
                    self.execute_script(sub_sobj, args, depth + 1)
                else:
                    logger.info("[{}][{}] {} is not a sub script list!".format(self.__class__.__name__,
                                                                               sys._getframe().f_code.co_name, repr(k)))

        return None

    def run_except(self, sobj, args, depth=0):
        logger = self._logger
        cmd = sobj[0]
        cargs = sobj[1] if len(sobj) > 1 else None
        csub = sobj[2] if len(sobj) > 2 else None

        E = self._exceptions_map.get(cmd)
        if E is not None:
            logger.debug("[{}][{}] {} requested!".format(self.__class__.__name__,
                                                         sys._getframe().f_code.co_name,
                                                         cmd))
            raise E()

        return None

    def run_callback(self, sobj, args, depth=0):
        logger = self._logger
        cmd = sobj[0]
        cargs = sobj[1] if len(sobj) > 1 else None
        csub = sobj[2] if len(sobj) > 2 else None

        callback = self._callback
        if callback is not None:
            logger.debug("[{}][{}] callback requested!".format(self.__class__.__name__,
                                                               sys._getframe().f_code.co_name))
            callback()

        return None

    def run_assert(self, sobj, args, depth=0):
        logger = self._logger
        cmd = sobj[0]
        cargs = sobj[1] if len(sobj) > 1 else None
        csub = sobj[2] if len(sobj) > 2 else None

        assert_result = True
        var = None
        v = None
        afunc = None
        afunc_name = ''
        if isinstance(cargs, dict):
            var = cargs.get(self.ARG_VAR)
            if var is not None:
                if isinstance(var, str):
                    var = [var]
                if not isinstance(var, list):
                    raise RuntimeError("'var' is not valid!")

                v = [args.vars.get(i) for i in var]
                for af in self.AFUNC_PREFER:
                    if af in cargs:
                        afunc_name = af
                        afunc = self.AFUNC_MAP.get(af)
                        break
                else:
                    logger.debug("[{}][{}] will have no effects on var {}".format(self.__class__.__name__,
                                                                                  sys._getframe().f_code.co_name,
                                                                                  repr(var)))
        elif isinstance(cargs, list):
            var = cargs
            v = [args.vars.get(i) for i in var]
        elif isinstance(cargs, str):
            var = [cargs]
            v = [args.vars.get(i) for i in var]

        logger.debug("[{}][{}] proceeding{}...".format(self.__class__.__name__,
                                                       sys._getframe().f_code.co_name,
                                                       ' ' + afunc_name if afunc_name else ''))
        if afunc is not None:
            afargs = cargs.get(afunc_name)
            for vi in v:
                assert_result = assert_result and afunc(vi, afargs)
                if not assert_result:
                    break
        else:
            for vi in v:
                a = True if vi else False
                assert_result = assert_result and a
                if not assert_result:
                    break

        if assert_result and csub:
            logger.debug("[{}][{}] assert result is True!".format(self.__class__.__name__,
                                                                  sys._getframe().f_code.co_name))
            self.execute_script(csub, args, depth + 1)

        return None

    def run_jsonpath(self, sobj, args, depth=0):
        logger = self._logger
        cmd = sobj[0]
        cargs = sobj[1] if len(sobj) > 1 else None
        csub = sobj[2] if len(sobj) > 2 else None

        # ['var', 'json_path'], or ['var', 'json_path', 'dest_var']
        var, jpath = cargs
        dest_var = cargs[2] if len(cargs) > 2 else var

        value = args.vars.get(var)
        parser = jp.parse(jpath)
        result = [match.value for match in parser.find(value)]
        args.vars[dest_var] = result

        return None

    def run_xpath(self, sobj, args, depth=0):
        logger = self._logger
        cmd = sobj[0]
        cargs = sobj[1] if len(sobj) > 1 else None
        csub = sobj[2] if len(sobj) > 2 else None

        # ['var', 'xpath'], or ['var', 'xpath', 'dest_var']
        var, xpath = cargs
        dest_var = cargs[2] if len(cargs) > 2 else var

        value = args.vars.get(var)
        et = et_fromstring(value)
        result = et.xpath(xpath)
        args.vars[dest_var] = result

        return None

    def run_read(self, sobj, args, depth=0):
        logger = self._logger
        cmd = sobj[0]
        cargs = sobj[1] if len(sobj) > 1 else None
        csub = sobj[2] if len(sobj) > 2 else None

        v = None
        if isinstance(cargs, dict):
            file_name = cargs.get(self.ARG_FILE_NAME)
            encoding = cargs.get(self.ARG_ENCODING)
            encoding = encoding if encoding is not None else self._data_encoding
            var = cargs.get(self.ARG_VAR)
            if None not in {file_name, var}:
                with open(file_name, "r", encoding=encoding) as fp:
                    # TODO auto load as json object?
                    args.vars[var] = fp.read()
                    logger.info("[{}][{}] file content of {} is loaded into variable {}".format(self.__class__.__name__,
                                                                                       sys._getframe().f_code.co_name,
                                                                                       repr(file_name), repr(var)))
            else:
                raise RuntimeError("'file_name' or 'var' is not valid!")

        return None

    def run_write(self, sobj, args, depth=0):
        logger = self._logger
        cmd = sobj[0]
        cargs = sobj[1] if len(sobj) > 1 else None
        csub = sobj[2] if len(sobj) > 2 else None

        v = None
        if isinstance(cargs, dict):
            file_name = cargs.get(self.ARG_FILE_NAME)
            encoding = cargs.get(self.ARG_ENCODING)
            encoding = encoding if encoding is not None else self._data_encoding
            var = cargs.get(self.ARG_VAR)
            if None not in {file_name, var}:
                mode = "a" if cmd == self.CMD_APPEND else "w"
                with open(file_name, mode, encoding=encoding) as fp:
                    # TODO auto dump as json string?
                    fp.write(args.vars[var])
                    logger.info("[{}][{}] value of variable {} is written into file {}".format(self.__class__.__name__,
                                                                                       sys._getframe().f_code.co_name,
                                                                                       repr(var), repr(file_name)))
            else:
                raise RuntimeError("'file_name' or 'var' is not valid!")

        return None


if __name__ == "__main__":
    # TODO For debugging
    script = r"""
    [
        ['msg', 'part 1'],
        ['vars', { a: 1, b: 2, c: 'hello world!', d: { xxx: 1, yyy: 2, zzz: 'hey!' } }],
        ['vars', { test_call: [ ['print', 'a'] ] }],
        ['call', 'test_call'],
        ['msg', 'part 2'],
        ['print', ['a', 'b']],
        ['print', ['d']],
        ['assign', { e: 'd' }],
        ['print', ['e']],
        ['assert', 'a', ['print', 'a'] ],
        ['assert', 'b', ['print', ['b']] ],
        ['assert', 'c', [ ['print', ['c']]] ],
        ['msg', 'part 3'],
        ['assert', ['a', 'b', 'c'], ['print', 'c'] ],
        ['assert', { 'var': 'c', 're': 'hello', }, ['print', 'c']],
    ]
    """
    t = TinyEngine(script=script)
    t.run()
