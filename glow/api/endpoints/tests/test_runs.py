import json
import typing
import uuid

# Third-party
import flask.testing

# Glow
from glow.api.tests.fixtures import test_client  # noqa: F401
from glow.db.tests.fixtures import test_db, make_run  # noqa: F401
from glow.db.queries import create_run


def test_list_runs_empty(test_client: flask.testing.FlaskClient):  # noqa: F811
    results = test_client.get("/api/v1/runs?limit=3")

    assert results.json == dict(
        current_page_url="http://localhost/api/v1/runs?limit=3",
        next_page_url=None,
        limit=3,
        next_cursor=None,
        after_cursor_count=0,
        content=[],
    )


def test_list_runs(test_client: flask.testing.FlaskClient):  # noqa: F811
    created_runs = [create_run(make_run()) for _ in range(5)]

    # Sort by latest
    created_runs = sorted(created_runs, key=lambda run: run.created_at, reverse=True)

    results = test_client.get("/api/v1/runs?limit=3")

    payload = results.json
    payload = typing.cast(typing.Dict[str, typing.Any], payload)

    assert len(payload["next_page_url"]) > 0
    assert len(payload["next_cursor"]) > 0
    assert payload["after_cursor_count"] == len(created_runs)
    assert payload["content"] == [run.to_json_encodable() for run in created_runs[:3]]

    next_page_url = payload["next_page_url"]
    next_page_url = next_page_url.split("localhost")[1]

    results = test_client.get(next_page_url)
    payload = results.json
    payload = typing.cast(typing.Dict[str, typing.Any], payload)

    assert payload["next_page_url"] is None
    assert payload["next_cursor"] is None
    assert payload["after_cursor_count"] == 2
    assert payload["content"] == [run.to_json_encodable() for run in created_runs[3:]]


def test_group_by(test_client: flask.testing.FlaskClient):  # noqa: F811
    runs = dict(RUN_A=[make_run(), make_run()], RUN_B=[make_run(), make_run()])

    for name, runs_ in runs.items():
        for run in runs_:
            run.name = name
            create_run(run)

    results = test_client.get("/api/v1/runs?group_by=name")

    payload = results.json
    payload = typing.cast(typing.Dict[str, typing.Any], payload)

    assert len(payload["content"]) == 2
    assert {run["name"] for run in payload["content"]} == set(runs)


def test_filters(test_client: flask.testing.FlaskClient):  # noqa: F811
    runs = make_run(), make_run()
    runs[0].parent_id = uuid.uuid4().hex

    for run in runs:
        create_run(run)

    for run in runs:
        filters = json.dumps({"parent_id": {"eq": run.parent_id}})

        results = test_client.get("/api/v1/runs?filters={}".format(filters))

        payload = results.json
        payload = typing.cast(typing.Dict[str, typing.Any], payload)

        assert len(payload["content"]) == 1
        assert payload["content"][0]["id"] == run.id
