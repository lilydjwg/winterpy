#!/usr/bin/env python3
# vim:fileencoding=utf-8

# Author: Eric Miao <eric.mjian@gmail.com>
# Modified By: lilydjwg <lilydjwg@gmail.com>

pinyinList = ['a', 'o', 'e', 'ai', 'ei', 'ao', 'ou', 'an', 'en', 'vn', 'van', 'ang', 'eng',
              'ba', 'bo', 'bi', 'bu', 'bai', 'bei', 'bao', 'bie', 'biao', 'ban', 'ben', 'bin','bian', 'bang', 'beng', 'bing',
              'pa', 'po', 'pi', 'pu', 'pai', 'pei', 'pao', 'pou', 'pie', 'piao', 'pan', 'pen', 'pin', 'pian', 'pang', 'peng', 'ping',
              'ma', 'mo', 'me', 'mi', 'mu', 'mai', 'mei', 'mao', 'mou', 'mie', 'miao', 'miu','man', 'men', 'min', 'mian', 'mang', 'meng', 'ming',
              'fa', 'fo', 'fu', 'fei', 'nao', 'fou', 'fan', 'fen', 'fang', 'feng',
              'da', 'de', 'di', 'du', 'dai', 'dao', 'dou', 'dia', 'die', 'duo', 'diao', 'diu', 'dui', 'dan', 'den', 'din', 'dian', 'duan', 'dun', 'dang', 'deng', 'ding', 'dong',
              'ta', 'te', 'ti', 'tu', 'tai', 'tao', 'tou', 'tie', 'tuo', 'tiao', 'tui', 'tan', 'tin', 'tian', 'tuan', 'tun', 'tang', 'teng', 'ting', 'tong',
              'na', 'ne', 'ni', 'nu', 'nai', 'nei', 'nao', 'nou', 'nie', 'nuo', 'nve', 'niao', 'niu', 'nan', 'nen', 'nin', 'nian', 'nuan', 'nun', 'nang', 'neng', 'ning', 'nong', 'niang',
              'la', 'le', 'li', 'lu', 'lai', 'lei', 'lao', 'lou', 'lie', 'luo', 'lve', 'liao', 'liu', 'lan', 'len', 'lin', 'lian', 'luan', 'lun', 'lang', 'leng', 'ling', 'long', 'liang',
              'ga', 'ge', 'gu', 'gai', 'gei', 'gao', 'gou', 'gua', 'guo', 'guai', 'gui', 'gan', 'gen', 'guan', 'gun', 'gang', 'geng', 'gong', 'guang',
              'ka', 'ke', 'ku', 'kai', 'kei', 'kao', 'kou', 'kua', 'kuo', 'kuai', 'kui', 'kan', 'ken', 'kuan', 'kun', 'kang', 'keng', 'kong', 'kuang',
              'ha', 'he', 'hu', 'hai', 'hei', 'hao', 'hou', 'hua', 'huo', 'huai', 'hui', 'han', 'hen', 'huan', 'hun', 'hang', 'heng', 'hong', 'huang',
              'ju', 'jiao', 'jiu', 'jian', 'juan', 'jun', 'jing', 'jiang', 'jiong', 'jia',
              'qi', 'qu', 'qia', 'qie', 'qiao', 'qiu', 'qin', 'qian', 'quan', 'qun', 'qing','qiang', 'qiong',
              'xi', 'xu', 'xia', 'xie', 'xiao', 'xiu', 'xin', 'xian', 'xuan', 'xun', 'xing','xiang', 'xiong',
              'zha', 'zhe', 'zhi', 'zhu', 'zhai', 'zhao', 'zhou', 'zhua', 'zhuo', 'zhuai', 'zhui', 'zhan', 'zhen', 'zhuan', 'zhun', 'zhang', 'zheng', 'zhong', 'zhuang',
              'cha', 'che', 'chi', 'chu', 'chai', 'chao', 'chou', 'chuo', 'chuai', 'chui', 'chan', 'chen', 'chuan', 'chun', 'chang', 'cheng', 'chong', 'chuang',
              'sha', 'she', 'shi', 'shu', 'shai', 'shao', 'shou', 'shua', 'shuo', 'shuai', 'shui', 'shan', 'shen', 'shuan', 'shun', 'shang', 'sheng', 'shong', 'shuang',
              're', 'ri', 'ru', 'rao', 'rou', 'ruo', 'rui', 'ran', 'ren', 'ruan', 'run', 'rang', 'reng', 'rong',
              'za', 'ze', 'zi', 'zu', 'zai', 'zei', 'zao', 'zou', 'zuo', 'zui', 'zan', 'zen','zuan', 'zun', 'zang', 'zeng', 'zong',
              'ca', 'ce', 'ci', 'cu', 'cai', 'cao', 'cou', 'cuo', 'cui', 'can', 'cen', 'cuan', 'cun', 'cang', 'ceng', 'cong',
              'sa', 'se', 'si', 'su', 'sai', 'sao', 'sou', 'suo', 'sui', 'san', 'sen', 'suan', 'sun', 'sang', 'seng', 'song',
              'ya', 'yo', 'ye', 'yi', 'yu', 'yao', 'you', 'yan', 'yin', 'yuan', 'yun', 'yang', 'ying', 'yong',
              'wo', 'wu', 'wai', 'wei', 'wan', 'wen', 'wang', 'weng', 'yong', 'er']


def split_pinyin(word):
  print('=' * 12)
  print(word)
  output = False
  ps = []
  if len(word) == 0:
    return True, []

  pres = []
  for pinyin in pinyinList:
    l = len(pinyin)
    if word[:l] == pinyin:
      pres.append(pinyin)
  print(pres)

  if not pres:
    return False, []

  for pre in pres:
    r, rp = split_pinyin(word[len(pre):])
    if r:
      output = True
      ps.append(pre)
      ps.extend(rp)
      break
  return output, ps

if __name__ == '__main__':
  import sys
  print(split_pinyin(''.join(sys.argv[1:]) if len(sys.argv) > 1 else 'zheshiyigeceshi'))
