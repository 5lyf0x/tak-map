#!/usr/bin/env python3
from __future__ import annotations

import ast
import importlib.util
import os
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / 'tak_dashboard.py'


def is_main_guard(node: ast.AST) -> bool:
    if not isinstance(node, ast.If):
        return False
    test = node.test
    if not isinstance(test, ast.Compare) or len(test.ops) != 1 or len(test.comparators) != 1:
        return False
    left = test.left
    right = test.comparators[0]
    return (
        isinstance(test.ops[0], ast.Eq)
        and isinstance(left, ast.Name)
        and left.id == '__name__'
        and isinstance(right, ast.Constant)
        and right.value == '__main__'
    ) or (
        isinstance(test.ops[0], ast.Eq)
        and isinstance(right, ast.Name)
        and right.id == '__name__'
        and isinstance(left, ast.Constant)
        and left.value == '__main__'
    )


def main() -> None:
    source = SOURCE.read_text(encoding='utf-8')
    tree = ast.parse(source, filename=str(SOURCE))
    guards = [(i, n) for i, n in enumerate(tree.body) if is_main_guard(n)]
    assert len(guards) == 1, f'expected one __main__ guard, found {len(guards)}'
    index, guard = guards[0]
    assert index == len(tree.body) - 1, '__main__ guard must be the final module statement'
    assert len(guard.body) == 1 and isinstance(guard.body[0], ast.Expr), 'main guard must only call main()'
    call = guard.body[0].value
    assert isinstance(call, ast.Call) and isinstance(call.func, ast.Name) and call.func.id == 'main', 'main guard must call main()'

    # Importing under a non-__main__ name must apply every iteration patch without starting the server.
    with tempfile.TemporaryDirectory(prefix='tak-map-i533-entrypoint-') as td:
        os.environ['TAK_DASHBOARD_DATA_DIR'] = td
        spec = importlib.util.spec_from_file_location('tak_map_i533_entrypoint_test', SOURCE)
        module = importlib.util.module_from_spec(spec)
        assert spec.loader
        spec.loader.exec_module(module)
        assert module.TAK_MAP_ITERATION == 'i537'
        assert 'takMapSelfServiceIdentityI534' in module.TAK_MAP_HTML
        assert 'takMapPerUserDataSyncIdentityI529' not in module.TAK_MAP_HTML
        assert 'takMapPerUserDataSyncIdentityI531' not in module.TAK_MAP_HTML and 'takMapPerUserDataSyncIdentityI530' not in module.TAK_MAP_HTML
        assert hasattr(module, '_i531_send_per_user_cot')
        assert hasattr(module, '_i531_associate_uid')
        cfg = module.tak_map_config()
        assert cfg['tak_map_iteration'] == 'i537'
        assert cfg['data_sync_native_point_publish']['publish_mode'] == 'ots-confirmed-self-configured-persistent-per-user-cot-mission-uid-i534'

    print('i533 final-entrypoint ordering and active-patch tests passed')


if __name__ == '__main__':
    main()
