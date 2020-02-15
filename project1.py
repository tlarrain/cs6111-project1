import sys
import re
import math
import requests
from googleapiclient.discovery import build
from mock_response import MOCK_RESPONSE
from HttpResponse import FormattedResponse


def get_stop_words():
    return requests.get(
        "http://www.cs.columbia.edu/"
        + "~gravano/cs6111/proj1-stop.txt").text.split("\n")


'''
Fixed Values
'''
RELEVANT_KEYWORD = 'relevant'
NOT_RELEVANT_KEYWORD = 'not_relevant'
SEARCH_ENGINE_ID = ''
JSON_API_KEY = ''
MAX_ATTEMPTS = 5
STOP_WORDS = get_stop_words()


def get_google_results(json_api_key,
                       search_engine_id, query, mock_response=True):
    '''
    Wrapper method for api call to json api to get google results for query
    Input: search engine id, json api key, query
    Output: list of formatted query results
    '''
    res_list = []
    if mock_response:
        res = {'items': MOCK_RESPONSE}
    else:
        service = build("customsearch", "v1", developerKey=json_api_key)
        res = service.cse().list(q=query, cx=search_engine_id).execute()
    for i, item in enumerate(res['items']):
        shortened_item = FormattedResponse(item, i)
        res_list.append(shortened_item)
    return res_list


def compute_total_query_count(feedback_dict):
    '''
    Getting total query results count
    '''
    return (len(feedback_dict[RELEVANT_KEYWORD])
            + len(feedback_dict[NOT_RELEVANT_KEYWORD]))


def compute_precision_10(feedback_dict):
    '''
    Computing precision@10
    '''
    count_yes = len(feedback_dict[RELEVANT_KEYWORD])
    return count_yes/compute_total_query_count(feedback_dict)


def print_received_input(json_api_key, search_engine_id,
                         input_query, des_precision):
    '''
    Showing users their input
    '''
    print('Parameters:')
    print(f'Client key  = {json_api_key}')
    print(f'Engine key  = {search_engine_id}')
    print(f'Query  = {input_query}')
    print(f'Precision  = {des_precision}')


def print_feedback_summary(input_query, res_precision, des_precision):
    '''
    Result summary for users.
    '''
    print('FEEDBACK SUMMARY')
    print(f'Query {input_query}')
    print(f'Precision {res_precision}')
    if res_precision == 0:
        print('Below desired precision, but can no longer augment the query')
        sys.exit()
    elif res_precision < des_precision:
        print(f'Still below the desired precision of {des_precision}')
    else:
        print('Desired precision reached, done')
        sys.exit()


def get_relevance_feedback(results):
    '''
    Display search results and get relevance feedback from users.
    '''
    feedback_dictionary = {
        RELEVANT_KEYWORD: [],
        NOT_RELEVANT_KEYWORD: [],
    }
    print('Google Search Results:')
    print('======================')

    for i, result in enumerate(results):
        print(f'Result {i+1}')
        print('[')
        print(f'URL: {result.url}')
        print(f'Title: {result.title}')
        print(f'Description: {result.description}')
        print(']')
        print()

        answer = input('Relevant (Y/N)?')
        print('----------------------')
        relevance = NOT_RELEVANT_KEYWORD
        if answer.title() == 'Y':
            relevance = RELEVANT_KEYWORD

        feedback_dictionary[relevance].append(result)

    print('======================')
    return feedback_dictionary


def compute_terms_set(custom_search_results):
    '''
    Convert all search results into one set of terms
    '''
    term_set = set()
    for result in custom_search_results:
        cleaned_result = clean_string(result.joint_text)
        term_set.update(set(cleaned_result.split()))
    return term_set


