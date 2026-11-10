#!/usr/bin/env python3
"""Public-source housing radar. No credentials, no personal data, no availability claims.

Run with: python monitor.py
On GitHub Actions a scheduled workflow commits data/updates.json + data/monitor_state.json.
A detected change is a lead to check, NOT confirmation of an open registration.
"""
from __future__ import annotations
import hashlib
import json
import re
from datetime import datetime, timedelta, timezone
from email.utils import parsedate_to_datetime
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import quote
from urllib.request import Request, urlopen
import xml.etree.ElementTree as ET

BASE = Path(__file__).resolve().parent
DATA = BASE / "data"
STATE_FILE = DATA / "monitor_state.json"
FEED_FILE = DATA / "updates.json"
NOW = datetime.now(timezone.utc)
TIMEOUT = 22

SOURCES = [
    {"name": "EMVIALSA · convocatorias", "area": "Alcobendas", "url": "https://emvialsa.org/acceso-a-la-vivienda/inscripciones"},
    {"name": "EMVIALSA · noticias", "area": "Alcobendas", "url": "https://emvialsa.org/"},
    {"name": "Valgrande · web oficial", "area": "Valgrande", "url": "https://valgrandealcobendas.es/"},
    {"name": "Cerro del Baile · web oficial", "area": "Cerro del Baile", "url": "https://cerrodelbaile.es/"},
    {"name": "CooperOpen · Valgrande", "area": "Valgrande", "url": "https://cooperopen.org/valgrande"},
    {"name": "CooperOpen · Cerro del Baile", "area": "Cerro del Baile", "url": "https://cooperopen.org/san-sebastian-de-los-reyes"},
    {"name": "Víveme · Valgrande", "area": "Valgrande", "url": "https://www.pisosenvalgrande.es/"},
    {"name": "Grupo Ibosa · futuras promociones", "area": "Zona norte", "url": "https://www.grupoibosa.com/?format=html&id=11&view=category"},
    {"name": "Nysa Valgrande", "area": "Valgrande", "url": "https://www.nysavalgrande.com/"},
]

SEARCHES = [
    ("Valgrande", 'Valgrande Alcobendas (vivienda OR pisos OR cooperativa OR promoción OR protegida) when:7d'),
    ("Cerro del Baile", '"Cerro del Baile" (viviendas OR cooperativa OR inscripción OR promotora) when:7d'),
    ("Alcobendas", 'EMVIALSA (convocatoria OR inscripción OR adjudicación OR viviendas) when:7d'),
]

class TextExtractor(HTMLParser):
    SKIP = {"script", "style", "noscript", "svg", "footer", "nav", "header", "form"}
    VOID = {"area", "base", "br", "col", "embed", "hr", "img", "input", "link", "meta", "param", "source", "track", "wbr"}
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.skip_depth = 0
        self.parts: list[str] = []
    def handle_starttag(self, tag, attrs):
        if (self.skip_depth or tag in self.SKIP) and tag not in self.VOID:
            self.skip_depth += 1
    def handle_endtag(self, tag):
        if self.skip_depth:
            self.skip_depth -= 1
    def handle_data(self, data):
        if not self.skip_depth:
            self.parts.append(data)

def page_fingerprint(raw: bytes) -> str:
    parser = TextExtractor()
    parser.feed(raw.decode('utf-8', errors='replace'))
    cleaned = re.sub(r"\s+", " ", " ".join(parser.parts)).strip().casefold()
    if len(cleaned) < 60:
        raise ValueError("Page returned too little readable text")
    return hashlib.sha256(cleaned[:80000].encode('utf-8')).hexdigest()

def fetch(url: str) -> bytes:
    req = Request(url, headers={"User-Agent": "Mozilla/5.0 (compatible; NorteRadar/1.0; public-pages-monitor)", "Accept": "text/html,application/rss+xml,application/xml;q=0.9,*/*;q=0.7"})
    with urlopen(req, timeout=TIMEOUT) as resp:
        if resp.status != 200:
            raise ValueError(f"HTTP {resp.status}")
        return resp.read(2_000_000)

