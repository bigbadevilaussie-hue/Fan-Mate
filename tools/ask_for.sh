# Fan-Mate handoff dump. Run: zsh tools/ask_for.sh
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
D="$HOME/Desktop"

python3 -c "
import os
root = os.path.expanduser('/Users/Nick/Documents/Arduino/fanmate')
out  = os.path.expanduser('$HOME/Desktop/repo.txt')
L = []
for f in sorted(os.listdir(root)):
    p = os.path.join(root, f)
    if not os.path.isfile(p): continue
    L += ['='*70, 'FILE: ' + f, '='*70]
    try: L.append(open(p, errors='replace').read())
    except Exception as e: L.append('ERROR: ' + str(e))
    L.append('')
open(out, 'w').write(chr(10).join(L))
print('wrote', out)
"

python3 -c "
import os
root = os.path.expanduser('/Users/Nick/Documents/Arduino/fanmate')
out  = os.path.expanduser('$HOME/Desktop/dump.txt')
L = []
for base, exts in [(root+'/fanmate_v2', ['.qml']), (root+'/fanmate', ['.py'])]:
    for r, d, fs in os.walk(base):
        for f in sorted(fs):
            if not any(f.endswith(e) for e in exts): continue
            p = os.path.join(r, f)
            L += ['='*70, 'FILE: ' + p.replace(root, 'fanmate'), '='*70, open(p, errors='replace').read(), '']
for r, d, fs in os.walk(root):
    for f in fs:
        if f == 'WebPage.h':
            p = os.path.join(r, f)
            L += ['='*70, 'FILE: ' + p.replace(root, 'fanmate'), '='*70, open(p, errors='replace').read(), '']
open(out, 'w').write(chr(10).join(L))
print('wrote', out)
"

python3 -c "
import os
root = os.path.expanduser('/Users/Nick/Documents/Arduino/fanmate')
out  = os.path.expanduser('$HOME/Desktop/firmware_dump.txt')
L = []
for f in sorted(os.listdir(root)):
    if not f.endswith(('.ino', '.cpp', '.h')): continue
    p = os.path.join(root, f)
    if not os.path.isfile(p): continue
    L += ['='*70, 'FILE: ' + f, '='*70, open(p, errors='replace').read(), '']
open(out, 'w').write(chr(10).join(L))
print('wrote', out)
"

echo ''
echo 'Dumps written to:'
echo '  '$D'/repo.txt'
echo '  '$D'/dump.txt'
echo '  '$D'/firmware_dump.txt'
echo ''
echo 'Also ask for:'
echo '  ls ~/Documents/Arduino/libraries/Adafruit_SSD1306_72x40/'
echo '  git ls-files secrets.h'
