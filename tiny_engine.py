# coding=utf-8

import traceback as tb
import types
import re
import json
import json5
from copy import deepcopy

import jsonpath
from lxml.etree import fromstring as et_fromstring
from lxml.html import fromstring as html_fromstring

from MiniUtils import get_logger

__version__ = "1.1.190710"


class TinyEngine:
    CMD_VARS = "vars"
    CMD_PRINT = "print"
    CMD_RERUN = "rerun"
    CMD_BREAK = "break"
    CMD_CALLBACK = "callback"
    CMD_ASSERT = "assert"
    CMD_READ = "read"
    CMD_WRITE = "write"

    # TODO jsonpath, xpath

    class Args:
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
        return self.var_replacer_raw(self.vars, v_str,
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

    def __init__(self, fp=None, script=None, encoding=None, logger=None, args=None, callback=None, **kwargs):
        self._fp = None
        self._script = None
        self._encoding = None

        self._logger = logger or get_logger()
        self._args = args or self.Args()
        self._callback = callback

        self._logger.debug("TinyEngine registering cmd runners...")
        self._cmd_runners = {}
        self.register_runners({
            self.CMD_VARS: None,
            self.CMD_PRINT: None,
            self.CMD_RERUN: None,
            self.CMD_BREAK: None,
            self.CMD_CALLBACK: None,
            self.CMD_ASSERT: None,
            self.CMD_READ: None,
            self.CMD_WRITE: None,
        })

        self._logger.debug("TinyEngine loading script...")
        self._script_obj = None
        if fp:
            self.load_from_file(fp, encoding)
        else:
            self.load_from_str(script)

        self._logger.debug("TinyEngine loaded. ({})".format(__version__))

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
        if sobj is None:
            sobj = self._script_obj
        args = self._args
        return self.execute_script(sobj, args)

    def execute_script(self, sobj, args, depth=0):
        logger = self._logger

        runners = self._cmd_runners
        if isinstance(sobj, list):
            if len(sobj) >= 1:
                cmd = sobj[0]
                if isinstance(cmd, str):
                    func = runners.get(cmd)
                    if func is not None:
                        logger.debug("Running cmd: {}".format(cmd))
                        return func(sobj, args, depth)
                else:
                    logger.debug("Running sub script (depth={})...".format(depth))
                    for sub_sobj in sobj:
                        self.execute_script(sub_sobj, args, depth + 1)
        return None

    def run_vars(self, sobj, args, depth=0):
        logger = self._logger
        cmd, cargs = sobj[:2]
        csub = sobj[2] if len(sobj) > 2 else None

        if isinstance(cargs, dict):
            vars = args.vars
            vars.update(cargs)


if __name__ == "__main__":
    # TODO For debugging
    pass
