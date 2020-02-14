class FormattedResponse():
    def __init__(self, google_response, result_rank):
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
    
    @property
    def joint_text(self):
        return self.title + ' ' + self.description
