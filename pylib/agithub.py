import datetime
import json
import weakref

import aiohttputils

def parse_datetime(s):
  dt = datetime.datetime.strptime(s, '%Y-%m-%dT%H:%M:%SZ')
  return dt.replace(tzinfo=datetime.timezone.utc)

class GitHubError(Exception):
  def __init__(self, message, documentation, code):
    self.message = message
    self.documentation = documentation
    self.code = code

class GitHub(aiohttputils.ClientBase):
  baseurl = 'https://api.github.com/'

  def __init__(self, token, session=None):
    self.token = f'token {token}'
    super().__init__(session = session)

  async def api_request(self, path, *args, method='get', data=None, **kwargs):
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

    res = await self.request(path, method=method, *args, **kwargs)
    j = await res.json()
    if 'message' in j:
      raise GitHubError(j['message'], j['documentation_url'], res.status)
    return j

  async def get_repo_issues(self, repo, *, state='open', labels=''):
    params = {'state': state}
    if labels:
      params['labels'] = labels
    r = await self.api_request(f'/repos/{repo}/issues', params = params)

    for x in r:
      yield Issue(x, self)

    while 'next' in r.links:
      r = await self.api_request(r.links['next'])
      for x in r:
        yield Issue(x, self)

  async def create_issue(self, repo, title, body=None, labels=()):
    data = {
      'title': title,
    }
    if body:
      data['body'] = body
    if labels:
      data['labels'] = labels

    issue = await self.api_request(f'/repos/{repo}/issues', data = data)
    return Issue(issue, self)

class Issue:
  def __init__(self, data, gh):
    self.gh = weakref.proxy(gh)
    self._data = data
    self.number = data['number']
    self.title = data['title']
    self.labels = [x['name'] for x in data['labels']]
    self.updated_at = parse_datetime(data['updated_at'])
    self._api_url = f"{data['repository_url']}/issues/{data['number']}"

  async def comment(self, comment):
    return await self.gh.api_request(f'{self._api_url}/comments', data = {'body': comment})

  async def add_labels(self, labels):
    if not isinstance(labels, (list, tuple)):
      raise TypeError('labels should be a list')
    return await self.gh.api_request(f'{self._api_url}/labels', data = labels)

  async def close(self):
    return await self.gh.api_request(f'{self._api_url}', method = 'patch',
                               data = {'state': 'closed'})

  def __repr__(self):
    return f'<Issue {self.number}: {self.title!r}>'
