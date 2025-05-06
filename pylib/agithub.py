from __future__ import annotations

import datetime
import json
import weakref
import asyncio
import logging
import time
from typing import (
  AsyncGenerator, Tuple, Any, Dict, Optional, List, Union, cast,
)
import enum

from aiohttp.client import ClientResponse
import aiohttputils

logger = logging.getLogger(__name__)

JsonDict = Dict[str, Any]
Json = Union[List[JsonDict], JsonDict]

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

  async def api_request(
    self, path: str, method: str = 'get',
    data: Optional[JsonDict] = None, **kwargs,
  ) -> Tuple[Json, ClientResponse]:
    h = kwargs.get('headers', None)
    if not h:
      h = kwargs['headers'] = {}
    h.setdefault('Accept', 'application/vnd.github.v3+json')
    h.setdefault('Authorization', self.token)

    if data:
      binary_data = json.dumps(data, ensure_ascii=False).encode('utf-8')
      if method == 'get':
        method = 'post'
      h.setdefault('Content-Type', 'application/json')
      kwargs['data'] = binary_data

    for _ in range(3):
      res = await self.request(path, method=method, **kwargs)
      j: JsonDict
      if res.status == 204:
        j = {}
      else:
        j = await res.json()
        if 'message' in j:
          if res.status == 403 and int(res.headers.get('X-RateLimit-Remaining', -1)) == 0:
            reset = int(res.headers['X-RateLimit-Reset']) - time.time() + 1
            logger.warn('rate limited; sleeping for %ds: %s', reset, j['message'])
            await asyncio.sleep(reset)
            continue
          raise GitHubError(j['message'], j['documentation_url'], res.status)
      return j, res

    raise Exception('unreachable')

  async def get_repo_issues(
    self, repo: str, *, state: str = 'open', labels: str = '',
  ) -> AsyncGenerator[Issue, None]:
    params = {'state': state}
    if labels:
      params['labels'] = labels
    j, r = await self.api_request(f'/repos/{repo}/issues', params = params)
    assert isinstance(j, list)

    for x in j:
      yield Issue(x, self)

    while 'next' in r.links:
      url = str(r.links['next']['url'])
      j, r = await self.api_request(url)
      assert isinstance(j, list)
      for x in j:
        yield Issue(x, self)

  async def get_issue(self, repo: str, issue_nr: int) -> 'Issue':
    j, _ = await self.api_request(f'/repos/{repo}/issues/{issue_nr}')
    assert isinstance(j, dict)
    return Issue(j, self)

  async def get_issue_comments(
    self, repo: str, issue_nr: int,
  ) -> AsyncGenerator[Comment, None]:
    j, r = await self.api_request(f'/repos/{repo}/issues/{issue_nr}/comments')

    assert isinstance(j, list)
    for x in j:
      yield Comment(x, self)

    while 'next' in r.links:
      url = str(r.links['next']['url'])
      j, r = await self.api_request(url)
      assert isinstance(j, list)
      for x in j:
        yield Comment(x, self)

  async def create_issue(
    self, repo: str, title: str, body: Optional[str] = None,
    labels: List[str] = [],
  ) -> 'Issue':
    data: JsonDict = {
      'title': title,
    }
    if body:
      data['body'] = body
    if labels:
      data['labels'] = labels

    issue, _ = await self.api_request(f'/repos/{repo}/issues', data = data)
    assert isinstance(issue, dict)
    return Issue(issue, self)

  async def find_login_by_email(self, email: str) -> str:
    j, _ = await self.api_request(f'/search/users?q={email}')
    assert isinstance(j, dict)
    try:
      return j['items'][0]['login']
    except IndexError:
      raise LookupError(email)

IssueStateReason = enum.StrEnum(
  'IssueStateReason',
  ['completed', 'not_planned', 'reopened']
)

class Issue:
  def __init__(self, data: JsonDict, gh: GitHub) -> None:
    self.gh = weakref.proxy(gh)
    self._data = data
    self.body = data['body']
    self.number = data['number']
    self.title = data['title']
    self.labels = [x['name'] for x in data['labels']]
    self.updated_at = parse_datetime(data['updated_at'])
    # pr or issue
    self._api_url = data.get('issue_url', data['url'])
    self.closed = data['state'] == 'closed'
    self.author = data['user']['login']
    self.closed_by = data.get('closed_by') and data['closed_by']['login'] or None

  async def comment(self, comment: str) -> JsonDict:
    j, _ = await self.gh.api_request(f'{self._api_url}/comments', data = {'body': comment})
    return j

  async def add_labels(self, labels: List[str]) -> JsonDict:
    j, _ = await self.gh.api_request(f'{self._api_url}/labels', data = labels)
    return j

  async def assign(self, assignees: List[str | GitHubLogin]) -> JsonDict:
    if isinstance(assignees[0], GitHubLogin):
      payload = {'assignees': [x.login for x in cast(list[GitHubLogin], assignees)]}
    else:
      payload = {'assignees': cast(list[str], assignees)}
    j, _ = await self.gh.api_request(f'{self._api_url}/assignees', data = payload)
    return j

  async def close(self, reason: Optional[IssueStateReason] = None) -> None:
    data = {'state': 'closed'}
    if reason is not None:
      data['state_reason'] = str(reason)

    data, _ = await self.gh.api_request(
      f'{self._api_url}', method = 'patch', data = data)
    self._data = data
    self.closed = data['state'] == 'closed'

  async def reopen(self) -> None:
    data, _ = await self.gh.api_request(
      f'{self._api_url}', method = 'patch', data = {'state': 'open'})
    self._data = data
    self.closed = data['state'] == 'closed'

  def __repr__(self):
    return f'<Issue {self.number}: {self.title!r}>'

class Comment:
  def __init__(self, data: JsonDict, gh: GitHub) -> None:
    self.gh = weakref.proxy(gh)
    self._update(data)

  def _update(self, data: JsonDict) -> None:
    self._data = data
    self.author = data['user']['login']
    self.html_url = data['html_url']
    self.url = data['url']
    self.body = data['body']

  async def delete(self) -> None:
    await self.gh.api_request(self.url, method = 'DELETE')

  async def edit(self, body: str) -> None:
    data, _ = await self.gh.api_request(
      self.url, method = 'PATCH',
      data = {'body': body},
    )
    self._update(data)

  def __repr__(self) -> str:
    return f'<Comment by {self.author}: {self.html_url}>'

class GitHubLogin:
  login: str
  lower: str

  def __init__(self, login: str) -> None:
    self.login = login
    self.lower = login.lower()

  def __str__(self) -> str:
    return self.login

  def __repr__(self) -> str:
    return f'<GitHub login: {self.login}>'

  def __eq__(self, other: Any) -> bool:
    if isinstance(other, GitHubLogin):
      return self.lower == other.lower
    else:
      return self.lower == other.lower()

  def __hash__(self):
    return hash(self.lower)

  def __lt__(self, other: GitHubLogin) -> bool:
    return self.lower < other.lower

class PullRequest(Issue):
  async def compare(self) -> JsonDict:
    repo_url = self._data['base']['repo']['url']
    base = self._data['base']['sha']
    head = self._data['head']['sha']
    compare_url = f'{repo_url}/compare/{base}...{head}'
    j, _ = await self.gh.api_request(compare_url)
    return j
