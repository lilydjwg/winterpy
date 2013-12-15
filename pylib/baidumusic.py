import json

from htmlutils import parse_document_from_requests
from musicsites import Base, SongInfo

class BaiduMusic(Base):
  def get_songs_from_list(self, url):
    doc = parse_document_from_requests(url, self.session)
    rows = doc.xpath(
      '//*[contains(concat(" ", normalize-space(@class), " "), " song-item ")]')
    songs = []

    for tr in rows:
      try:
        a = tr.xpath('./span[@class="song-title"]/a')[0]
      except IndexError:
        # some lists contain empty items...
        # e.g. index 30 of this:
        # http://music.baidu.com/search/song?key=70%E5%90%8E&start=20&size=20
        continue
      href = a.get('href')
      sid = href.rsplit('/', 1)[-1]
      title = a.text_content()
      artists = tuple(
        a.text_content() for a in
        tr.xpath('./span[@class="singer"]/span/a'))
      try:
        album = tr.xpath('./span[@class="album-title"]/a')[0].text_content().strip()
        album = album.lstrip('《').rstrip('》')
      except IndexError:
        album = None
      song = SongInfo(sid, title, href, artists, album, None)
      songs.append(song)

    return songs

  def get_song_info(self, sid):
    '''
    其中，``songLink`` 键是歌曲下载地址，``songName`` 是歌曲名
    '''
    s = self.session
    url = 'http://music.baidu.com/data/music/fmlink?songIds=' + sid
    r = s.get(url)
    return json.loads(r.text)['data']['songList'][0]
