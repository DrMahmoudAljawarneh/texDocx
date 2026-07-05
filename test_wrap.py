import re

# Read the actual algo snippet
with open('/shared/1a435438-4f6d-4b0e-8e57-38454f3b9835/algo_0.tex', 'r') as f:
    content = f.read()

snippet_fixed = re.sub(r'\\begin\{(algorithm|algorithm\*)\}', r'\\begin{\1}[H]', content)

# Detect package
if re.search(r'\\(STATE|WHILE|ENDWHILE|IF|ELSIF|ELSE|ENDIF|FOR|ENDFOR|REQUIRE|ENSURE|COMMENT|AND|OR|XOR|LOOP|ENDLOOP|REPEAT|UNTIL)', snippet_fixed):
    algo_pkg = "\\usepackage{algorithmic}"
else:
    algo_pkg = "\\usepackage{algpseudocode}"

doc = """\\documentclass{article}
\\usepackage[paperwidth=9999pt,paperheight=9999pt,margin=0pt]{geometry}
\\usepackage{amsmath}
\\usepackage{algorithm}
%s
\\usepackage{float}
\\pagestyle{empty}
\\begin{document}
%s
\\end{document}
""" % (algo_pkg, snippet_fixed)

with open('/tmp/test_real_wrap.tex', 'w') as f:
    f.write(doc)

print('Detected package:', algo_pkg)
print('Written', len(doc), 'bytes')
