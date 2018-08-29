import requestsutils

class Confluence(requestsutils.RequestsBase):
  def __init__(self, baseurl, user, password):
    super().__init__()

    self.user = user
    self.password = password
    self.baseurl = baseurl

    self.session.auth = (self.user, self.password)

  def post_page(self, space_key, ancestor_id, title, content):
    data = {
      'type': 'page',
      'title': title,
      'space': {'key': space_key},
      'ancestors': [{'id': ancestor_id}], # only the first element is used
      'body': {'storage': {'value': content, 'representation': 'storage'}},
    }
    return self.api_request('content/', json = data)

  def api_request(self, path, *args, **kwargs):
    return self.request(path, *args, **kwargs).json()

