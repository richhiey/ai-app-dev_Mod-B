import json
import pytest
from module_b.data import load_fixture, load_json, load_jsonl
from module_b.source import source_excerpt, source_text


def test_different_layout_and_json_shapes(tmp_path):
    (tmp_path/'cases').mkdir()
    (tmp_path/'cases/items.json').write_text('[{"sku": "A"}, {"sku": "B"}]')
    assert load_fixture(tmp_path, 'items', directory='cases') == [{'sku':'A'}, {'sku':'B'}]
    (tmp_path/'scalar.json').write_text('false')
    assert load_json(tmp_path, 'scalar.json') is False
    (tmp_path/'events.jsonl').write_text('{"request_id":"1"}\n\n{"status":429}\n')
    assert load_jsonl(tmp_path,'events.jsonl') == [{'request_id':'1'}, {'status':429}]


def test_jsonl_failure_names_line_without_echoing_payload(tmp_path):
    (tmp_path/'events.jsonl').write_text('{}\nprivate-invalid-content\n')
    with pytest.raises(ValueError,match='line 2') as error:
        load_jsonl(tmp_path, 'events.jsonl')
    assert 'private-invalid-content' not in str(error.value)


def test_readers_reject_links_traversal_and_private_paths(tmp_path):
    (tmp_path/'real.json').write_text('{}')
    (tmp_path/'alias.json').symlink_to(tmp_path/'real.json')
    (tmp_path/'.env.json').write_text('{}')
    for path in ['alias.json','../real.json','.env.json']:
        with pytest.raises(ValueError):
            load_json(tmp_path, path)


def test_python_package_and_ui_source_are_inspectable_without_execution(tmp_path):
    (tmp_path/'src/catalog').mkdir(parents=True)
    (tmp_path/'src/catalog/api.py').write_text('raise RuntimeError("Never execute")\n\ndef route():\n    return "catalog"\n')
    assert 'return "catalog"' in source_excerpt(tmp_path,'src/catalog/api.py','route', roots=('src',))
    (tmp_path/'web').mkdir()
    js='export const endpoint = "/v1/catalog";\n'
    (tmp_path/'web/client.ts').write_text(js)
    assert source_text(tmp_path,'web/client.ts', roots=('web',), suffixes=('.ts',)) == js
    with pytest.raises(ValueError):
        source_text(tmp_path,'web/client.ts', roots=('src',), suffixes=('.ts',))
    with pytest.raises(ValueError):
        source_text(tmp_path,'web/client.ts', roots=('web',), suffixes=('.css',))


def test_public_environment_template_can_be_inspected_explicitly(tmp_path):
    (tmp_path/'.env.example').write_text('EXAMPLE_KEY=\n')
    assert source_text(tmp_path,'.env.example', roots=('.',), suffixes=('.example',)) == 'EXAMPLE_KEY=\n'
    (tmp_path/'.ENV.local').write_text('EXAMPLE_KEY=synthetic\n')
    with pytest.raises(ValueError):
        source_text(tmp_path,'.ENV.local', roots=('.',), suffixes=('.local',))
