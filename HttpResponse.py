from requests_html import HTMLSession
from html2text import HTML2Text
import re

HTML_SESSION = HTMLSession()
HTML_2_TEXT = HTML2Text()
HTML_2_TEXT.ignore_links = True


class FormattedResponse():
    def __init__(self, google_response, result_rank, full_text=False):
        self.result_rank = result_rank
        self.url = google_response['formattedUrl']
        if 'snippet' not in google_response:
            self.description = ''
        else:
            self.description = google_response['snippet'].replace(
                '\n', '').replace('\xa0', '')
        if 'title' not in google_response:
            self.title = ''
        else:
            self.title = google_response['title']

        self.body = ''
        if full_text:
            self.body = self.get_body_from_url()

    @property
    def joint_text(self):
        return self.title + ' ' + self.description + ' ' + self.body

    def get_body_from_url(self):
        response = HTML_SESSION.get(self.url)
        try:
            body = response.html.find('body', first=True)
        except:
            body = ''
        if not body:
            return ''
        return HTML_2_TEXT.handle(body.html)

    def __clean_string(self, string):
        '''
        Clean string from unwanted elements
        '''
        alphabet_pattern = re.compile(r'[^a-zA-Z\' ]+')
        cleaned_string = string.replace('-', ' ')
        cleaned_string = re.sub(alphabet_pattern, '', string).lower()
        return cleaned_string
