import sys
from googleapiclient.discovery import build
from sklearn.feature_extraction.text import TfidfVectorizer
from HttpResponse import FormattedResponse


'''
Fixed Values
'''
RELEVANT_KEYWORD = 'relevant'
NOT_RELEVANT_KEYWORD = 'not_relevant'
SEARCH_ENGINE_ID = ''
JSON_API_KEY = ''
MAX_ATTEMPTS = 10
USE_FULL_TEXT = False
USE_MOCK = False

ALPHA = 1
BETA = 0.75
GAMMA = 0.15


def get_google_results(json_api_key,
                       search_engine_id, query, mock_response=USE_MOCK):
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
        shortened_item = FormattedResponse(item, i, full_text=USE_FULL_TEXT)
        res_list.append(shortened_item)
    return res_list


def compute_total_query_count(feedback_dict):
    '''
    Getting total query results count
    Input: Dictionary containing user feedback for results
    Output: Integer representing total number of results
    '''
    return (len(feedback_dict[RELEVANT_KEYWORD])
            + len(feedback_dict[NOT_RELEVANT_KEYWORD]))


def compute_precision_10(feedback_dict):
    '''
    Computing precision@10
    Input: Dictionary containing user feedback for results
    Output: Float representing precision@10 score
    '''
    count_yes = len(feedback_dict[RELEVANT_KEYWORD])
    return count_yes/compute_total_query_count(feedback_dict)


def print_received_input(json_api_key, search_engine_id,
                         input_query, des_precision):
    '''
    Showing users their input
    Input: API key, search engine id, query, desired Precision@10 score
    Output: nothing returned, only print output
    '''
    print('Parameters:')
    print(f'Client key  = {json_api_key}')
    print(f'Engine key  = {search_engine_id}')
    print(f'Query  = {input_query}')
    print(f'Precision  = {des_precision}')


def print_feedback_summary(input_query, res_precision, des_precision):
    '''
    Result summary for users,
    Terminates program if precision is 0, or if desired precision reached.
    Input: query, achieved Precision@10 score, desired Precision@10 score
    Output: nothing returned, only print output
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
    Input: list of dictionaries of each of the results, user input for each of the displayed results
    Output: Dictionary containing 2 lists:
            1st list: containing 1 string each for all documents declared relevant by user
            2nd list: containing 1 string each for all documents declared irrelevant by user
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
        relevance = NOT_RELEVANT_KEYWORD # defaulting to not relevant
        if answer.title() == 'Y': #interpreting both upper case and lowercase responses
            relevance = RELEVANT_KEYWORD #changing to relevant only if indicated by user

        feedback_dictionary[relevance].append(result.joint_text)

    print('======================')
    return feedback_dictionary


def get_augmented_query(input_query, search_results, relevance_feedback_dict):
    '''
    Method for query logic expansion
    Input: Query, formatted search results (list of dictionaries), Dictionary with relevance feedback
    Output: New, augmented query
    '''

    print('Indexing results ....')

    # Create TfidfVectorizer instance here to pass through 2 functions:
    #   rocchio method and highest relevance word retriever
    tf = TfidfVectorizer(analyzer='word', stop_words='english')

    # Compute tf-idf vector for new query
    q_m_vector = compute_rocchio_query_vector(input_query, search_results,
                                              relevance_feedback_dict, tf)

    #From new query vector, get words sorted: highest to lowest tf-idf scores
    new_query_terms = get_best_words(q_m_vector, tf)

    #Append words to query
    augmented_words = []
    for term in new_query_terms:
        #Stop if 2 words selected
        if len(augmented_words) == 2:
            break
        #If the term is already in the query, ignore
        if term in input_query:
            continue
        augmented_words.append(term)

    return input_query + ' ' + ' '.join(augmented_words)


def compute_rocchio_query_vector(input_query, search_results,
                                 relevance_feedback_dict, tfidf_vectorizer):
    '''
        Implements Rocchio to compute new query vector based on relevance feedback
        Uses tf-idf vector to vectorize documents and queries
        Input: Query, formatted search results (list of dictionaries),
                Dictionary with relevance feedback, vectorizer object
        Output: Resultant query vector
    '''

    # Creates list of documents to create tf-idf matrix
    document_set = []
    for res in search_results:
        document_set.append(res.joint_text)

    # Uses list of documents to create matrix
    tfidf_matrix = tfidf_vectorizer.fit_transform(document_set)

    #Uses matrix to convert input query into tf-idf vector
    q_0_vector = tfidf_vectorizer.transform([input_query])

    #Uses matrix to convert relevant, not-relevant documents into individual tf-idf vectors
    relevant_doc_vectors, not_relevant_doc_vectors = get_doc_vectors(
        relevance_feedback_dict, tfidf_vectorizer)

    relevant_doc_sum = sum(relevant_doc_vectors)
    not_relevant_doc_sum = sum(not_relevant_doc_vectors)

    len_relevant_doc = len(relevance_feedback_dict[RELEVANT_KEYWORD])
    len_not_relevant_doc = len(relevance_feedback_dict[NOT_RELEVANT_KEYWORD])

    #Creating new query vector based on Rocchio's formula
    q_m_vector = ALPHA * q_0_vector
    q_m_vector += BETA * (1 / len_relevant_doc) * relevant_doc_sum
    q_m_vector -= GAMMA * (1 / len_not_relevant_doc) * not_relevant_doc_sum

    return q_m_vector


def get_doc_vectors(relevance_feedback_dict, tfidf_vectorizer):
    '''
        Uses matrix to convert relevant, not-relevant documents into individual tf-idf vectors
        Input: Dictionary with relevance feedback, vectorizer instance
        Output: 2 lists of if-idf vectors for relevant and not relevant documents respectively
    '''


    relevant_doc_vectors = generate_doc_vectors(
        relevance_feedback_dict[RELEVANT_KEYWORD], tfidf_vectorizer)
    not_relevant_doc_vectors = generate_doc_vectors(
        relevance_feedback_dict[NOT_RELEVANT_KEYWORD], tfidf_vectorizer)
    return relevant_doc_vectors, not_relevant_doc_vectors


def generate_doc_vectors(doc_list, tfidf_vectorizer):
    # return list of tf-idf vectors from list of strings
    return [tfidf_vectorizer.transform([doc]) for doc in doc_list]


def get_best_words(query_idf, tfidf_vectorizer):
    '''
        Uses matrix to convert tf-idf vector of query into list of words
        Input: tf-idf query vector, vectorizer instance
        Output: list of words, reverse sorted based on scores
    '''

    # Creating dictionary (index in matrix): score
    rows, cols = query_idf.nonzero()
    indices = []
    for i in range(len(rows)):
        indices.append((rows[i], cols[i]))
    tfidf_dict = {}
    for index in indices:
        tfidf_dict[index] = query_idf[index]

    # Using inverse transform, get every word
    inv = tfidf_vectorizer.inverse_transform(query_idf)
    term_list = []
    for tlist in inv:
        for term in tlist:
            term_list.append(term)

    # Combine scores and words, and sort words based on scores
    word_scores = dict(zip(term_list, list(tfidf_dict.values())))
    best_words = sorted(
        word_scores, key=lambda k: word_scores[k], reverse=True)

    return best_words


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
