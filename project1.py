import sys
from googleapiclient.discovery import build


'''
Fixed Values
'''
SEARCH_ENGINE_ID = ''
JSON_API_KEY = ''
MAX_ATTEMPTS = 5


'''
Wrapper method for api call to json api to get google results for query
Input: search engine id, json api key, query
Output: list of formatted query results
'''
def get_google_results(json_api_key, search_engine_id, query):
    res_list = []
    service = build("customsearch", "v1", developerKey=json_api_key)
    res = service.cse().list(q=query, cx=search_engine_id).execute()
    for item in res['items']:
        shortened_item = dict()
        shortened_item['url'] = item['formattedUrl']
        shortened_item['title'] = item['title']
        shortened_item['description'] = item['snippet'].replace('\n','')
        res_list.append(shortened_item)
    return res_list


'''
Computing precision@10
'''
def compute_precision_10(feedback_dict):
    values = list(feedback_dict.values())
    count_yes = values.count('Y') + values.count('y')
    count_total = len(feedback_dict)
    return count_yes/count_total


'''
Showing users their input
'''
def print_received_input(json_api_key, search_engine_id, input_query, des_precision):
    print('Parameters:')
    print(f'Client key  = {json_api_key}')
    print(f'Engine key  = {search_engine_id}')
    print(f'Query  = {input_query}')
    print(f'Precision  = {des_precision}')


'''
Result summary for users.
'''
def print_feedback_summary(input_query, res_precision, des_precision):
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


'''
Display search results and get relevance feedback from users.
'''
def get_relevance_feedback(results):
    feedback_dictionary = {}
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
        feedback_dictionary[result['url']] = answer

    print('======================')
    return feedback_dictionary


'''
TO DO: METHOD FOR QUERY EXPANSION LOGIC
'''
def get_augmented_query(input_query, search_results, relevance_feedback_dict):
    print('Indexing results ....')
    print('Indexing results ....')

    added_string = ''
    print(f'Augmenting by {added_string}')
    aug_query = input_query + added_string

    return aug_query


'''
MAIN METHOD
'''
def main():
    if not (len(sys.argv) == 5 and sys.argv[3].replace('.', '', 1).isdigit()):
        sys.exit("Format: basic.py <Google API Key> <Google Search Engine ID> <Precision> <Query>")

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


if __name__ == '__main__':
    main()