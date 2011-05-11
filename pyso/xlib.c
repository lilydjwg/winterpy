#include<X11/Xlib.h>

/* 成功返回 1，否则返回 0 */
int test_display(const char* name){
  Display *dpy;
  if((dpy = XOpenDisplay(name)) == NULL){
    return 0;
  }
  XCloseDisplay(dpy);
  return 1;
}
