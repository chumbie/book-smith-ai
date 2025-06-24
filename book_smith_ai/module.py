# Core libraries for API interaction and content processing
import os  # to get API key from environment
import requests  # to send API requests
import json  # conversion to/from JSON data object
import time
import types  # Import SimpleNamespace for dynamic type creation

from pathlib import Path

# EPUB creation libraries
#from ebooklib import epub
#import pypub

# Additional utilities
import re
import uuid
from datetime import datetime

# CONSTANTS
TEST_CASE = 1


class PerplexityBookGenerator:
    ## STEP 1: API Authorization and Setup
    def __init__(self, api_key, book_idea, dry_run = False):
        # Set this in Linux w/ $export PERPLEXITY_API_KEY=<your api key>         
        self.api_key = os.getenv("PERPLEXITY_API_KEY")
        if not api_key:
            raise ValueError(
                "Please set the PERPLEXITY_API_KEY environment variable."
                )
        self.base_url = "https://api.perplexity.ai/chat/completions"
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        self.book_idea = book_idea
        # Will use stored tests/ data instead of calling LLM
        self.dry_run = dry_run

    @staticmethod  # Declares this method as static (no self/cls parameter needed)
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



    def send_api_payload(self, 
        prompt: str, role: str = "You are a helpful assistant.", 
        model: str = "r1-1776", temp: float = 0.7,
        debug: bool = False) -> str:
            """Method to submit prompts to LLM"""

            self.payload = {
            "model": model,  # Use "sonar-pro" or another Pro model
            "messages": [
                {"role": "system", "content": role + "Do not include any citations in your response. "},
                {"role": "user", "content": prompt}
            ],
            "temperature": temp
            }
            response = requests.post(self.base_url, headers=self.headers, json=self.payload)
            response.raise_for_status()  # Raises an error for bad status codes

            result = response.json()
            if debug:
                # Print full JSON responses
                print(f"Prompt: {prompt}", "Result:", json.dumps(result, indent=2), sep="\n",)
                # Do not remove <think> section via post-processing
                return result["choices"][0]["message"]["content"]
            else:
                return re.sub(
                    # Removes <think> section from response
                    r'<think>.*?</think>\s*'
                    , ''
                    , result["choices"][0]["message"]["content"]
                    , flags=re.DOTALL
                    )


    ## Step 2: Go from book idea to comprehensive concept specification 
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
        book_spec_dict = json.loads(response.replace("```json\n","").replace("\n```", ""))
        
        # Store dictionary as accessible nested class attributes
        self.book_spec = self._dict_to_namespace(book_spec_dict)
        
        # Return book_spec
        return book_spec_dict


if __name__ == "__main__":
    from pprint import pprint
    my_api_key = os.getenv("PERPLEXITY_API_KEY")
    prompt_1 = """
    A lone radio operator on a decaying space station intercepts a 
    signal from Earth—centuries after humanity was believed extinct. 
    Is it a distress call, or something far more sinister?
    """
    # print(PerplexityBookGenerator(my_api_key).send_api_payload(prompt, debug=True))
    # print(PerplexityBookGenerator(my_api_key, prompt, dry_run=True).generate_book_spec())
    # with open("tests/book_concept_test_1.json", "w", encoding="utf-8") as file:
    #     file.write(
    #         PerplexityBookGenerator(
    #             my_api_key, prompt
    #             ).generate_book_spec())

    bookGen = PerplexityBookGenerator(my_api_key, prompt_1, dry_run=True)
    bookGen.generate_book_spec()
    # pprint(vars(bookGen))
    print("TITLE:", bookGen.book_spec.expanded_title, sep="\n")
    print("SUBTITLE:", bookGen.book_spec.subtitle, sep="\n")
    print("CORE_THEMES:", bookGen.book_spec.target_audience.primary, sep="\n")
    print("CORE_THEMES:", bookGen.book_spec.target_audience.secondary, sep="\n")
    print("CORE_THEMES:", bookGen.book_spec.target_audience.key_interests, sep="\n")
    # print("CORE_THEMES (type):", type(bookGen.core_themes), sep="\n")
    # print("GENRE:", bookGen.genre, sep="\n")
    # print("SUBGENRES:", bookGen.subgenres, sep="\n")
    # print("TONE:", bookGen.tone, sep="\n")
    # print("TONE:", bookGen.prologue, sep="\n")

    # print(book.title)
    # print(book.title)