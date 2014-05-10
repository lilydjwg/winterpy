import urllib.parse
from functools import partial

from tornado import escape
from tornado.auth import OAuth2Mixin, _auth_return_future, AuthError
from tornado.httputil import url_concat
from tornado.httpclient import AsyncHTTPClient
from tornado.concurrent import return_future

class WeiboMixin(OAuth2Mixin):
  '''Weibo OAuth 2.0 authentication'''
  _OAUTH_NO_CALLBACKS = False

  _WEIBO_BASE_URL = 'https://api.weibo.com/oauth2/'
  # for the mobile client, the following should be used
  # _OAUTH_URL_BASE = 'https://open.weibo.cn/oauth2/'

  _OAUTH_ACCESS_TOKEN_URL = _WEIBO_BASE_URL + 'access_token'
  _OAUTH_AUTHORIZE_URL = _WEIBO_BASE_URL + 'authorize'

  REQUEST_FIELDS = frozenset({
    'id', 'idstr', 'name', 'screen_name', 'province', 'city', 'location',
    'description', 'url', 'profile_image_url', 'gender', 'domain',
    'followers_count', 'friends_count', 'statuses_count', 'favourites_count',
    'created_at', 'following', 'allow_all_act_msg', 'geo_enabled', 'verified',
    'allow_all_comment', 'avatar_large', 'verified_reason', 'follow_me',
    'online_status', 'bi_followers_count',
  })

  def get_auth_http_client(self):
    return AsyncHTTPClient()

  @_auth_return_future
  def get_authenticated_user(self, redirect_uri, client_id, client_secret,
                             code, callback, extra_fields=None):
    http = self.get_auth_http_client()
    args = {
      "redirect_uri": redirect_uri,
      "code": code,
      "client_id": client_id,
      "client_secret": client_secret,
    }

    if extra_fields:
      fields = self.REQUEST_FIELDS & extra_fields
    else:
      fields = self.REQUEST_FIELDS

    http.fetch(
      self._OAUTH_ACCESS_TOKEN_URL,
      partial(
        self._on_access_token, redirect_uri, client_id,
        client_secret, callback, fields
      ),
      method = 'POST',
      body = urllib.parse.urlencode(args),
    )

  def _on_access_token(self, redirect_uri, client_id, client_secret,
                       future, fields, response):
    if response.error:
      future.set_exception(AuthError(
        'SinaWeibo auth error: %s' % str(response)))
      return

    args = escape.json_decode(response.body)
    session = {
      'access_token': args['access_token'],
      'expires_in': args['expires_in'],
      'uid': args['uid'],
    }

    weibo_request(
      path = 'users/show',
      callback = partial(
        self._on_get_user_info, future, session, fields,
      ),
      access_token = session['access_token'],
      uid = session['uid'],
      httpclient = self.get_auth_http_client(),
    )

  def _on_get_user_info(self, future, session, fields, user):
    fieldmap = {field: user.get(field) for field in fields}

    fieldmap['access_token'] = session['access_token']
    fieldmap['session_expires'] = session['expires_in']
    future.set_result(fieldmap)

@_auth_return_future
def weibo_request(path, callback, access_token=None, post_args=None,
                  httpclient=None, **args):
  url = "https://api.weibo.com/2/" + path + ".json"
  all_args = {}
  if access_token:
    all_args['access_token'] = access_token
  all_args.update(args)
  if post_args:
    all_args.update(post_args)

  header = {'Authorization': 'OAuth2 ' + access_token}
  callback = partial(_on_weibo_request, callback)
  http = httpclient or AsyncHTTPClient()

  if post_args is not None:
    http.fetch(
      url, method="POST", body=urllib.parse.urlencode(all_args),
      callback=callback, headers=header)
  else:
    if all_args:
      url = url_concat(url, all_args)
    http.fetch(url, callback=callback, headers=header)

def _on_weibo_request(future, response):
  body = response.body.decode('utf-8')
  if response.error:
    try:
      ex = WeiboError(body)
    except:
      ex = WeiboRequestError(response)
    future.set_exception(ex)
  future.set_result(escape.json_decode(body))

class WeiboRequestError(Exception):
  pass

class WeiboError(WeiboRequestError):
  def __init__(self, body):
    # doc: http://open.weibo.com/wiki/Error_code
    self._raw = body
    info = escape.json_decode(body)
    self.path = info['request']
    self.code = info['error_code']
    self.msg = info['error']

  def __repr__(self):
    return '%s(%r)' % (
      self.__class__.__name__, self._raw)

@return_future
def send_status(status, access_token, callback,
                annotations=None, httpclient=None):
  args = {
    'status': status,
  }
  if annotations:
    args['annotations'] = annotations
  weibo_request('statuses/update', callback,
                access_token = access_token,
                httpclient = httpclient, post_args = args)
