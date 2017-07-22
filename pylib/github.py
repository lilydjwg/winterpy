import datetime
import json
import weakref

import requestsutils

def parse_datetime(s):
  dt = datetime.datetime.strptime(s, '%Y-%m-%dT%H:%M:%SZ')
  return dt.replace(tzinfo=datetime.timezone.utc)

class GitHub(requestsutils.RequestsBase):
  baseurl = 'https://api.github.com/'

  def __init__(self, token, *, session=None):
    self.token = f'token {token}'
    super().__init__(session=session)

  def api_request(self, path, *args, method='get', data=None, **kwargs):
    h = kwargs.get('headers', None)
    if not h:
      h = kwargs['headers'] = {}
    h.setdefault('Accept', 'application/vnd.github.v3+json')
    h.setdefault('Authorization', self.token)

    if data:
      data = json.dumps(data, ensure_ascii=False).encode('utf-8')
      if method == 'get':
        method = 'post'
      h.setdefault('Content-Type', 'application/json')
      kwargs['data'] = data

    return self.request(path, method=method, *args, **kwargs)

  def get_repo_issues(self, repo, *, state='open', labels=''):
    params = {'state': state}
    if labels:
      params['labels'] = labels
    r = self.api_request(f'/repos/{repo}/issues', params = params)

    yield from (Issue(x, self) for x in r.json())
    while 'next' in r.links:
      r = self.api_request(r.links['next'])
      yield from (Issue(x, self) for x in r.json())

class Issue:
  def __init__(self, data, gh):
    self.gh = weakref.proxy(gh)
    self._data = data
    self.number = data['number']
    self.title = data['title']
    self.updated_at = parse_datetime(data['updated_at'])
    self._api_url = f"{data['repository_url']}/issues/{data['number']}"

  def comment(self, comment):
    return self.gh.api_request(f'{self._api_url}/comments', data = {'body': comment})

  def add_labels(self, labels):
    if not isinstance(labels, (list, tuple)):
      raise TypeError('labels should be a list')
    return self.gh.api_request(f'{self._api_url}/labels', data = labels)

  def close(self):
    return self.gh.api_request(f'{self._api_url}', method = 'patch',
                               data = {'state': 'closed'})

  def __repr__(self):
    return f'<Issue {self.number}: {self.title!r}>'
