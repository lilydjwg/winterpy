<!DOCTYPE html>
<html>
  <head>
    <meta http-equiv="content-type" content="text/html; charset=utf-8" />
    <title>Index of /{{path}}</title>
    <style type="text/css">
    <!--
      table { width: 900px; border-collapse: collapse; }
      td { padding: 0 0.2em; }
      tr:hover { background: #add8e6; }
      td.size { text-align: right; }
      td.time { width: 19ex; }
    -->
    </style>
  </head>
  <body>
    <!--[if lt IE 7]><div style=' clear: both; height: 59px; padding:0 0 0 15px; position: relative;'><a href="http://www.microsoft.com/windows/internet-explorer/default.aspx?ocid=ie6_countdown_bannercode"><img src="http://www.theie6countdown.com/images/upgrade.jpg" border="0" height="42" width="820" alt="" /></a></div><![endif]-->
    <h1>Index of /{{path}}</h1>
    <hr/>
    <table>
      %if path:
      <tr>
	<td><a href="../">../</a></td>
	<td></td>
	<td></td>
      </tr>
      %end
      %for f in files:
      <tr>
	<td><a href="{{f.name}}">{{f.name}}</a></td>
	<td class="size" align="right">{{f.size}}</td>
	<td class="time">{{f.time}}</td>
      </tr>
      %end
    </table>
    <hr/>
  </body>
</html>
<!-- vim:se ft=html: -->
