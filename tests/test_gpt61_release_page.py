#!/usr/bin/env python3
import json
from pathlib import Path
P=Path(__file__).resolve().parents[1]
s=(P/"models/gpt-6-1/index.html").read_text()
assert s.count('rel="canonical" href="https://sxf.si/models/gpt-6-1/"')==1
assert s.count("data-gpt61-release-guide")==1 and s.count("data-gpt61-cache")==1
assert 'No post-baseline factual changes recorded for  since' not in s and '{{' not in s
assert 'data-change-models="gpt-6.1-sol"' in s
assert len(s)>25000
j=json.loads(s.split('<script type="application/ld+json">',1)[1].split('</script>',1)[0])["@graph"]
assert next(x for x in j if x["@type"]=="ItemList")["numberOfItems"]==1
assert len(next(x for x in j if x["@type"]=="FAQPage")["mainEntity"])==14
assert 'enrich_gpt61_release_page' in (P/"scripts/update_news.py").read_text()
print("PASS GPT-6.1 editorial release hub")
