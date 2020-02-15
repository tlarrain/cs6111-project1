import sys
import re
import math
import requests
import numpy as np
from collections import defaultdict
from googleapiclient.discovery import build
from sklearn.feature_extraction.text import TfidfVectorizer


def get_stop_words():
    return requests.get("http://www.cs.columbia.edu/~gravano/cs6111/proj1-stop.txt").text.split("\n")


'''
Fixed Values
'''
RELEVANT_KEYWORD = 'relevant'
NOT_RELEVANT_KEYWORD = 'not_relevant'
SEARCH_ENGINE_ID = ''
JSON_API_KEY = ''
MAX_ATTEMPTS = 5
STOP_WORDS = get_stop_words()

ALPHA = 1
BETA = 0.75
GAMMA = 0.15


def get_google_results(json_api_key, search_engine_id, query):
    '''
    Wrapper method for api call to json api to get google results for query
    Input: search engine id, json api key, query
    Output: list of formatted query results
    '''
    res_list = []
    service = build("customsearch", "v1", developerKey=json_api_key)
    res = service.cse().list(q=query, cx=search_engine_id).execute()
    for item in res['items']:
        shortened_item = dict()
        shortened_item['url'] = item['formattedUrl']
        if 'snippet' not in item:
            shortened_item['description'] = ''
        else:
            shortened_item['description'] = item['snippet'].replace(
                '\n', '').replace('\xa0', '')
        if 'title' not in item:
            shortened_item['title'] = ''
        else:
            shortened_item['title'] = item['title']
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
        print(f'URL: {result["url"]}')
        print(f'Title: {result["title"]}')
        print(f'Description: {result["description"]}')
        print(']')
        print()

        answer = input('Relevant (Y/N)?')
        print('----------------------')
        relevance = NOT_RELEVANT_KEYWORD
        if answer.title() == 'Y':
            relevance = RELEVANT_KEYWORD

        feedback_dictionary[relevance].append(result['title'])
        feedback_dictionary[relevance].append(result['description'])

    print('======================')
    return feedback_dictionary


# def compute_terms_set(custom_search_results):
#     '''
#     Convert all search results into one set of terms
#     '''
#     term_set = set()
#     for result in custom_search_results:
#         cleaned_result = clean_string(result['title']
#                                       + ' ' + result['description'])
#         term_set.update(set(cleaned_result.split()))
#     return term_set


def get_augmented_query(input_query, search_results, relevance_feedback_dict):
    '''
    Method for query logic expansion
    '''

    print('Indexing results ....')
    tf = TfidfVectorizer(analyzer='word', stop_words='english')
    q_m_vector = compute_rocchio_query_vector(input_query, search_results, relevance_feedback_dict, tf)
    new_query_terms = get_best_words(q_m_vector, tf)

    return input_query + ' ' + ' '.join(new_query_terms[1:3])


def compute_rocchio_query_vector(input_query, search_results, relevance_feedback_dict, tfidf_vectorizer):

    document_set = []
    for res in search_results:
        document_set.append(res['title'])
        document_set.append(res['description'])

    tfidf_matrix = tfidf_vectorizer.fit_transform(document_set)
    q_0_vector = tfidf_vectorizer.transform([input_query])

    relevant_doc_vectors = [tfidf_vectorizer.transform([relevant_doc]) for relevant_doc in relevance_feedback_dict[RELEVANT_KEYWORD]]
    not_relevant_doc_vectors = [tfidf_vectorizer.transform([not_relevant_doc]) for not_relevant_doc in relevance_feedback_dict[NOT_RELEVANT_KEYWORD]]

    relevant_doc_sum = sum(relevant_doc_vectors)
    not_relevant_doc_sum = sum(not_relevant_doc_vectors)

    # print('relevant_doc_sum', relevant_doc_sum)
    # print('not_relevant_doc_sum', not_relevant_doc_sum)

    len_relevant_doc = len(relevance_feedback_dict[RELEVANT_KEYWORD])
    len_not_relevant_doc = len(relevance_feedback_dict[NOT_RELEVANT_KEYWORD])

    q_m_vector = ALPHA * q_0_vector
    q_m_vector += BETA * (1 / len_relevant_doc) * relevant_doc_sum
    q_m_vector -= GAMMA * (1 / len_not_relevant_doc) * not_relevant_doc_sum

    # print('q_m_vector', q_m_vector)

    return  q_m_vector


