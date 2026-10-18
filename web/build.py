import re, sys
w = sys.argv[1]
h = open(w + '/huelle.html').read()
css = open('kanaldb/static/leaflet/leaflet.css').read()
css = re.sub(r'/\*.*?\*/', '', css, flags=re.S)
css = re.sub(r'\n\s*\n', '\n', css)
js = open(w + '/app.js').read()
assert '</script' not in js.lower()
open(w + '/kanalbetrieb.html', 'w').write(h.replace('/*__LEAFLET_CSS__*/', css).replace('/*__APP_JS__*/', js))
print('gebaut', len(h) + len(css) + len(js))
