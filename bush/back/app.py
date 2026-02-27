import argparse
import json
import threading
import urllib.parse
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path


class MarkdownRequestHandler(BaseHTTPRequestHandler):
    api_root = Path('.').resolve()

    def _send_json(self, status, payload):
        body = json.dumps(payload).encode('utf-8')
        self.send_response(status)
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.send_header('Content-Length', str(len(body)))
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET,PUT,OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
        self.wfile.write(body)

    def _read_json(self):
        length = int(self.headers.get('Content-Length', '0'))
        raw = self.rfile.read(length)
        if not raw:
            return {}
        return json.loads(raw.decode('utf-8'))

    @classmethod
    def _resolve_path(cls, rel_path):
        if not rel_path:
            raise ValueError('missing path')
        path = (cls.api_root / rel_path).resolve()
        if not path.is_relative_to(cls.api_root):
            raise ValueError('invalid path')
        return path

    @classmethod
    def _resolve_markdown_path(cls, rel_path):
        path = cls._resolve_path(rel_path)
        if path.suffix.lower() != '.md':
            raise ValueError('only .md files are allowed')
        return path

    @classmethod
    def _resolve_log_path(cls, rel_path):
        path = cls._resolve_path(rel_path)
        if path.suffix.lower() not in {'.log', '.txt'}:
            raise ValueError('only .log and .txt files are allowed')
        return path

    def _build_tree(self, root, suffixes):
        entries = []
        for child in sorted(root.iterdir(), key=lambda p: (p.is_file(), p.name.lower())):
            if child.name.startswith('.'):
                continue
            if child.is_dir():
                subtree = self._build_tree(child, suffixes)
                if subtree:
                    entries.append({'type': 'dir', 'name': child.name, 'children': subtree})
            elif child.suffix.lower() in suffixes:
                entries.append(
                    {
                        'type': 'file',
                        'name': child.name,
                        'path': child.relative_to(self.api_root).as_posix(),
                    }
                )
        return entries

    def _read_log_chunk(self, path, offset, limit):
        with path.open('rb') as fh:
            fh.seek(offset)
            data = fh.read(limit)
            next_offset = fh.tell()
        return data.decode('utf-8', errors='replace'), next_offset

    def do_OPTIONS(self):
        self._send_json(HTTPStatus.OK, {'ok': True})

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        if parsed.path == '/api/tree':
            return self._send_json(HTTPStatus.OK, {'root': self.api_root.name, 'items': self._build_tree(self.api_root, {'.md'})})
        if parsed.path == '/api/logs/tree':
            return self._send_json(HTTPStatus.OK, {'root': self.api_root.name, 'items': self._build_tree(self.api_root, {'.log', '.txt'})})
        if parsed.path == '/api/file':
            params = urllib.parse.parse_qs(parsed.query)
            rel_path = params.get('path', [''])[0]
            try:
                path = self._resolve_markdown_path(rel_path)
                content = path.read_text(encoding='utf-8')
            except FileNotFoundError:
                return self._send_json(HTTPStatus.NOT_FOUND, {'error': 'not found'})
            except ValueError as exc:
                return self._send_json(HTTPStatus.BAD_REQUEST, {'error': str(exc)})
            return self._send_json(HTTPStatus.OK, {'path': rel_path, 'content': content})
        if parsed.path == '/api/log':
            params = urllib.parse.parse_qs(parsed.query)
            rel_path = params.get('path', [''])[0]
            try:
                offset = max(0, int(params.get('offset', ['0'])[0]))
                limit = min(262144, max(1, int(params.get('limit', ['65536'])[0])))
                path = self._resolve_log_path(rel_path)
                size = path.stat().st_size
                if offset > size:
                    offset = size
                content, next_offset = self._read_log_chunk(path, offset, limit)
            except FileNotFoundError:
                return self._send_json(HTTPStatus.NOT_FOUND, {'error': 'not found'})
            except (ValueError, OSError) as exc:
                return self._send_json(HTTPStatus.BAD_REQUEST, {'error': str(exc)})
            return self._send_json(
                HTTPStatus.OK,
                {
                    'path': rel_path,
                    'offset': offset,
                    'next_offset': next_offset,
                    'size': size,
                    'eof': next_offset >= size,
                    'content': content,
                },
            )
        self._send_json(HTTPStatus.NOT_FOUND, {'error': 'not found'})

    def do_PUT(self):
        parsed = urllib.parse.urlparse(self.path)
        if parsed.path != '/api/file':
            return self._send_json(HTTPStatus.NOT_FOUND, {'error': 'not found'})
        try:
            payload = self._read_json()
            path = self._resolve_markdown_path(payload.get('path', ''))
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(payload.get('content', ''), encoding='utf-8')
        except json.JSONDecodeError:
            return self._send_json(HTTPStatus.BAD_REQUEST, {'error': 'invalid json'})
        except ValueError as exc:
            return self._send_json(HTTPStatus.BAD_REQUEST, {'error': str(exc)})
        return self._send_json(HTTPStatus.OK, {'ok': True, 'path': payload.get('path', '')})


