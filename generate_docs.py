import inspect

import pandas as pd

from src.dokter.analyzer import Analyzer

rules = []
for i in [(i, f) for i, f in inspect.getmembers(object=Analyzer) if i.startswith("dfa")]:
    long_desc = inspect.getdoc(i[1]).split(":return:", 1)[0]
    rule_name = i[0]
    rules.append({'Rule name': rule_name, 'Short description': inspect.getdoc(i[1]).splitlines()[0],
                  "More information": f"[{rule_name}]({rule_name}.md)"})

    with open(f"docs/{rule_name}.md", "w") as f:
        f.write(f"# {rule_name}\n\n")
        f.write(long_desc)
        print(f"Written documentation for {rule_name} to: docs/{rule_name}.md")

df = pd.DataFrame(rules)
df.to_markdown("docs/overview.md", index=False)
