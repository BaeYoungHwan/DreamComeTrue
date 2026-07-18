from streamlit.testing.v1 import AppTest


def test_app_runs_without_exception():
    at = AppTest.from_file("app.py")
    at.run()

    assert not at.exception
    assert at.title[0].value == "로컬 팜 인벤토리"
