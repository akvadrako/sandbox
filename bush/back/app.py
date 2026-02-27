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

    def _resolve_markdown_path(self, rel_path):
        if not rel_path:
            raise ValueError('missing path')
        path = (self.api_root / rel_path).resolve()
        if not str(path).startswith(str(self.api_root)):
            raise ValueError('invalid path')
        if path.suffix.lower() != '.md':
            raise ValueError('only .md files are allowed')
        return path

    def _build_tree(self, root):
        entries = []
        for child in sorted(root.iterdir(), key=lambda p: (p.is_file(), p.name.lower())):
            if child.name.startswith('.'):
                continue
            if child.is_dir():
                subtree = self._build_tree(child)
                if subtree:
                    entries.append({'type': 'dir', 'name': child.name, 'children': subtree})
            elif child.suffix.lower() == '.md':
                entries.append(
                    {
                        'type': 'file',
                        'name': child.name,
                        'path': child.relative_to(self.api_root).as_posix(),
                    }
                )
        return entries

    def do_OPTIONS(self):
        self._send_json(HTTPStatus.OK, {'ok': True})

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        if parsed.path == '/api/tree':
            return self._send_json(HTTPStatus.OK, {'root': self.api_root.name, 'items': self._build_tree(self.api_root)})
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
        handler._resolve_markdown_path(handler, '../bad.md')
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