def get_best_words(query_idf, tfidf_vectorizer):
    rows, cols = query_idf.nonzero()
    indices = []
    for i in range(len(rows)):
        indices.append((rows[i], cols[i]))
    tfidf_dict = {}
    for index in indices:
        tfidf_dict[index] = query_idf[index]

    inv = tfidf_vectorizer.inverse_transform(query_idf)
    term_list = []
    for tlist in inv:
        for term in tlist:
            term_list.append(term)

    word_scores = dict(zip(term_list, list(tfidf_dict.values())))
    best_words = sorted(word_scores, key=lambda k: word_scores[k], reverse=True)
    # print('word_scores', word_scores)
    # max_index_2 = sorted_indices[-2:-1][0]

    return best_words

# def sum_dicts(dict_list):
#     pass

# def get_relevance_doc_sums(relevant_docs, tf_idf_matrix, doc_set):
#     index_list = []
#     vector_sum = defaultdict(float)
#     for doc in relevant_docs:
#         index = doc_set.index(doc)
#         doc_tfidf_vector = tf_idf_matrix[index]



# def get_tfidf(term, document, doc_set):
#     tf = document.count(term) / len(document)
#     df = 0
#     for i in range(len(doc_set)):
#         if term in doc_set[i]:
#             df += 1
#     idf = np.log(len(doc_set) / df)
#     tf_idf = tf * idf
#
#     return tf_idf
#
#
# def convert_tfidf_matrix(doc_set):
#     tfidf_matrix = []
#     for doc in doc_set:
#         doc_dict = defaultdict(float)
#         set_of_terms = set(doc)
#         for word in set_of_terms:
#             tf_idf_score = get_tfidf(word, doc, doc_set)
#             doc_dict[word] = tf_idf_score
#         tfidf_matrix.append(doc_dict)
#     return tfidf_matrix


# def query_to_vector(query, doc_set):
#     whole_set = doc_set.append(query)
#     query_vector_dict = defaultdict(float)
#     for term in query:
#         tf_idf_score = get_tfidf(term, query, whole_set)
#         query_vector_dict[term] = tf_idf_score
#     return query_vector_dict

# def get_terms_odds_params(terms_set, relevance_feedback_dict):
#     terms_params = {}
#     for term in terms_set:
#         s = 0
#         df_t = 0
#         for relevant_doc in relevance_feedback_dict[RELEVANT_KEYWORD]:
#             clean_doc = clean_string(relevant_doc)
#             if term in clean_doc:
#                 s += 1
#                 df_t += 1
#         for not_relevant_doc in relevance_feedback_dict[NOT_RELEVANT_KEYWORD]:
#             clean_doc = clean_string(not_relevant_doc)
#             if term in clean_doc:
#                 df_t += 1
#         terms_params[term] = (s, df_t)
#     return terms_params
#
#
# def compute_ct_params(terms_params, S, N):
#     '''
#     Get c_t params for each term
#     '''
#     ct_params = {}
#     for term in terms_params:
#         s, df_t = terms_params[term]
#         ct_params[term] = math.log(
#             ((s + 0.5) / (S - s + 0.5))
#             / ((df_t - s + 0.5) / (N - df_t - S + s + 0.5)))
#
#     return sorted(ct_params.items(), key=lambda x: x[1], reverse=True)


# def clean_string(string):
#     '''
#     Clean string from unwanted elements
#     '''
#     alphabet_pattern = re.compile(r'[^a-zA-Z ]+')
#     cleaned_string = string.replace('-', ' ')
#     cleaned_string = re.sub(alphabet_pattern, '', string).lower()
#     return cleaned_string



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
        print_received_input(JSON_API_KEY,
                             SEARCH_ENGINE_ID,
                             raw_query,
                             desired_precision)

        custom_search_results = get_google_results(JSON_API_KEY,
                                                   SEARCH_ENGINE_ID,
                                                   raw_query)

        relevance_feedback = get_relevance_feedback(custom_search_results)
        result_precision = compute_precision_10(relevance_feedback)

        print_feedback_summary(raw_query,
                               result_precision,
                               desired_precision)
        augmented_query = get_augmented_query(raw_query,
                                              custom_search_results,
                                              relevance_feedback)

        raw_query = augmented_query

    print('Below desired precision, '
          + 'but max number of attempts has been reached.')


if __name__ == '__main__':
    main()
