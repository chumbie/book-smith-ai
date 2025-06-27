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
# Import Logging and config
import logging

# Standard Imports
import os
from sys import stderr
from unittest import mock

# Third Party Imports
import pytest

# Custom Imports
from book_smith_ai.module import PerplexityBookGenerator

logging.basicConfig(stream=stderr, level=logging.DEBUG)

# Constants
MOCK_API_KEY = "test_api_key"


@pytest.fixture
def test_book_idea_1():
    return """
    A lone radio operator on a decaying space station intercepts a
    signal from Earth—centuries after humanity was believed extinct.
    Is it a distress call, or something far more sinister?
    """


@pytest.fixture
def set_test_api_key(monkeypatch):
    monkeypatch.setenv("PERPLEXITY_API_KEY", MOCK_API_KEY)


class TestPyTest:
    def test_0_pass(self):
        assert 1 + 1 == 2

        def test_exception(self):
            with pytest.raises(SystemExit) as err:
                raise SystemExit(1)

    @pytest.mark.skip(reason="example of un-implemented test")
    def test_0_not_implemented(self): ...


class TestModule:
    def test_1_constructor_sets_correct_attributes(
        self, monkeypatch, set_test_api_key
    ):
        """Test attribute initialization with valid API key"""
        set_test_api_key
        mock_api_key = "test_api_key"
        book_idea = "Test book idea"
        generator = PerplexityBookGenerator(book_idea=book_idea)

        assert generator.api_key == mock_api_key
        assert generator.book_idea == book_idea
        assert (
            generator.base_url
            == "https://api.perplexity.ai/chat/completions"
        )
        assert generator.headers == {
            "Authorization": f"Bearer {mock_api_key}",
            "Content-Type": "application/json",
        }

    def test_2_constructor_raises_error_without_api_key(
        self, monkeypatch
    ):
        """Test ValueError when API key is missing"""
        monkeypatch.delenv("PERPLEXITY_API_KEY", raising=False)
        with pytest.raises(ValueError) as excinfo:
            PerplexityBookGenerator(book_idea="Test")
        assert "PERPLEXITY_API_KEY environment variable" in str(
            excinfo.value
        )

    def test_3_dict_to_namespace_conversion(self):
        """Test nested dictionary conversion to dot-accessible namespace"""
        test_data = {
            "key1": "value1",
            "nested": {"subkey": [1, 2, 3], "subdict": {"k": "v"}},
        }
        result = PerplexityBookGenerator._dict_to_namespace(test_data)
        assert result.key1 == "value1"
        assert result.nested.subkey == [1, 2, 3]
        assert result.nested.subdict.k == "v"

    @mock.patch("requests.post")
    def test_4_send_api_payload_success(
        self, mock_post, set_test_api_key
    ):
        """
        Test that PerplexityBookGenerator.send_api_payload returns the correct content
        when the API call is successful and the response is well-formed.
        """
        # Create a mock response object to simulate the result of
        # requests.post
        mock_response = mock.Mock()
        # Configure the mock to return a specific JSON structure
        # when .json() is called.
        # This structure mimics the actual API response expected by the
        # method.
        mock_response.json.return_value = {
            "choices": [{"message": {"content": "TEST_RESPONSE"}}]
        }
        # Simulate a successful HTTP response by making
        # .raise_for_status() do nothing.
        mock_response.raise_for_status.return_value = None
        # Set the mock_post (the patched requests.post) to
        # return our mock_response object.
        mock_post.return_value = mock_response

        # Instantiate the generator with a test book idea.
        # Note: api_key is fetched from the environment in the class,
        # so ensure it's set for the test.
        set_test_api_key
        generator = PerplexityBookGenerator(book_idea="test")

        # Call the method under test with a sample prompt.
        response = generator.send_api_payload("Test prompt")

        # Assert that the returned response matches the mocked content.
        assert response == "TEST_RESPONSE"
        # Assert that the requests.post function was called exactly
        # once.
        mock_post.assert_called_once()


class TestAPI:

    def test_book_spec_structure(self):
        """Test generated spec contains required keys"""
        generator = PerplexityBookGenerator(
            book_idea="test", dry_run=True
        )
        spec = generator.generate_book_spec()

        required_keys = {
            "expanded_title",
            "subtitle",
            "target_audience",
            "core_themes",
            "genre_classification",
            "word_count",
            "chapter_structure",
            "unique_selling_proposition",
        }
        assert set(spec.keys()) == required_keys
        assert isinstance(spec["core_themes"], list)
        assert "primary" in spec["target_audience"]
