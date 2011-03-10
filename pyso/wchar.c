#include<wchar.h>

/* Like wcswidth(), but ignores non-printing characters. */
size_t width(const wchar_t *wcs){
  size_t i;
  int cw;

  for(i = 0; *wcs != L'\0'; wcs++)
    if((cw = wcwidth(*wcs)) > 0)
      i += cw;
  return i;
}
