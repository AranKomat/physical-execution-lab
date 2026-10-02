"""Versioned, loopback-only semantic-policy transport; no automatic retries."""
from __future__ import annotations
from dataclasses import asdict
from http.server import BaseHTTPRequestHandler, HTTPServer
import json
from k1lab.errors import ContractError
from k1lab.util import digest, plain
from k1lab.multibench.transport import RemotePolicy, PolicyDispatcher
from .contracts import SemanticContext

PROTOCOL = 'semantic-policy.v1'


def implementation_sha256():
    from pathlib import Path
    from k1lab.util import file_sha
    root = Path(__file__).resolve().parent
    return digest({name: file_sha(root / name) for name in ('contracts.py', 'policy.py', 'transport.py')})


class SemanticRemotePolicy(RemotePolicy):
    def __init__(self, config, **kwargs):
        super().__init__(config, **kwargs)
        if (self.server_info.get('semantic_protocol') != PROTOCOL or
                self.server_info.get('semantic_implementation_sha256') != implementation_sha256()):
            self.close()
            raise ContractError('use run_semantic.py serve-policy; legacy server lacks language conditioning')

    def set_context(self, context):
        return self._call('semantic_context', {'context': asdict(context)})

    def finish_prefix(self, executed, reason='natural_boundary'):
        return self._call('finish_prefix', {'executed': executed, 'reason': reason})


class SemanticDispatcher(PolicyDispatcher):
    def dispatch(self, envelope):
        req = envelope['request']
        if digest(req) != envelope['request_sha256']:
            raise ContractError('request digest mismatch')
        if req['op'] not in ('semantic_context', 'finish_prefix'):
            result = super().dispatch(envelope)
            if req['op'] == 'acquire':
                result['result']['semantic_protocol'] = PROTOCOL
                result['result']['semantic_implementation_sha256'] = implementation_sha256()
            return result
        if self.poisoned or req['owner'] != self.owner or req['seq'] != self.seq:
            raise ContractError('owner/sequence/poisoned state mismatch')
        try:
            if req['op'] == 'semantic_context':
                result = self.policy.set_context(SemanticContext(**req['args']['context']))
            else:
                result = self.policy.finish_prefix(**req['args'])
            self.seq += 1
            return {'request_sha256': envelope['request_sha256'], 'result': plain(result)}
        except Exception:
            self.poisoned = True
            raise


def serve(policy, port, load_seconds=None):
    state = SemanticDispatcher(policy, load_seconds)
    class Handler(BaseHTTPRequestHandler):
        def do_POST(self):
            if self.path != '/rpc':
                self.send_error(404)
                return
            try:
                n = int(self.headers.get('Content-Length', '0'))
                if not 0 < n <= 24_000_000:
                    raise ContractError('request size bound')
                body = state.dispatch(json.loads(self.rfile.read(n)))
                code = 200
            except Exception as exc:
                body = {'error': f'{type(exc).__name__}: {str(exc)[:400]}'}
                code = 409
            raw = json.dumps(plain(body), allow_nan=False).encode()
            self.send_response(code)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Content-Length', str(len(raw)))
            self.end_headers()
            self.wfile.write(raw)
        def log_message(self, *_):
            pass
    with HTTPServer(('127.0.0.1', int(port)), Handler) as server:
        print(json.dumps({'ready': True, 'port': port, 'semantic_protocol': PROTOCOL,
                          'identity': policy.identity.identity}), flush=True)
        try:
            server.serve_forever()
        finally:
            policy.close()
