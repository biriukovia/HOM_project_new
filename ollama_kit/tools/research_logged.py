"""Instrumented copy of the course MCP; stores real replies, never synthetic provenance."""
import functools, importlib.util, json, os, sys, datetime, typing
from pathlib import Path
original = Path(__file__).resolve().parents[1] / 'week5/research_mcp.py'
# Execute the course module, wrapping registrations before functions are registered.
from mcp.server.fastmcp import FastMCP
register = FastMCP.tool

def logged_tool(self, *args, **kwargs):
    decorate = register(self, *args, **kwargs)
    def wrap(fn):
        @functools.wraps(fn)
        def call(*a, **kw):
            record = {'time': datetime.datetime.now().astimezone().isoformat(),
                      'tool': fn.__name__, 'args': a, 'kwargs': kw}
            try:
                reply = fn(*a, **kw)
                try: record['response'] = json.loads(reply)
                except (TypeError, ValueError): record['response'] = reply
                return reply
            except Exception as exc:
                # Avoid storing exception strings which could contain credential-bearing URLs.
                record['error_type'] = type(exc).__name__
                raise
            finally:
                target = os.environ.get('HOM_RESEARCH_LOG')
                if target:
                    text = json.dumps(record, ensure_ascii=False, default=str)
                    for key in ('OPENALEX_API_KEY', 'OPEN_ALEX'):
                        secret = os.environ.get(key)
                        if secret: text = text.replace(secret, '[REDACTED]')
                    with open(target, 'a', encoding='utf-8') as f: f.write(text + '\n')
        call.__annotations__ = typing.get_type_hints(fn)
        return decorate(call)
    return wrap
FastMCP.tool = logged_tool
spec = importlib.util.spec_from_file_location('course_research', original)
module = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = module
spec.loader.exec_module(module)
FastMCP.tool = register
if __name__ == '__main__': module.mcp.run()
