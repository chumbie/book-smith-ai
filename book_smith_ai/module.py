# Core libraries for API interaction and content processing
import functools  # for spinner
import json  # conversion to/from JSON data object

# Import Logging and config
import logging
import os  # to get API key from environment

# Additional utilities
import re
import threading  # For spinner
import time
import types  # Import SimpleNamespace for dynamic type creation
import uuid
from datetime import datetime
from pathlib import Path
from sys import stderr
from typing import Any, Callable  # for spinner

import requests  # to send API requests

logging.basicConfig(stream=stderr, level=logging.DEBUG)


# CONSTANTS
TEST_CASE = 1


class PerplexityBookGenerator:
    # STEP 1: API Authorization and Setup
    def __init__(self, book_idea, dry_run=False):
        # Set this in Linux w/ $export PERPLEXITY_API_KEY=<your api key>
        self.api_key = os.getenv("PERPLEXITY_API_KEY")
        if not self.api_key:
            raise ValueError(
                "Please set the PERPLEXITY_API_KEY environment variable."
            )
        logging.debug("## API key detected")
        self.base_url = "https://api.perplexity.ai/chat/completions"
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        self.book_idea = book_idea
        # Will use stored tests/ data instead of calling LLM
        self.dry_run = dry_run
        if dry_run:
            logging.debug(
                "## dry_run=True, pulling data from file where present"
            )

    # Declares this method as static (no self/cls parameter needed)
    @staticmethod
    def _dict_to_namespace(data):
        """
        Recursively converts nested dictionaries/lists into
        dot-accessible namespaces.

        Args:
            data: Input data (dict, list, or primitive) to convert

        Returns:
            types.SimpleNamespace for dictionaries,
            processed list for lists,
            unchanged data for primitives
        """

        # Handle dictionary inputs: recursively process nested values
        if isinstance(data, dict):
            # Recursively convert each value in the dictionary
            converted = {
                k: PerplexityBookGenerator._dict_to_namespace(v)
                for k, v in data.items()
            }
            # Convert processed dictionary to namespace object
            return types.SimpleNamespace(**converted)

        # Handle list inputs: recursively process each item
        elif isinstance(data, list):
            # Recursively convert each element in the list
            return [
                PerplexityBookGenerator._dict_to_namespace(item)
                for item in data
            ]

        # Base case: return primitives unchanged (terminate recursion)
        else:
            return data

    def send_api_payload(
        self,
        prompt: str,
        role: str = "You are a helpful assistant.",
        model: str = "r1-1776",
        temp: float = 0.7,
        debug: bool = False,
    ) -> str:
        """Method to submit prompts to LLM"""

        self.payload = {
            "model": model,  # Use "sonar-pro" or another Pro model
            "messages": [
                {
                    "role": "system",
                    "content": role
                    + "Do not include any citations in your response. ",
                },
                {"role": "user", "content": prompt},
            ],
            "temperature": temp,
        }
        response = requests.post(
            self.base_url, headers=self.headers, json=self.payload
        )
        response.raise_for_status()  # Raises an error for bad status codes

        result = response.json()
        if debug:
            # Print full JSON responses
            print(
                f"Prompt: {prompt}",
                "Result:",
                json.dumps(result, indent=2),
                sep="\n",
            )
            # Do not remove <think> section via post-processing
            return result["choices"][0]["message"]["content"]
        else:
            return re.sub(
                # Removes <think> section from response
                r"<think>.*?</think>\s*",
                "",
                result["choices"][0]["message"]["content"],
                flags=re.DOTALL,
            )

    # Step 2: Go from book idea to comprehensive concept specification
    def generate_book_spec(self) -> dict:
        """
        Sends book concept to Perplexity, in order to create a
        specification of book elements to use further in the
        generation process
        """
        concept_prompt = f"""
        Based on this book idea: "{self.book_idea}"

        Please create a comprehensive book concept including:
        1. Expanded title and subtitle
        2. Target audience analysis
        3. Core themes and messages
        4. Genre classification
        5. Estimated word count and chapter structure
        6. Unique selling proposition

        Format your output strictly as JSON using the following structure:

        {{
        "expanded_title": "A clear, evocative full title for the work or concept.",
        "subtitle": "A one-sentence hook or tagline capturing the core premise.",
        "target_audience": {{
            "primary": "The main demographic or audience segment.",
            "secondary": [
            "List of secondary or niche audience segments."
            ],
            "key_interests": [
            "Key themes, tropes, or interests that appeal to the target audience."
            ]
        }},
        "core_themes": [
            "List of 4-6 central themes explored in the work."
        ],
        "genre_classification": {{
            "primary": "Main genre.",
            "secondary": [
            "List of secondary genres or subgenres."
            ],
            "tone": "Brief description of the story's tone or atmosphere."
        }},
        "word_count": "Estimated total word count as a number.",
        "chapter_structure": {{
            "prologue": "Brief summary of the prologue (if present).",
            "act_1_discovery": [
            "List of key plot beats or chapters in Act 1."
            ],
            "act_2_investigation": [
            "List of key plot beats or chapters in Act 2."
            ],
            "act_3_confrontation": [
            "List of key plot beats or chapters in Act 3."
            ],
            "epilogue": "Brief summary of the epilogue (if present).",
            "total_chapters": "Total number of chapters as a number."
        }},
        "unique_selling_proposition": "One or two sentences describing what makes this work unique and compelling."
        }}

        """
        print("Generating book specification...")
        if self.dry_run:
            # Dry run means get the json from file, instead of api
            fname = f"tests/book_concept_test_{TEST_CASE}.json"
            print(f"dry_run=true, getting concept from file: {fname}")
            with open(fname, "r") as f:
                response = f.read()
        else:
            # Get response from LLM
            response = self.send_api_payload(concept_prompt)

        # Remove markdown formatting before returning
        book_spec_dict = json.loads(
            response.replace("```json\n", "").replace("\n```", "")
        )

        # Store dictionary as accessible nested class attributes
        self.book_spec = self._dict_to_namespace(book_spec_dict)

        # Return book_spec
        return book_spec_dict


