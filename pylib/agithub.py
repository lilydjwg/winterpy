import datetime
import json
import weakref
import asyncio
import logging
from typing import AsyncGenerator

import aiohttputils

logger = logging.getLogger(__name__)

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

    for _ in range(3):
      res = await self.request(path, method=method, *args, **kwargs)
      j = await res.json()
      if 'message' in j:
        if res.status == 403 and int(res.headers.get('X-RateLimit-Remaining')) == 0:
          reset = int(res.headers.get('X-RateLimit-Reset')) - asyncio.time() + 1
          logger.warn('rate limited; sleeping for %ds: %s', reset, j['message'])
          await asyncio.sleep(reset)
          continue
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

  async def get_issue(self, repo: str, issue_nr: int) -> 'Issue':
    r = await self.api_request(f'/repos/{repo}/issues/{issue_nr}')
    return Issue(r, self)

  async def get_issue_comments(
    self, repo: str, issue_nr: int,
  ) -> AsyncGenerator['Comment', None]:
    r = await self.api_request(f'/repos/{repo}/issues/{issue_nr}/comments')

    for x in r:
      yield Comment(x, self)

    while 'next' in r.links:
      r = await self.api_request(r.links['next'])
      for x in r:
        yield Comment(x, self)

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

  async def find_login_by_email(self, email):
    j = await self.api_request(f'/search/users?q={email}')
    try:
      return j['items'][0]['login']
    except IndexError:
      raise LookupError(email)

class Issue:
  def __init__(self, data, gh):
    self.gh = weakref.proxy(gh)
    self._data = data
    self.body = data['body']
    self.number = data['number']
    self.title = data['title']
    self.labels = [x['name'] for x in data['labels']]
    self.updated_at = parse_datetime(data['updated_at'])
    self._api_url = f"{data['repository_url']}/issues/{data['number']}"
    self.closed = data['state'] == 'closed'

  async def comment(self, comment):
    return await self.gh.api_request(f'{self._api_url}/comments', data = {'body': comment})

  async def add_labels(self, labels):
    if not isinstance(labels, (list, tuple)):
      raise TypeError('labels should be a list')
    return await self.gh.api_request(f'{self._api_url}/labels', data = labels)

  async def assign(self, assignees):
    if not isinstance(assignees, (list, tuple)):
      raise TypeError('assignees should be a list')
    payload = {'assignees': assignees}
    return await self.gh.api_request(f'{self._api_url}/assignees', data = payload)

  async def close(self) -> None:
    self._data = data = await self.gh.api_request(
      f'{self._api_url}', method = 'patch', data = {'state': 'closed'})
    self.closed = data['state'] == 'closed'

  async def reopen(self) -> None:
    self._data = data = await self.gh.api_request(
      f'{self._api_url}', method = 'patch', data = {'state': 'closed'})
    self.closed = data['state'] == 'closed'

  def __repr__(self):
    return f'<Issue {self.number}: {self.title!r}>'

class Comment:
  def __init__(self, data, gh: GitHub):
    self.gh = weakref.proxy(gh)
    self._data = data
    self.author = data['user']['login']
    self.html_url = data['html_url']
    self.url = data['url']

  async def delete(self) -> None:
    await self.gh.api_request(self.url, method = 'DELETE')

  def __repr__(self):
    return f'<Comment by {self.author}: {self.html_url}>'
