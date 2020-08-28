from __future__ import annotations

import datetime
import weakref
from typing import Any, Iterator, Dict

import requestsutils
from requests import Response

JsonDict = Dict[str, Any]

def parse_datetime(s: str) -> datetime.datetime:
  dt = datetime.datetime.strptime(s, '%Y-%m-%dT%H:%M:%SZ')
  return dt.replace(tzinfo=datetime.timezone.utc)

class GitHub(requestsutils.RequestsBase):
  baseurl = 'https://api.github.com/'

  def __init__(self, token=None, *, session=None):
    if token:
      self.token = f'token {token}'
    else:
      self.token = None
    super().__init__(session=session)

  def api_request(self, path, *args, method='get', data=None, **kwargs):
    h = kwargs.get('headers', None)
    if not h:
      h = kwargs['headers'] = {}
    h.setdefault('Accept', 'application/vnd.github.v3+json')
    if self.token:
      h.setdefault('Authorization', self.token)

    if data:
      kwargs['json'] = data
      if method == 'get':
        method = 'post'

    return self.request(path, method=method, *args, **kwargs)

  def get_issue(self, repo: str, issue_nr: int) -> 'Issue':
    r = self.api_request(
      f'/repos/{repo}/issues/{issue_nr}')
    j = r.json()
    return Issue(j, self)

  def get_repo_issues(self, repo, *, state='open', labels=''):
    params = {'state': state}
    if labels:
      params['labels'] = labels
    r = self.api_request(f'/repos/{repo}/issues', params = params)

    yield from (Issue(x, self) for x in r.json())
    while 'next' in r.links:
      r = self.api_request(r.links['next']['url'])
      yield from (Issue(x, self) for x in r.json())

  def get_user_info(self, username: str) -> Any:
    r = self.api_request(f'/users/{username}')
    return r.json()

  def get_actions_artifacts(self, repo: str) -> Iterator[Any]:
    r = self.api_request(f'/repos/{repo}/actions/artifacts')
    yield from r.json()['artifacts']
    while 'next' in r.links:
      r = self.api_request(r.links['next']['url'])
      yield from r.json()['artifacts']

  def add_issue_comment(
    self, repo: str, issue_nr: int, comment: str,
  ) -> Response:
    return self.api_request(
      f'/repos/{repo}/issues/{issue_nr}/comments',
      data = {'body': comment},
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
    self._api_url = f"{data['repository_url']}/issues/{data['number']}"

  def comment(self, comment: str) -> Response:
    return self.gh.api_request(f'{self._api_url}/comments', data = {'body': comment})

  def add_labels(self, labels):
    if not isinstance(labels, (list, tuple)):
      raise TypeError('labels should be a list')
    return self.gh.api_request(f'{self._api_url}/labels', data = labels)

  def close(self) -> None:
    self.gh.api_request(f'{self._api_url}', method = 'patch',
                        data = {'state': 'closed'})

  def __repr__(self) -> str:
    return f'<Issue {self.number}: {self.title!r}>'
