# Unit Tests for module.py (book-smith-ai)
r"""
Get Into Testing Environment, cmd:
    cd "C:\Users\John.Weldon\OneDrive - Motion Recruitment Partners\Documents\Workato\projects\commissions_redesign" && .\venv\Scripts\activate

Get Into Testing Environment, linux cli:
    cd ~/path/to/project_folder && source .venv/bin/activate

Run Tests:
    (venv) $ cls && pytest -v


TODO: learn monkeypatch to mock class attributes, etc
https://docs.pytest.org/en/stable/how-to/monkeypatch.html

    Set VSCode to detect venv interpreter:
    https://stackoverflow.com/questions/66869413/visual-studio-code-does-not-detect-virtual-environments
    

        In VSCode open your command palette — Ctrl+Shift+P by default
        Look for Python: Select Interpreter
        In Select Interpreter choose Enter interpreter path... and then Find...
        Navigate to your venv folder — eg, ~/pyenvs/myenv/ or \Users\Foo\Bar\PyEnvs\MyEnv\
        In the virtual environment folder choose <your-venv-name>/bin/python or <your-venv-name>/bin/python3

    PyTest:
    https://realpython.com/pytest-python-testing/
    https://stackoverflow.com/questions/5626193/what-is-monkey-patching


        PyTest benchmarking:
        https://pytest-benchmark.readthedocs.io/en/stable/

        Requests Errors
        https://stackoverflow.com/questions/61463224/when-to-use-raise-for-status-vs-status-code-testing



"""


# Third Party Imports
import pytest

import logging
from sys import stderr
logging.basicConfig(stream=stderr, level=logging.DEBUG)

# Custom Imports
from book_smith_ai import module as bsai

@pytest.fixture
def test_book_idea_1():
    return """
    A lone radio operator on a decaying space station intercepts a 
    signal from Earth—centuries after humanity was believed extinct. 
    Is it a distress call, or something far more sinister?
    """

 
class TestPyTest:
    def test_pass(self):
        assert 1 + 1 == 2
        def test_exception(self):
            with pytest.raises(SystemExit) as err:
                raise SystemExit(1)
        
    @pytest.mark.skip(reason="example of un-implemented test")
    def test_not_implemented(self):
        ...