def get_augmented_query(input_query, search_results, relevance_feedback_dict):
    '''
    Method for query logic expansion
    '''
    print('Indexing results ....')
    S = 2*len(relevance_feedback_dict[RELEVANT_KEYWORD])
    N = 2*compute_total_query_count(relevance_feedback_dict)
    terms_set = compute_terms_set(search_results)
    terms_params = get_terms_odds_params(terms_set, relevance_feedback_dict)
    ct_params = compute_ct_params(terms_params, S, N)
    words_added = 0
    added_string = ''
    for ct in ct_params:
        if words_added == 2:
            break
        if ct[0] in STOP_WORDS or ct[0] in input_query:
            continue
        added_string += ct[0] + ' '
        words_added += 1

    print(f'Augmenting by {added_string}')
    aug_query = input_query + ' ' + added_string

    return aug_query


def get_terms_odds_params(terms_set, relevance_feedback_dict):
    terms_params = {}
    for term in terms_set:
        s = 0
        df_t = 0
        doc_rank = 0
        for relevant_doc in relevance_feedback_dict[RELEVANT_KEYWORD]:
            clean_doc = clean_string(relevant_doc.title)
            if term in clean_doc:
                s += 1
                df_t += 1
                doc_rank = max(1, relevant_doc.result_rank)
        for relevant_doc in relevance_feedback_dict[RELEVANT_KEYWORD]:
            clean_doc = clean_string(relevant_doc.description)
            if term in clean_doc:
                s += 1
                df_t += 1
                doc_rank = max(1, relevant_doc.result_rank)
        for not_relevant_doc in relevance_feedback_dict[NOT_RELEVANT_KEYWORD]:
            clean_doc = clean_string(not_relevant_doc.title)
            if term in clean_doc:
                df_t += 1
        for not_relevant_doc in relevance_feedback_dict[NOT_RELEVANT_KEYWORD]:
            clean_doc = clean_string(not_relevant_doc.description)
            if term in clean_doc:
                df_t += 1
        terms_params[term] = (s, df_t, doc_rank)
    return terms_params


def compute_ct_params(terms_params, S, N):
    '''
    Get c_t params for each term
    '''
    ct_params = {}
    for term in terms_params:
        s, df_t, rank = terms_params[term]
        ct_params[term] = (math.log(
            ((s + 0.5) / (S - s + 0.5))
            / ((df_t - s + 0.5) / (N - df_t - S + s + 0.5))), rank)

    ct_list = list(ct_params.items())
    ct_list.sort(key=lambda x:x[1][1])
    ct_list.sort(key=lambda x:x[1][0], reverse=True)
    return ct_list


def clean_string(string):
    '''
    Clean string from unwanted elements
    '''
    alphabet_pattern = re.compile(r'[^a-zA-Z ]+')
    cleaned_string = string.replace('-', ' ')
    cleaned_string = re.sub(alphabet_pattern, '', string).lower()
    return cleaned_string


def main():
    '''
    Main method
    '''
    if not (len(sys.argv) == 5 and sys.argv[3].replace('.', '', 1).isdigit()):
        sys.exit("Format: basic.py <Google API Key> "
                 + "<Google Search Engine ID> <Precision> <Query>")

    JSON_API_KEY, SEARCH_ENGINE_ID = sys.argv[1], sys.argv[2]
    desired_precision, raw_query = float(sys.argv[3]), sys.argv[4]

    for i in range(MAX_ATTEMPTS):
        print_received_input(
            JSON_API_KEY, SEARCH_ENGINE_ID, raw_query, desired_precision)

        custom_search_results = get_google_results(
            JSON_API_KEY, SEARCH_ENGINE_ID, raw_query)

        relevance_feedback = get_relevance_feedback(custom_search_results)
        result_precision = compute_precision_10(relevance_feedback)

        print_feedback_summary(
            raw_query, result_precision, desired_precision)
        augmented_query = get_augmented_query(
            raw_query, custom_search_results, relevance_feedback)

        raw_query = augmented_query

    print('Below desired precision, '
          + 'but max number of attempts has been reached.')


if __name__ == '__main__':
    main()