def with_spinner(msg: str = "Loading...") -> Callable:
    """
    Decorator to display a simple animated spinner in the terminal
    while the decorated function is running. The spinner runs in a
    separate thread and stops automatically when the function completes.

    Args:
        msg (str): Message to display alongside the spinner.

    Returns:
        Callable: Decorator that wraps the target function.
    """

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            stop_event = threading.Event()

            def spin():
                spinner_chars = "|/-\\"
                idx = 0
                while not stop_event.is_set():
                    # Print spinner character and return to start of
                    # line
                    print(
                        msg,
                        spinner_chars[idx % len(spinner_chars)],
                        end="\r",
                        flush=True,
                    )
                    idx += 1
                    time.sleep(0.1)
                # Clear spinner after stopping
                print(" " * (len(msg) + 2), end="\r")

            thread = threading.Thread(target=spin)
            thread.daemon = (
                True  # Daemon thread won't block program exit
            )
            thread.start()
            try:
                # Run the decorated function and capture its result
                result = func(*args, **kwargs)
                return result
            finally:
                # Signal the spinner to stop and wait for the thread to
                # finish
                stop_event.set()
                thread.join()
                print(f"{msg} Done.")

        return wrapper

    return decorator


if __name__ == "__main__":
    # prompt_1 = """
    # A lone radio operator on a decaying space station intercepts a
    # signal from Earth—centuries after humanity was believed extinct.
    # Is it a distress call, or something far more sinister?
    # """

    # bookGen = PerplexityBookGenerator(prompt_1, dry_run=True)
    # exit()
    # # Pretty-print the JSON output
    # print(json.dumps(bookGen.generate_book_spec(), indent=2))
    @with_spinner("Waiting for Perplexity API response to prompt...")
    def long_task(seconds):
        time.sleep(seconds)
        return "Task is complete!"

    result = long_task(3)
    print(result)
