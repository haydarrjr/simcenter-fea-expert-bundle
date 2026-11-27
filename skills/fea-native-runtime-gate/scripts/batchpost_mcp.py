"""Start an isolated BatchPost worker and attach the official stdio connector."""
import argparse
from contextlib import contextmanager
import os
from pathlib import Path
from queue import Empty, Queue
import subprocess
import sys
from threading import Thread
from time import monotonic
from uuid import uuid4


def message(text):
    print('BatchPost: ' + text, file=sys.stderr, flush=True)


@contextmanager
def owned_process(argv, **options):
    process = subprocess.Popen(argv, creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0), **options)
    try:
        yield process
    finally:
        if process.poll() is None:
            process.terminate()
            process.wait(timeout=5)
        for stream in (process.stdin, process.stdout):
            if stream:
                stream.close()


def await_pipe(worker, pipe, timeout, start):
    lines = Queue()

    def consume():
        ready_marker = False
        ready = False
        try:
            for raw in worker.stdout:
                text = raw.decode(errors='replace').strip()
                if text:
                    message(text)
                if not ready:
                    if text.startswith('MCP ready to connect'):
                        ready_marker = True
                    elif ready_marker and text == pipe:
                        ready = True
                        lines.put(True)
        finally:
            lines.put(False)

    Thread(target=consume, daemon=True).start()
    try:
        if not lines.get(timeout=max(0, start + timeout - monotonic())):
            raise RuntimeError('worker output closed before announcing pipe readiness')
    except Empty as exc:
        raise TimeoutError(f'worker did not announce pipe readiness within {timeout:g} s') from exc


def run(base, timeout):
    if not base.is_absolute() or not 0 < timeout <= 120:
        raise ValueError('choose an absolute product location and a startup timeout in (0, 120]')
    binaries = base / 'NXBIN'
    worker = binaries / 'sc3d_batchpost.exe'
    connector = binaries / 'sc3d_batchpost_mcpconnector.exe'
    for executable in (worker, connector):
        if not executable.is_file():
            raise FileNotFoundError(executable)
    env = {**os.environ, 'UGII_BASE_DIR': str(base)}
    pipe = 'sc3d_batchpost_' + uuid4().hex
    pipe_args = ['--mcp-pipe-name', pipe]
    start = monotonic()
    with owned_process([str(worker), '--mcp', *pipe_args], env=env, stdin=subprocess.PIPE,
                       stdout=subprocess.PIPE, stderr=subprocess.STDOUT) as backend:
        await_pipe(backend, pipe, timeout, start)
        message(f'worker ready after {monotonic() - start:.2f} s; native pid={backend.pid}; attaching official connector')
        with owned_process([str(connector), *pipe_args], env=env, stdin=subprocess.PIPE) as server:
            def forward():
                try:
                    while chunk := sys.stdin.buffer.read1(65536):
                        server.stdin.write(chunk)
                        server.stdin.flush()
                except (BrokenPipeError, OSError, ValueError):
                    pass
                finally:
                    server.stdin.close()

            Thread(target=forward, daemon=True).start()
            while True:
                try:
                    return server.wait(timeout=0.5)
                except subprocess.TimeoutExpired:
                    if backend.poll() is not None:
                        raise RuntimeError(f'worker exited while serving MCP ({backend.returncode})')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--ugii-base-dir', default=os.getenv('UGII_BASE_DIR'), type=Path)
    parser.add_argument('--startup-timeout', default=55.0, type=float)
    args = parser.parse_args()
    if args.ugii_base_dir is None:
        parser.error('choose the installed Siemens product directory')
    try:
        raise SystemExit(run(args.ugii_base_dir, args.startup_timeout))
    except (OSError, RuntimeError, ValueError, subprocess.SubprocessError) as exc:
        message(str(exc))
        raise SystemExit(1) from None
