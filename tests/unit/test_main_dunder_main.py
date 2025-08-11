import runpy

def test_dunder_main_calls_uvicorn(monkeypatch):
    called = {}
    def fake_run(*args, **kwargs):
        called["ok"] = (args, kwargs)

    # Patch before running module as __main__
    monkeypatch.setattr("uvicorn.run", fake_run)

    runpy.run_module("app.main", run_name="__main__")
    assert "ok" in called
