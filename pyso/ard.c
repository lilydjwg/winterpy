#include<stdio.h>
#include<string.h>
#include<iconv.h>
#define LEN 102400
char string[LEN] = {0};

static char ardd(char d){
  return d < 60 ? d - 48 : d < 91 ? d - 53 : d == 94 ? 10 : d - 59;
}
int code_convert(short int *src, char *dest){
  iconv_t cd;
  char **pin = (char**)&src;
  char **pout = &dest;
  size_t inlen;
  size_t outlen = LEN;
  for(inlen=0; src[inlen] !=0; inlen++);
  inlen *= 2;

  cd = iconv_open("utf-8", "utf16le");
  if(cd == 0)
    return -1;
  memset(dest, 0, outlen);
  if(iconv(cd, pin, &inlen, pout, &outlen) == -1)
    return -1;
  iconv_close(cd);
  return 0;
}

char *ard(const char *s, const char *y){
  short int t[LEN] = {0};
  char k[LEN] = {0};
  int d, x;
  int i, j;
  int z = 0;
  int l = strlen(y);
  int m = 0;

  for(i = 0; i < l; i++){
    k[i] = ardd(y[i]);
  }

  for(i = 0, j = 0; i < strlen(s); i++, j = (j + 1 == l) ? 0 : j + 1){
    d = s[i];
    if(z == 0){
      if(d == 94 || (d > 47 && d < 60) || (d > 64 && d < 91) || (d > 96 && d < 123)){/*字符 '^' '0'-'9' 'A'-'Z' 'a'-'z' */
	x = ardd(d) ^ k[j];
	t[m] = (x == 10 ? 94 : x < 12 ? x + 48 : x < 38 ? x + 53 : x + 59);
	m++;
      }else if(d > 60 && d < 65){/*'=' '>' '?' '@' */
	x = (d - 61) ^ (k[j] & 3);
	z = 1;
      }else{
	x = (d == 95 ? 0 : d == 91 ? 2 : d == 93 ? 7 : d >
	    123 ? d - 110 : d - 32) ^ (k[j] & 15);
	z = 2;
      }
    }else{
      x = (x << 6) + (ardd(d) ^ k[j]);
      if(z == 2){
	z = 3;
      }else{
	t[m] = x;
	m++;
	z = 0;
      }
    }
  }

  code_convert(t, string);
  return string;
}

int main(){
  /* ard("[11|Hf", "PeN"); */
  ard("?2qm3aI=z437B@D?Kac3r@Gz6s@T>A@JBoCaxH?b>t1aZJCD@L?w;tsIWY8?5dl58315?c7flI5?0@2=k54AKF?g=G?o?r>q?h@E>GSEJb3qq?i@E@H=V>1^DAQbB@W7kyL@3=x4LDS@RxGYY6awHW7=x>3MQR3?QtpL?X>pxSL>3V2k?g^DBj@;U?yo@2i@bV?jg?2dOFVyh7p4N0xXVj>TK?nO9@0HmFv@bhtc>T^fjc>dJ=UbmBm^?h3q?1sR>eyH^iG?OsCojRpxqDf@1qhDVo?vPyrZg?kn91OH@2nLgQxrDliPojrZ?xRU2pv@AjK3N^H?xX?z2=xY@6crspXERT^JD>Te=mMu?gL31U0@3AGt46Xgei?gjnvZpJXOf=Va>BD@Ao5VQ@CPA4nn?xi8O67G=UhB8@2^5w3bTE@5Ia9Ust@;CP^kE>0jO;3i=UKvw7r?yEii>Bnv2fWH?0MTmYLD@0UDLCD?;;3Bm@0BBkx;a6TZ?jicoj7E=LhuW00@b8uapU?3HqBbD=Udw1R3XA>Tlqu^3@3RWBAgS@Ao0Wsf?pf3lqTlWm?vWXbGr^?oUh4=VfcyT;?hdZsBu@2sB6fBq@bf31w@wMyq>eYrdhTdLVn7>TGDR3ZJ?z260?NhaR7J?1Hl7UA=UGCo@4jd83@yx39K^4H=xWKczYDEClD@31eDg=xVN6@GYiFmw?x44xaXw?MI1I0Z?3Iw;3x=VP9DRB?gW;B8e@2^4ucZ>B88oae@zYtx>cFmS;lXicx?;klsypf?yEiik?NR7jn?2izMlA7=UU78J9L?;;3Blq=LilAlB@bc8j9e@yx39K?z233?NhaR7?2hkp=LioC>2aa8AXs35?lY;H?z2775yQ?hUSl0RQiR6=Udsjg@D83dK?lTsY?x20B@b8vZz@xXlqW?ynL9s2@6jj4jx7x?x44xXj=mIn6KfQ?3Iw;7p6?xi8O?m24;8?kh9e0yRyf?MjnVDC@ySuiTBdU4>DxA4?;kkzu@0^3kjA>Bnu1cAPFu?oGYso@0UCGiH?;;7j?qUeCk8>2aa893>TGDR3C1?z26;H?v1O0Sq?nK0bCl@2dnI1^K=VIi5B=LhuW0>Aq@Bl=VV?lM>eVDT1Df2sU?98?0TRFFBo@0UDL?mVxhc?lK7h9lTQf@bc8j9c@yx39Lj=WU02Kh350@xXol>dcJL>3IG3gOl?2B6zxW?x20B2M@B6pgs4Efq@1jgv98@6cZ2@xFw;g@3RWBAY@4aH7UwbA?xYqo?xi9R4VK=Uh9e@2^4ud^>B88obZ@zYtxdT?yt90C?vWWZ@xe;wf@3Oc;du@5Ia9YO?kRdMB3GXm@bf31wibz6@0B8q@2G1V@BDDX?0MPn@0af0>DxB36qi@yRl0iW>TCp6?vVdCW?0MTmZ@0A37@bf31wi@yRl0?yEjgl?NR6j^V0@CspXzq1mm?NhaR6O?1Hl7VY=UGCoH1dti?2B6zwX?x20B2K@B6pg?3Hr^YHgN=xVR6DbVys8@;ih3>ThBb4@Ao0Ws@CPB3bqO>2jR15X=UhB8yW@3Oc;>B89nY=WM@CL=L1=UZp?MXVLm4hO;v>caSLo=mN9?gPN2?nR>eqzVY4qpko?^2c3FlV@3E6zb?MNv@o5^y@;V?yzS>0A@4e?K@i?i@Tj6zeCfsKs4?K@f?b@1@Fsr^H7S@A?8@X?X@E@SaZCAS@P?z=m?0?6>R?wb433B@Gf^ec?n@TiIxa>GOT3?k=V?Elh7iDfq>F?94Ic0apCl@F@Ezt7L3G8?y=lxMoy^cL=n>HB11QjOYZBo@F@Ezt7ESBI7p^Y?G?Z2l4tl6=9CJ^b5tw?os9YI;?0>C@I^f^ic?k", "2yC;xLy0TxxmbvmGoT");
  puts(string);
  return 0;
}