def run_server(host='127.0.0.1', port=8000, root='.'):
    MarkdownRequestHandler.api_root = Path(root).resolve()
    httpd = ThreadingHTTPServer((host, port), MarkdownRequestHandler)
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        httpd.server_close()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--host', default='127.0.0.1')
    parser.add_argument('--port', default=8000, type=int)
    parser.add_argument('--root', default='.')
    args = parser.parse_args()
    run_server(args.host, args.port, args.root)


if __name__ == '__main__':
    main()


def _start_test_server(root, port):
    MarkdownRequestHandler.api_root = Path(root).resolve()
    httpd = ThreadingHTTPServer(('127.0.0.1', port), MarkdownRequestHandler)
    thread = threading.Thread(target=httpd.serve_forever, daemon=True)
    thread.start()
    return httpd, thread


def test_resolve_markdown_path_rejects_traversal(tmp_path):
    MarkdownRequestHandler.api_root = tmp_path
    handler = MarkdownRequestHandler
    try:
        handler._resolve_markdown_path('../bad.md')
        assert False
    except ValueError as exc:
        assert 'invalid path' in str(exc)


def test_get_tree_and_file_and_put(tmp_path):
    docs = tmp_path / 'docs'
    docs.mkdir()
    note = docs / 'a.md'
    note.write_text('one', encoding='utf-8')
    port = 8765
    httpd, _ = _start_test_server(tmp_path, port)
    try:
        import urllib.request

        tree_resp = urllib.request.urlopen(f'http://127.0.0.1:{port}/api/tree')
        tree = json.loads(tree_resp.read().decode('utf-8'))
        assert tree['items'][0]['type'] == 'dir'

        file_resp = urllib.request.urlopen(f'http://127.0.0.1:{port}/api/file?path=docs/a.md')
        data = json.loads(file_resp.read().decode('utf-8'))
        assert data['content'] == 'one'

        req = urllib.request.Request(
            f'http://127.0.0.1:{port}/api/file',
            method='PUT',
            data=json.dumps({'path': 'docs/a.md', 'content': 'two'}).encode('utf-8'),
            headers={'Content-Type': 'application/json'},
        )
        put_resp = urllib.request.urlopen(req)
        put_data = json.loads(put_resp.read().decode('utf-8'))
        assert put_data['ok'] is True
        assert note.read_text(encoding='utf-8') == 'two'
    finally:
        httpd.shutdown()
        httpd.server_close()


def test_reject_non_markdown_put(tmp_path):
    port = 8766
    httpd, _ = _start_test_server(tmp_path, port)
    try:
        import urllib.error
        import urllib.request

        req = urllib.request.Request(
            f'http://127.0.0.1:{port}/api/file',
            method='PUT',
            data=json.dumps({'path': 'x.txt', 'content': 'bad'}).encode('utf-8'),
            headers={'Content-Type': 'application/json'},
        )
        try:
            urllib.request.urlopen(req)
            assert False
        except urllib.error.HTTPError as exc:
            body = json.loads(exc.read().decode('utf-8'))
            assert exc.code == 400
            assert 'only .md files' in body['error']
    finally:
        httpd.shutdown()
        httpd.server_close()


def test_get_logs_tree_and_chunk(tmp_path):
    logs = tmp_path / 'logs'
    logs.mkdir()
    log_file = logs / 'app.log'
    log_file.write_text('first\nsecond\n', encoding='utf-8')
    port = 8767
    httpd, _ = _start_test_server(tmp_path, port)
    try:
        import urllib.request

        tree_resp = urllib.request.urlopen(f'http://127.0.0.1:{port}/api/logs/tree')
        tree = json.loads(tree_resp.read().decode('utf-8'))
        assert tree['items'][0]['name'] == 'logs'

        chunk_resp = urllib.request.urlopen(f'http://127.0.0.1:{port}/api/log?path=logs/app.log&offset=0&limit=6')
        chunk = json.loads(chunk_resp.read().decode('utf-8'))
        assert chunk['content'] == 'first\n'
        assert chunk['next_offset'] == 6
        assert chunk['eof'] is False
    finally:
        httpd.shutdown()
        httpd.server_close()
