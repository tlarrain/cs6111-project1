# CS6111 - Advance Database Systems Project 1
## Authors
Arjun Mangla (am4409) and Tomás Larrain (tal2150)
## Files

Name | Usage
--- | ---
project1.py | main program
HttpResponse.py | Google response class
mock_response.py | Mock Response for offline work
requirements.txt | Python packages to run the project

## Credentials
Credential | Detail
--- | ---
AIzaSyC7QIDsftl4f8lLTNwGsevas5hOOC96FZ8 | Google API KEY
015789145925826530430:flftxrkxktl | Search Engine ID

## Dependencies
To install, run:

  `$ pip install -r requirements.txt`

## How to Run
Under the program's root directory, run

`
$ python3 project1.py <google api key> <search engine id> <precision> "<query>"
`

## Internal Design

The program will first get arguments such as _API key_, _search engine ID_, _precision@10_, and _query terms_ from user input. The code is mainly divided in 3 main parts (with many methods each):
1. **Fetch Google Results**: This is mainly done by the ``get_google_results()`` method. After that, they are handled to the user through the terminal for the next step.
2. **Get relevance feedback**: The user must divide the results between relevant and not relevant through the terminal (summarized in ``get_relevance_feedback()``). With the relevance feedback, ``compute_precision_10()`` checks if the desired precision was achieved.
3. **Compute augmented query**: With the results of the relevance ready, the system procedes to compute the augmented query in ``get_augmented_query()``. This method returns the full augmented query, which replace the original one to start a new fetch and feedback loop.

## Query-modification Method

TO DO

## External references
[1] API design for machine learning software: experiences from the scikit-learn project, Buitinck et al., 2013.