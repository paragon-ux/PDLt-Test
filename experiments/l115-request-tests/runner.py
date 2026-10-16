"""The sandbox runner shared by evaluate.py and bound_tests.py: loads the deliverable as module "deliverable", then runs the request tests (test_* functions and TestCase methods) with a time limit each."""
PREFIX = "REQUEST_TESTS: "
RUNNER = r'''
import io as _io, json as _json, sys as _sys, threading as _threading, types as _types
_REAL = _sys.stdout
_sys.stdout = _io.StringIO()
_MOD = _types.ModuleType("deliverable")
NS = _MOD.__dict__
NS["__builtins__"] = __builtins__
_sys.modules["deliverable"] = _MOD
_load = []
for _i, _b in enumerate(__BLOCKS__):
    try:
        exec(compile(_b, "<deliverable %d>" % (_i + 1), "exec"), NS)
    except BaseException as _e:
        _load.append("%s: %s" % (type(_e).__name__, str(_e)[:150]))
import unittest as _unittest
_report = {"load_errors": _load, "tests": {}}
TNS = dict(NS)
try:
    exec(compile(__TESTS__, "<request tests>", "exec"), TNS)
except BaseException as _e:
    _report["module_error"] = "%s: %s" % (type(_e).__name__, str(_e)[:200])
_new = [k for k in TNS if k not in NS or TNS[k] is not NS[k]]
_cases = []
for _k in sorted(_new):
    _v = TNS[_k]
    if _k.startswith("test_") and callable(_v) and not isinstance(_v, type):
        _cases.append((_k, _v))
    elif isinstance(_v, type) and issubclass(_v, _unittest.TestCase):
        for _m in sorted(n for n in dir(_v) if n.startswith("test")):
            def _run_case(_cls=_v, _m=_m):
                _res = _unittest.TestResult()
                _cls(_m).run(_res)
                for _t, _tb in _res.errors + _res.failures:
                    raise AssertionError(_tb.strip().splitlines()[-1][:200])
            _cases.append(("%s.%s" % (_k, _m), _run_case))
for _name, _f in _cases:
    _out = {}
    def _t(_f=_f):
        try:
            _f(); _out["ok"] = True
        except BaseException as _e:
            _out["err"] = "%s: %s" % (type(_e).__name__, str(_e)[:200])
    _th = _threading.Thread(target=_t, daemon=True); _th.start(); _th.join(10)
    _report["tests"][_name] = "timeout" if _th.is_alive() else ("ok" if _out.get("ok") else _out.get("err", "failed"))
    if _th.is_alive():
        break
_REAL.write(__PREFIX__ + _json.dumps(_report) + "\n"); _REAL.flush()
'''
