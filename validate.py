#!/usr/bin/env python3
"""Validate public artifacts, true static routes, local references and metadata."""
from pathlib import Path
from html.parser import HTMLParser
from urllib.parse import urlparse
import json
import re
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parent / 'dist'
BASE = '/belieftrace'
ROUTES = ['/', '/privacy/', '/terms/', '/support/', '/safety/', '/data/']


class Inspect(HTMLParser):
    def __init__(self):
        super().__init__(); self.refs=[]; self.ids=set(); self.h1=0; self.main=0; self.meta={}; self.images=[]; self.canonical=[]
    def handle_starttag(self, tag, attrs):
        attrs=dict(attrs)
        if attrs.get('id'): self.ids.add(attrs['id'])
        if tag in ['a','link','img']:
            ref=attrs.get('href') or attrs.get('src')
            if ref:self.refs.append(ref)
        if tag=='h1':self.h1+=1
        if tag=='main':self.main+=1
        if tag=='img':self.images.append(attrs)
        if tag=='meta':self.meta[attrs.get('name') or attrs.get('property')]=attrs.get('content')
        if tag=='link' and attrs.get('rel')=='canonical':self.canonical.append(attrs['href'])


def main():
    checked=0
    for route in ROUTES:
        file=ROOT/route.strip('/')/'index.html'
        text=file.read_text();p=Inspect();p.feed(text)
        assert p.h1==1 and p.main==1,(file,'semantic landmarks')
        assert p.meta.get('viewport') and p.meta.get('description'),(file,'missing metadata')
        assert p.meta.get('og:url')==f'https://shinywesley.github.io{BASE}{route}'
        assert p.canonical==[f'https://shinywesley.github.io{BASE}{route}']
        assert not re.search(r'\{\{|TODO|TBD|Coming soon|60 successful|rolling 24|com\.shinyw\.belieftrace\.plus\.monthly|test_[A-Za-z0-9]{20,}|appl_[A-Za-z0-9]{20,}|/Users/',text)
        assert '<script' not in text
        for img in p.images:assert 'alt' in img and img.get('width') and img.get('height')
        for ref in p.refs:
            url=urlparse(ref)
            if url.scheme or ref.startswith('//'):continue
            if not url.path:
                assert url.fragment in p.ids,(route,ref);continue
            assert url.path.startswith(BASE+'/'),(route,'wrong project base',ref)
            rel=url.path[len(BASE):].lstrip('/')
            target=ROOT/rel
            if target.is_dir():target=target/'index.html'
            assert target.is_file(),(route,'missing direct file',ref)
            if url.fragment:
                q=Inspect();q.feed(target.read_text());assert url.fragment in q.ids,(route,ref)
            checked+=1
    for file in ROOT.rglob('*'):
        if not file.is_file():continue
        assert file.suffix in {'.html','.png','.css','.xml','.txt',''}
        assert not re.search(rb'-----BEGIN (?:RSA |EC )?PRIVATE KEY-----|\bsk-(?:proj-|svcacct-)?[A-Za-z0-9_-]{35,}|\bghp_[A-Za-z0-9_]{35,}',file.read_bytes())
    ET.parse(ROOT/'sitemap.xml')
    assert (ROOT/'404.html').is_file() and (ROOT/'robots.txt').is_file()
    print(json.dumps({'status':'PASS','routes':len(ROUTES),'local_references_checked':checked,'tracking_scripts':0,'unresolved_product_values':0,'private_secret_patterns':0}))


if __name__=='__main__':main()