def event_id(s: str) -> str:
    return hashlib.sha256(s.encode('utf-8')).hexdigest()[:24]

def parse_rss(body: bytes, area: str) -> list[dict]:
    root = ET.fromstring(body)
    out = []
    for item in root.findall('./channel/item')[:22]:
        title = (item.findtext('title') or '').strip()
        link = (item.findtext('link') or '').strip()
        pub = (item.findtext('pubDate') or '').strip()
        try:
            published = parsedate_to_datetime(pub).astimezone(timezone.utc)
        except (TypeError, ValueError, OverflowError):
            continue
        if not title or not link or published < NOW - timedelta(days=9) or published > NOW + timedelta(days=1):
            continue
        source_node = item.find('source')
        source = (source_node.text or '').strip() if source_node is not None else 'Google News · prensa'
        out.append({
            'id': event_id('news|'+title.casefold()),
            'title': title[:220], 'source': source[:100], 'area': area,
            'kind': 'Noticia', 'date': published.date().isoformat(),
            'url': link, 'summary': 'Titular detectado automáticamente. Confirma su contenido y cualquier plazo en la fuente original.'
        })
    return out

def read_json(path: Path, default):
    try: return json.loads(path.read_text('utf-8'))
    except (FileNotFoundError, json.JSONDecodeError): return default

def main() -> None:
    DATA.mkdir(exist_ok=True)
    previous_state = read_json(STATE_FILE, {'pages': {}})
    previous_feed = read_json(FEED_FILE, {'items': []})
    snapshots = dict(previous_state.get('pages', {}))
    found: list[dict] = []
    succeeded = 0
    for s in SOURCES:
        url = s['url']
        try:
            fingerprint = page_fingerprint(fetch(url))
            succeeded += 1
            prior = snapshots.get(url)
            if prior and prior != fingerprint:
                found.append({
                    'id': event_id('page|'+url+'|'+fingerprint),
                    'title': 'Cambio detectado: ' + s['name'],
                    'source': s['name'], 'area': s['area'],
                    'kind': 'Cambio de web', 'date': NOW.date().isoformat(),
                    'url': url,
                    'summary': 'El contenido público de la página ha cambiado. No confirma nuevas plazas: revisa los detalles en la fuente.'
                })
            snapshots[url] = fingerprint
            print('OK page:', s['name'], '(changed)' if prior and prior != fingerprint else '')
        except Exception as e:
            print('WARN page:', s['name'], str(e))
    for area, query in SEARCHES:
        rss_url = 'https://news.google.com/rss/search?q='+quote(query)+'&hl=es&gl=ES&ceid=ES:es'
        try:
            items = parse_rss(fetch(rss_url), area)
            succeeded += 1
            found.extend(items)
            print('OK RSS:', area, len(items))
        except Exception as e:
            print('WARN RSS:', area, str(e))
    if succeeded == 0:
        raise SystemExit('No sources could be fetched; preserving previous feed')
    kept = [x for x in previous_feed.get('items', []) if isinstance(x, dict) and x.get('date', '1900') >= (NOW.date()-timedelta(days=28)).isoformat()]
    combined = {x['id']:x for x in kept if x.get('id')}
    for item in found:
        combined[item['id']] = item
    # Ignore duplicates if a story appears in multiple Google News searches.
    unique_titles = set()
    fresh = []
    for x in sorted(combined.values(), key=lambda x:(x.get('date', ''), x.get('kind')=='Cambio de web'), reverse=True):
        title_key = re.sub(r'\W+', '', x.get('title','').casefold())[:160]
        if title_key in unique_titles: continue
        unique_titles.add(title_key)
        fresh.append(x)
    payload = {'mode': 'automatic', 'updated_at': NOW.isoformat(timespec='seconds'), 'items': fresh[:70], 'sources_ok': succeeded, 'sources_total': len(SOURCES)+len(SEARCHES)}
    FEED_FILE.write_text(json.dumps(payload, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
    STATE_FILE.write_text(json.dumps({'pages': snapshots}, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
    print(f'Wrote {len(payload["items"])} items; checked {succeeded}/{payload["sources_total"]} sources')

if __name__ == '__main__':
    main()
