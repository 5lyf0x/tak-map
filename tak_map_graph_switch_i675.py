"""TAK Map i675: operator-authorized, reversible local Valhalla graph switching.

Never downloads external URLs or accepts filesystem paths from HTTP clients.
The existing NDM catalog is the only source of eligible graph identifiers.
The privileged operation is limited to restarting the fixed Valhalla systemd unit.
"""
import json
import os
from pathlib import Path
import re
import subprocess
import threading
import time
import urllib.request

from ndm_packages_i651 import Catalog, NDMError, _LOCK
from ndm_valhalla_i651 import prepare_graph, _version_ok, _wheel_binary, SERVICE_PORT

_ID = re.compile(r'^[0-9a-f]{64}$')
_RESTART = ('sudo', '-n', '/usr/local/sbin/tak-map-action', 'route-graph-restart-i675')


class GraphSwitcher:
    def __init__(self, catalog=None, prepare=None, restart=None, ready=None):
        self.catalog = catalog if catalog is not None else Catalog()
        self.prepare = prepare if prepare is not None else prepare_graph
        self.restart = restart if restart is not None else self._restart_service
        self.ready = ready if ready is not None else self._wait_ready
        self.lock = threading.Lock()
        self.job = {'status': 'idle', 'dataset_id': '', 'error': ''}

    @staticmethod
    def _restart_service():
        proc = subprocess.run(_RESTART, capture_output=True, text=True, timeout=45)
        if proc.returncode != 0:
            raise NDMError('Unable to restart the local Valhalla service: ' +
                           (proc.stderr or proc.stdout or 'service operation failed')[:180], 'ROUTER_RESTART')

    @staticmethod
    def _wait_ready():
        for _ in range(45):
            try:
                with urllib.request.urlopen('http://127.0.0.1:%d/status' % SERVICE_PORT, timeout=2) as resp:
                    if resp.status == 200:
                        return True
            except (OSError, ValueError):
                pass
            time.sleep(1)
        return False

    def options(self):
        datasets = []
        for entry in self.catalog.listing():
            if entry.get('type') != 'routing' or entry.get('valhalla_version') != '3.6.3':
                continue
            if not entry.get('available') or entry.get('superseded'):
                continue
            datasets.append({'dataset_id': entry['dataset_id'],
                             'label': str(entry.get('region') or entry.get('region_id') or 'Routing graph')[:80],
                             'region_id': entry.get('region_id', ''),
                             'active': bool(entry.get('active')),
                             'bounds': entry.get('bounds')})
        datasets.sort(key=lambda e: (not e['active'], e['label'].lower(), e['dataset_id']))
        with self.lock:
            status = dict(self.job)
        return {'ok': True, 'datasets': datasets,
                'active_dataset_id': next((d['dataset_id'] for d in datasets if d['active']), ''),
                'switch': status}

    def start(self, dataset_id):
        if not isinstance(dataset_id, str) or not _ID.fullmatch(dataset_id):
            raise NDMError('Invalid routing package identifier', 'INVALID_DATASET')
        row = self.catalog.detail(dataset_id)
        if not row or row.get('type') != 'routing' or row.get('valhalla_version') != '3.6.3':
            raise NDMError('Only registered Valhalla 3.6.3 routing packages may be activated', 'NO_GRAPH')
        if not _version_ok(_wheel_binary()):
            raise NDMError('Valhalla 3.6.3 executable is not ready', 'ROUTER_UNAVAILABLE')
        with self.lock:
            if self.job['status'] in ('preparing', 'restarting'):
                raise NDMError('A routing package switch is already in progress', 'SWITCH_BUSY')
            if any(d.get('dataset_id') == dataset_id and d.get('active') for d in self.catalog.listing()):
                self.job = {'status': 'ready', 'dataset_id': dataset_id, 'error': ''}
                return {'ok': True, 'already_active': True, **self.job}
            self.job = {'status': 'preparing', 'dataset_id': dataset_id, 'error': ''}
        worker = threading.Thread(target=self._switch, args=(dataset_id,), daemon=True,
                                  name='tak-map-route-graph-switch-i675')
        worker.start()
        return {'ok': True, 'accepted': True, 'status': 'preparing', 'dataset_id': dataset_id}

    def _status(self, status, dataset_id, error=''):
        with self.lock:
            self.job = {'status': status, 'dataset_id': dataset_id, 'error': str(error)[:350]}

    def _switch(self, dataset_id):
        # Keep the old service running while validating, hashing and extracting a
        # potentially multi-GiB graph archive. Never change systemd until ready.
        active_dir = self.catalog.root / 'active'
        cfg_path = active_dir / 'valhalla.json'
        id_path = active_dir / 'dataset-id'
        previous_cfg = None
        previous_id = None
        wrote_config = False
        try:
            previous_cfg = cfg_path.read_bytes() if cfg_path.is_file() else None
            previous_id = id_path.read_bytes() if id_path.is_file() else None
            self.prepare(self.catalog, dataset_id)
            prepared = self.catalog.root / 'prepared' / (dataset_id + '.json')
            new_config = prepared.read_bytes()
            cfg = json.loads(new_config)
            extract = Path(str(cfg['mjolnir']['tile_extract']))
            if not extract.is_file() or not extract.stat().st_size:
                raise NDMError('Prepared Valhalla archive is missing', 'NO_GRAPH')
            active_dir.mkdir(mode=0o750, parents=True, exist_ok=True)
            self._status('restarting', dataset_id)
            self._atomic(cfg_path, new_config)
            wrote_config = True
            self._atomic(id_path, (dataset_id + '\n').encode())
            self.restart()
            if not self.ready():
                raise NDMError('Selected graph did not become ready; restoring prior graph', 'ROUTER_UNAVAILABLE')
            with _LOCK:
                data = self.catalog._load()
                if dataset_id not in data['datasets']:
                    raise NDMError('Routing package was unregistered during switching', 'NOT_FOUND')
                for key, row in data['datasets'].items():
                    row['active'] = (key == dataset_id)
                self.catalog._save(data)
            self._status('ready', dataset_id)
        except Exception as exc:
            if wrote_config:
                try:
                    self._restore(cfg_path, previous_cfg)
                    self._restore(id_path, previous_id)
                    self.restart()
                    # Keep the catalog's original active record on failure.
                except Exception as rollback_exc:
                    self._status('error', dataset_id,
                                 str(exc) + '; rollback needs operator attention: ' + str(rollback_exc))
                    return
            self._status('error', dataset_id, exc)

    @staticmethod
    def _atomic(path, content):
        import tempfile
        fd, temporary = tempfile.mkstemp(prefix='.route-graph-', dir=path.parent)
        try:
            with os.fdopen(fd, 'wb') as output:
                output.write(content)
                output.flush()
                os.fsync(output.fileno())
            os.chmod(temporary, 0o640)
            os.replace(temporary, path)
        finally:
            if os.path.exists(temporary):
                os.unlink(temporary)

    @staticmethod
    def _restore(path, content):
        if content is None:
            path.unlink(missing_ok=True)
        else:
            GraphSwitcher._atomic(path, content)
