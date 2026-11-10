#!/usr/bin/env python3
"""Generate seven animated, self-contained SVGs for the Code-Theory GitHub profile.

    python scripts/render_readme_cards.py                # render from saved GitHub JSON
    python scripts/render_readme_cards.py --refresh       # fetch REAL GitHub calendar first
    STATIC=1 python scripts/render_readme_cards.py --data data/demo.json --out preview/cards

Each card is safe to include via <img>: internal CSS keyframes, optional decorative
SMIL, embedded subset WOFF, no JavaScript or external assets. The empty initial
JSON produces a clearly labeled no-data state, never fictitious GitHub numbers.
"""
from __future__ import annotations
import argparse
import base64
import calendar
from collections import defaultdict
from datetime import date, datetime, timedelta, timezone
import json
import math
import mimetypes
import os
from pathlib import Path
import subprocess
import tempfile
import urllib.error
import urllib.request
from xml.sax.saxutils import escape

ROOT = Path(__file__).resolve().parents[1]
USER = os.environ.get('GITHUB_USERNAME','Code-Theory')
STATIC = os.getenv('STATIC') == '1'

# EDIT THESE to change the entire profile's personality.
PAPER = '#F8F7F1'
INK = '#191D1D'
DARK = '#171B1C'
MUTED = '#676E6B'
LINE = '#DADBD2'
LIME = '#D6FB65'            # brand / contribution graph
PURPLE = '#C9C3FE'
PEACH = '#FFB998'
SOFTGREEN = '#E4F0D4'
SOFTPURPLE = '#ECEAFE'
SOFTPEACH = '#FCEBE0'
WHITE = '#FEFEF9'
STEEL = '#929D9B'

NAME = 'Daksh Gangwar'
TAGLINE = 'I build things, optimise them, and secure them.'



def esc(v):
    return escape(str(v), {'"':'&quot;',"'":'&apos;'})


def R(x,y,w,h,fill,rx=0, extra=''):
    return f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{rx}" fill="{fill}" {extra}/>'


def T(x,y,s,size=18,color=INK,klass='body',anchor=None,delay=None,extra=''):
    a = f' text-anchor="{anchor}"' if anchor else ''
    style=f' style="--delay:{delay:.2f}s"' if delay is not None else ''
    return f'<text x="{x}" y="{y}" font-size="{size}" fill="{color}" class="{klass}"{a}{style} {extra}>{esc(s)}</text>'


def P(d,stroke=INK,width=2,fill='none',extra=''):
    return f'<path d="{d}" fill="{fill}" stroke="{stroke}" stroke-width="{width}" stroke-linecap="round" stroke-linejoin="round" {extra}/>'


def A(cx,cy,color=INK,scale=1,klass='arrow',delay=0):
    return P(f'M{cx-11*scale} {cy+11*scale}L{cx+11*scale} {cy-11*scale} M{cx-4*scale} {cy-11*scale}H{cx+11*scale}V{cy+4*scale}',color,2.5*scale,extra=f'class="{klass}" style="--delay:{delay}s"')


def font_sources():
    """Fonts locally installed on runner; never serve or ship standalone font files."""
    return {
        'Display': os.environ.get('FONT_DISPLAY','/usr/share/fonts/opentype/inter/InterDisplay-Black.otf'),
        'Body': os.environ.get('FONT_BODY','/usr/share/fonts/opentype/inter/Inter-Regular.otf'),
        'Mono': os.environ.get('FONT_MONO','/usr/share/fonts/truetype/liberation/LiberationMono-Regular.ttf'),
    }


def fonts_css():
    lines=[]
    glyphs=''.join(chr(i) for i in range(32,127))+'·—–’→↗•∞'
    with tempfile.TemporaryDirectory() as tmp:
        chars=Path(tmp)/'glyphs.txt'; chars.write_text(glyphs,encoding='utf-8')
        for family,path in font_sources().items():
            if not Path(path).is_file():
                raise FileNotFoundError(f'Missing local font {path}; install fonts-inter and fonts-liberation. Or set FONT_DISPLAY/FONT_BODY/FONT_MONO.')
            out=Path(tmp)/(family+'.woff')
            subprocess.run(['pyftsubset',path,f'--output-file={out}',f'--text-file={chars}',
                            '--flavor=woff','--no-hinting','--layout-features=*'],
                           check=True,stdout=subprocess.DEVNULL)
            encoded=base64.b64encode(out.read_bytes()).decode()
            lines.append(f"@font-face{{font-family:'{family}';src:url(data:font/woff;base64,{encoded}) format('woff');font-weight:400;font-style:normal}}")
    return '\n'.join(lines)

FONT_CSS = ''


def style():
    rules = '''
      text { text-rendering:geometricPrecision; }
      .display { font-family:'Display',sans-serif; font-weight:400; letter-spacing:-1.3px; }
      .body { font-family:'Body',sans-serif; font-weight:400; }
      .mono { font-family:'Mono',monospace; letter-spacing:1px; }
      .in { opacity:0; animation:comeIn .76s cubic-bezier(.16,1,.3,1) var(--delay,0s) both; }
      .fade { opacity:0; animation:fadeIn .8s ease var(--delay,0s) both; }
      .cell { opacity:0; animation:cellIn .32s ease-out var(--delay,0s) both; }
      .grow { transform:scaleY(0); transform-box:fill-box; transform-origin:bottom center; animation:barIn .9s cubic-bezier(.15,1,.28,1) var(--delay,0s) both; }
      .trace { stroke-dasharray:350; stroke-dashoffset:350; animation:traceIn 2.2s ease var(--delay,0s) both; }
      .float { animation:bob 6s ease-in-out 3s infinite; }
      .arrow { animation:nudge 2.6s ease-in-out 5s infinite; }
      .cursor { animation:blink 1s steps(1) 2.1s infinite; }
      .smil {display:inline} .still {display:none}
      @keyframes comeIn {from{opacity:0;transform:translateY(18px)}to{opacity:1;transform:translateY(0)}}
      @keyframes fadeIn {to{opacity:1}}
      @keyframes cellIn {from{opacity:0;transform:scale(.45)}to{opacity:1;transform:scale(1)}}
      @keyframes barIn {to{transform:scaleY(1)}}
      @keyframes traceIn {to{stroke-dashoffset:0}}
      @keyframes bob {50%{transform:translateY(-7px)}}
      @keyframes nudge {0%,78%,100%{transform:translate(0,0)}89%{transform:translate(5px,-5px)}}
      @keyframes blink {50%{opacity:0}}
      @media(prefers-reduced-motion:reduce){
        *,*::before,*::after{animation:none!important;transition:none!important;transform:none!important;opacity:1!important}
        .smil {display:none!important} .still {display:inline!important} .trace{stroke-dashoffset:0!important}
      }
    '''
    if STATIC:
        rules+='''\n*,*::before,*::after{animation:none!important;transform:none!important;opacity:1!important}
.smil{display:none!important}.still{display:inline!important}.trace{stroke-dashoffset:0!important}\n'''
    return FONT_CSS+rules


def svg(h, content, title, bg=PAPER,defs=''):
    w=1000
    body=f'{R(1,1,998,h-2,bg,26,extra=f"stroke={chr(34)}{LINE if bg==PAPER else bg}{chr(34)} stroke-width={chr(34)}2{chr(34)}")}'
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}" role="img" aria-label="{esc(title)}">
<title>{esc(title)}</title>
<defs><clipPath id="bounds"><rect x="1" y="1" width="998" height="{h-2}" rx="26"/></clipPath>{defs}</defs>
<style><![CDATA[{style()}]]></style>
{body}<g clip-path="url(#bounds)">{content}</g></svg>'''


def header(index,category, color=INK):
    return T(56,49,f'{index} / {category}',14,color,'mono in',delay=.2)


def hero(portrait):
    h=409
    b=R(1,1,998,h-2,PAPER,26)
    # Editorial top nav, with precise alignment rather than noisy grid backgrounds.
    b+=T(55,52,'DG / CODE THEORY',16,INK,'mono in',delay=.08)
    b+=T(948,52,'DTU  ·  CSE 2028',14,MUTED,'mono in',anchor='end',delay=.12)
    b+=P('M54 70H948',LINE,1.3)
    b+=R(55,101,11,11,'#FF8863',3)
    b+=T(79,113,"HEY, I'M",15,INK,'mono in',delay=.23)
    b+=T(48,222,'Daksh',108,INK,'display in',delay=.36)
    b+=T(48,320,'Gangwar.',104,INK,'display in',delay=.50)
    # Lime highlighter creates a recognisable editorial motif.
    b+=R(56,334,115,5,LIME,2,extra='class="fade" style="--delay:.75s"')
    b+=T(57,376,TAGLINE,19,MUTED,'body in',delay=.66)
    # Inset panel: a compact diagram of building, improving and securing systems.
    x,y,w,k=672,92,276,286
    b+=R(x,y,w,k,DARK,22)
    for xx in range(x+18,x+w-10,26):
        b+=P(f'M{xx} {y+59}V{y+k-39}','#454B43',.6,extra='opacity=".20"')
    for yy in range(y+60,y+k-30,26):
        b+=P(f'M{x+13} {yy}H{x+w-13}','#454B43',.6,extra='opacity=".20"')
    b+=R(x+18,y+19,8,8,LIME,4)
    b+=R(x+31,y+19,8,8,PURPLE,4)
    b+=R(x+44,y+19,8,8,PEACH,4)
    b+=T(x+256,y+27,'001',11,STEEL,'mono',anchor='end')
    b+=P(f'M{x+25} {y+47}H{x+w-25}','#3F4541',1)
    # Orbiting / bridging diagram, not a stock "DG" avatar.
    b+=P('M738 208C768 150 819 157 847 199S899 262 916 206','#4C5850',1.7,extra='class="trace" style="--delay:.7s"')
    b+=P('M734 257C770 229 789 274 828 235S885 175 920 256','#62725A',1.4,extra='class="trace" style="--delay:1.1s"')
    for cx,cy,r,fill in [(748,208,13,LIME),(828,235,20,PURPLE),(903,204,11,PEACH)]:
        b+=f'<circle cx="{cx}" cy="{cy}" r="{r+8}" fill="none" stroke="{fill}" stroke-opacity=".28"/>'
        b+=f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="{fill}" class="fade" style="--delay:.9s"/>'
    b+=T(748,213,'01',10,INK,'mono',anchor='middle')
    b+=T(828,240,'02',11,INK,'mono',anchor='middle')
    b+=T(903,208,'03',9,INK,'mono',anchor='middle')
    b+=T(x+22,y+240,'BUILD  /  OPTIMISE  /  SECURE',12,WHITE,'mono in',delay=1.1)
    b+=P(f'M{x+24} {y+255}H{x+w-24}','#465048',1)
    b+=R(x+22,y+265,8,8,LIME,4,extra='class="cursor"')
    b+=T(x+39,y+274,'always building something',10,STEEL,'mono')
    if portrait:
        f=Path(portrait)
        if not f.is_file(): raise FileNotFoundError(f'PORTRAIT_FILE not found: {f}')
        mime=mimetypes.guess_type(f.name)[0]
        if mime not in {'image/jpeg','image/png','image/webp'}: raise ValueError('Portrait must be JPG, PNG or WEBP.')
        raw=base64.b64encode(f.read_bytes()).decode()
        # Optional circular portrait, embedded; preserve all panel styling around it.
        b+=f'<defs><clipPath id="portrait"><circle cx="827" cy="220" r="70"/></clipPath></defs>'
        b+=f'<circle cx="827" cy="220" r="75" fill="{LIME}"/>'
        b+=f'<image x="757" y="150" width="140" height="140" preserveAspectRatio="xMidYMid slice" clip-path="url(#portrait)" href="data:{mime};base64,{raw}"/>'
    # A tiny SMIL spark, disabled visually for accessibility.
    b+='<g class="smil"><circle cx="738" cy="208" r="3" fill="white"><animate attributeName="r" values="3;7;3" dur="2.2s" begin="1.4s" repeatCount="indefinite"/></circle></g>'
    b+='<g class="still"><circle cx="738" cy="208" r="3" fill="white"/></g>'
    return svg(h,b,NAME+' — engineering, AI & systems')


def icon_tile(i, color):
    x=267; y=52
    if i==0:
        return P(f'M{x-26} {y-13}L{x-42} {y+3}L{x-26} {y+19} M{x+8} {y-13}L{x+24} {y+3}L{x+8} {y+19}',color,3) + P(f'M{x-13} {y+22}L{x-2} {y-18}',color,3)
    if i==1:
        return (f'<circle cx="{x-14}" cy="{y-6}" r="12" fill="none" stroke="{color}" stroke-width="2.7"/>'
            + f'<circle cx="{x+15}" cy="{y+10}" r="12" fill="none" stroke="{color}" stroke-width="2.7"/>'
            + P(f'M{x-4} {y+3}L{x+5} {y+5}',color,2.7))
    return P(f'M{x-29} {y+18}L{x+28} {y-14}L{x+9} {y+27}L{x-2} {y+12}Z',color,2.8) + P(f'M{x-2} {y+12}L{x+28} {y-14}',color,2.4)


def tile(i):
    blocks=[('01','FIND ME ON','GitHub','Code, experiments & curiosity',LIME),
            ('02','LET’S CONNECT','LinkedIn','People, teams & experience',PURPLE),
            ('03','THE CONNECTION','Say hello','Have an idea? Let’s talk.',PEACH)]
    # Avoid typographic ligature unsupported by subset and keep titles unambiguous.
    num,kicker,title,desc,bg=blocks[i]
    h=193
    b=R(1,1,318,h-2,bg,23)
    b+=T(24,37,num,14,INK,'mono in',delay=.95+i*.15)
    b+=T(24,79,kicker,11,MUTED,'mono in',delay=1.00+i*.15)
    b+=T(24,126,title,38,INK,'display in',delay=1.08+i*.15)
    b+=T(24,156,desc.replace('Let’s',"Let's"),14,INK,'body in',delay=1.18+i*.15)
    b+=R(229,20,69,67,INK,18)
    b+=icon_tile(i,bg)
    b+=A(279,168,INK,.66,delay=1.4+i*.15)
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="320" height="193" viewBox="0 0 320 193" role="img" aria-label="{esc(title)}">
<title>{esc(title)}</title><style><![CDATA[{style()}]]></style>{b}</svg>'''


def valid_data(data):
    if not isinstance(data,dict) or not isinstance(data.get('days'),list):
        raise ValueError('Expected contribution JSON with a days array')
    days={}
    for row in data['days']:
        d=date.fromisoformat(row['date']); v=int(row['count'])
        if v<0: raise ValueError('Negative contributions are invalid')
        days[d]=v
    return days


def compute_stats(days):
    if not days:
        return {'days':{},'total':None,'active':None,'current':None,'longest':None,'busiest':None,'monthly':[]}
    latest=max(days)
    # Current streak falls back to yesterday if today has not yet had an event.
    d=latest if days.get(latest,0)>0 else latest-timedelta(days=1)
    current=0
    while days.get(d,0)>0:
        current+=1;d-=timedelta(days=1)
    longest=run=0
    for d in sorted(days):
        run=run+1 if days[d]>0 and days.get(d-timedelta(days=1),0)>0 else (1 if days[d]>0 else 0)
        longest=max(longest,run)
    counts=defaultdict(int)
    for d,c in days.items(): counts[(d.year,d.month)]+=c
    monthly=[]
    for k in range(11,-1,-1):
        integer=latest.year*12+latest.month-1-k
        yr,month=divmod(integer,12); month+=1
        monthly.append((calendar.month_abbr[month],counts[(yr,month)],yr,month))
    busiest=max(days, key=lambda d:(days[d],-d.toordinal()))
    return {'days':days,'total':sum(days.values()),'active':sum(x>0 for x in days.values()),
            'current':current,'longest':longest,
            'busiest':(busiest,days[busiest]) if days[busiest]>0 else None,
            'monthly':monthly}


def activity(st, demo):
    h=398
    b=header('03','ACTIVITY / LAST 12 MONTHS',LIME)
    b+=T(55,112,'Code, consistently.',55,WHITE,'display in',delay=3.05)
    b+=T(941,58,'SAMPLE DATA' if demo else 'REAL GITHUB DATA' if st['total'] is not None else 'PENDING SYNC',12,LIME,'mono',anchor='end')
    b+=P('M56 138H944','#3D4644',1)
    if st['total'] is None:
        b+=T(55,234,'Waiting on your first contribution sync.',30,WHITE,'display in',delay=3.1)
        b+=T(55,270,'Run the GitHub Action once to populate your real activity.',17,STEEL,'body in',delay=3.2)
        b+=P('M56 308H944','#3D4644',1)
        b+=T(56,362,'No placeholder numbers. Ever.',20,LIME,'body')
        return svg(h,b,'Monthly GitHub activity awaiting initial sync',DARK)
    maximum=max(1,max(v for _,v,_,_ in st['monthly']))
    for k in range(4):
        yy=169+k*30
        b+=P(f'M57 {yy}H944','#323B3A',1,extra='stroke-dasharray="4 8"')
    # 12 rounded animated columns; all x values comfortably inside 1000px.
    for i,(month,val,yr,m) in enumerate(st['monthly']):
        x=66+i*74
        ht=8 if not val else max(8,round(val/maximum*112))
        yy=284-ht
        is_peak=val==maximum and val>0
        col=LIME if is_peak else '#5F736B'
        b+=R(x,yy,43,ht,col,9,extra=f'class="grow" style="--delay:{3.35+i*.07:.2f}s"')
        b+=T(x+21,309,month.upper(),11,STEEL,'mono',anchor='middle')
        if is_peak:
            b+=T(x+21,yy-11,str(val),14,LIME,'mono fade',anchor='middle',delay=3.40+i*.07)
    b+=P('M56 326H944','#3D4644',1)
    busy=st['busiest']
    figures=[(56,str(st['current'])+'d','CURRENT STREAK'),(278,str(st['active']),'ACTIVE DAYS'),
             (510,str(st['longest'])+'d','LONGEST STREAK'),(741,busy[0].strftime('%d %b').title() if busy else '—','BUSIEST DAY')]
    for i,(x,val,key) in enumerate(figures):
        b+=T(x,370,val,36,WHITE,'display in',delay=4.14+i*.09)
        # Four metrics need a second label baseline, not crammed next to numbers.
    for i,(x,val,key) in enumerate(figures):
        b+=T(x,390,key,10,STEEL,'mono in',delay=4.17+i*.09)
    return svg(h,b,'Monthly activity with current streak, active days, longest streak and busiest day',DARK)


def focus():
    """A single non-project interests card, with a typographic systems aesthetic."""
    h=338
    b=header('02','THE THINGS I GRAVITATE TOWARD',MUTED)
    b+=T(53,109,'Curiosity, in three directions.',46,INK,'display in',delay=1.78)
    b+=T(55,135,'I like understanding how things work, and then trying to build them.',16,MUTED,'body in',delay=1.90)
    cards=[
        ('BACKEND ENGINEERING','Fast APIs. Better queries.','C++ / PYTHON / SQL',SOFTGREEN,LIME),
        ('AI & MACHINE LEARNING','Models with real-world uses.','PYTORCH / OPENCV / RAG',SOFTPURPLE,PURPLE),
        ('SYSTEMS & SECURITY','What happens under the hood.','LINUX / REDIS / DOCKER',SOFTPEACH,PEACH),
    ]
    for i,(title,description,tools,bg,accent) in enumerate(cards):
        x=55+i*302
        delay=2.02+i*.15
        b+=R(x,156,284,158,bg,18,extra=f'class="fade" style="--delay:{delay:.2f}s"')
        b+=R(x+17,174,31,28,DARK,9)
        if i==0:
            b+=P(f'M{x+26} 182l-6 6 6 6 M{x+39} 182l6 6 -6 6',accent,2)
            b+=P(f'M{x+35} 180l-5 16',accent,1.6)
        elif i==1:
            for xx,yy in [(x+24,188),(x+40,181),(x+41,196)]:
                b+=f'<circle cx="{xx}" cy="{yy}" r="3.4" fill="{accent}"/>'
            b+=P(f'M{x+24} 188L{x+40} 181L{x+41} 196L{x+24} 188',accent,1.3)
        else:
            b+=P(f'M{x+22} 184l6 5 -6 5 M{x+32} 194h9',accent,1.8)
        b+=T(x+58,193,'0'+str(i+1),11,INK,'mono in',delay=delay+.05)
        b+=P(f'M{x+17} 214H{x+266}',INK,.8,extra='stroke-opacity=".16"')
        b+=T(x+17,239,title,16,INK,'body in',delay=delay+.11)
        b+=T(x+17,267,description,13,MUTED,'body in',delay=delay+.17)
        b+=T(x+17,294,tools,10,INK,'mono in',delay=delay+.20)
    return svg(h,b,'Engineering interests: backend, AI and systems')


def contribution_grid(st,demo):
    h=325
    b=header('04','CONTRIBUTION MAP',INK)
    b+=T(51,106,'The green squares.',54,INK,'display in',delay=5.15)
    if st['total'] is None:
        b+=T(943,90,'—',61,INK,'display',anchor='end')
        b+=T(940,110,'AWAITING SYNC',11,MUTED,'mono',anchor='end')
        b+=T(55,201,'Your contribution graph appears after the first Action run.',20,MUTED,'body')
        return svg(h,b,'Contribution calendar awaiting first GitHub refresh')
    b+=T(939,92,f'{st["total"]:,}',64,INK,'display in',anchor='end',delay=5.35)
    b+=T(938,111,'CONTRIBUTIONS / 365 DAYS',11,MUTED,'mono',anchor='end')
    vals=st['days']; latest=max(vals)
    start=latest-timedelta(days=364)
    aligned=start-timedelta(days=(start.weekday()+1)%7)
    x0,y0,stepx,stepy=68,151,16.2,18.0
    for j,n in enumerate(['SUN','MON','TUE','WED','THU','FRI','SAT']):
        if j in (1,3,5): b+=T(24,y0+j*stepy+10,n[0],10,MUTED,'mono')
    maxn=max(vals.values(),default=0)
    for k in range((latest-aligned).days+1):
        d=aligned+timedelta(days=k)
        if d<start:continue
        col=k//7;row=(d.weekday()+1)%7
        c=vals.get(d,0)
        if c<=0: color='#E4E6DA'
        else:
            v=(c/maxn)**.55 if maxn else 0
            color='#BEDB87' if v<.33 else '#9BBD55' if v<.62 else '#6C9540' if v<.84 else '#254C37'
        b+=R(round(x0+col*stepx,2),round(y0+row*stepy,2),12,12,color,3,
             extra=f'class="cell" style="--delay:{5.50+col*.017+row*.012:.2f}s"')
    for back in range(12,-1,-1):
        number=latest.year*12+latest.month-1-back
        yr,mm=divmod(number,12);mm+=1
        d=date(yr,mm,1)
        if start<=d<=latest:
            week=(d-aligned).days//7
            if 0<=week<=53:b+=T(round(x0+week*stepx,2),140,calendar.month_abbr[mm].upper(),10,MUTED,'mono')
    b+=T(57,299,'LESS',11,MUTED,'mono')
    for i,c in enumerate(['#E4E6DA','#BEDB87','#9BBD55','#6C9540','#254C37']):
        b+=R(106+i*20,287,13,13,c,3)
    b+=T(223,299,'MORE',11,MUTED,'mono')
    b+=T(944,299,'SAMPLE DATA  /  PREVIEW ONLY' if demo else 'UPDATED DAILY VIA GITHUB ACTIONS',11,MUTED,'mono',anchor='end')
    return svg(h,b,'Github contributions calendar, lime green activity',PAPER)

def fetch_contributions(target):
    token=os.getenv('STATS_TOKEN') or os.getenv('GH_TOKEN') or os.getenv('GITHUB_TOKEN')
    if not token:
        raise RuntimeError('--refresh requires STATS_TOKEN or GITHUB_TOKEN. This script does not make up activity.')
    now=datetime.now(timezone.utc).date()
    since=now-timedelta(days=364)
    query='''query($username:String!,$from:DateTime!,$to:DateTime!){
      user(login:$username){contributionsCollection(from:$from,to:$to){
        contributionCalendar{totalContributions weeks{contributionDays{date contributionCount}}}
      }} }'''

    # GitHub can impose a GraphQL resource limit on full-year calendars.
    # Small (up to 100-day) nonoverlapping windows keep the query lightweight.
    rows={}
    part_start=since
    while part_start<=now:
        part_end=min(part_start+timedelta(days=99),now)
        payload=json.dumps({'query':query,'variables':{'username':USER,
             'from': part_start.isoformat()+'T00:00:00Z',
             'to': part_end.isoformat()+'T23:59:59Z'}}).encode('utf-8')
        req=urllib.request.Request('https://api.github.com/graphql',data=payload,
            headers={'Authorization':'Bearer '+token, 'User-Agent':'Code-Theory-README-svg-cards',
                     'Content-Type':'application/json','Accept':'application/vnd.github+json'},method='POST')
        try:
            with urllib.request.urlopen(req,timeout=30) as response:
                obj=json.load(response)
        except urllib.error.HTTPError as exc:
            raise RuntimeError(f'GitHub GraphQL returned HTTP {exc.code}: {exc.read().decode(errors="replace")[:350]}') from exc
        if obj.get('errors'):
            raise RuntimeError('GitHub GraphQL errors: '+json.dumps(obj['errors'])[:600])
        user=(obj.get('data') or {}).get('user')
        if not user: raise RuntimeError('GitHub user not found in GraphQL response')
        calendar_data=user['contributionsCollection']['contributionCalendar']
        part_rows={d['date']:int(d['contributionCount'])
                   for week in calendar_data['weeks'] for d in week['contributionDays']
                   if part_start<=date.fromisoformat(d['date'])<=part_end}
        if sum(part_rows.values())!=int(calendar_data['totalContributions']):
            raise RuntimeError('GraphQL total/day mismatch for '+part_start.isoformat())
        rows.update(part_rows)
        part_start=part_end+timedelta(days=1)

    filtered=[{'date':d.isoformat(),'count':int(rows.get(d.isoformat(),0))}
              for d in (since+timedelta(days=k) for k in range(365))]
    fresh={'user':USER,'updated_utc':datetime.now(timezone.utc).isoformat(timespec='seconds'),
           'period_start':since.isoformat(),'period_end':now.isoformat(),
           'source':'GitHub GraphQL contributionsCollection.contributionCalendar',
           'days':filtered}
    # Validate before overwriting the last known-good snapshot.
    valid_data(fresh)
    target.parent.mkdir(parents=True,exist_ok=True)
    target.write_text(json.dumps(fresh,indent=2)+'\n',encoding='utf-8')
    print(f'Refreshed {target} with {sum(x["count"] for x in filtered)} real public contributions')




def render(data_file,out_dir,portrait_file):
    global FONT_CSS
    FONT_CSS=fonts_css()
    data=json.loads(data_file.read_text(encoding='utf-8'))
    stats=compute_stats(valid_data(data))
    demo=bool(data.get('demo'))
    out_dir.mkdir(parents=True,exist_ok=True)
    cards={
        'hero.svg':hero(portrait_file),
         'github.svg':tile(0),
        'linkedin.svg':tile(1),
        'email.svg':tile(2),
        'focus.svg':focus(),
        'activity.svg':activity(stats,demo),
        'contributions.svg':contribution_grid(stats,demo),
    }
    for filename,markup in cards.items():
        path=out_dir/filename
        path.write_text(markup,encoding='utf-8')
        print(f'{filename}: {path.stat().st_size//1024} KiB')
    print('Mode:', 'static final-frame' if STATIC else 'animated', '|', 'SAMPLE DATA' if demo else 'real data' if stats['total'] is not None else 'pending first sync')


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--refresh',action='store_true',help='Refresh GitHub contribution JSON using GITHUB_TOKEN or STATS_TOKEN')
    parser.add_argument('--refresh-only',action='store_true',help='Fetch only; do not render SVG cards')
    parser.add_argument('--data',type=Path,default=ROOT/'data'/'contributions.json')
    parser.add_argument('--out',type=Path,default=ROOT/'cards')
    args=parser.parse_args()
    if args.refresh:fetch_contributions(args.data)
    if not args.refresh_only:render(args.data,args.out,os.environ.get('PORTRAIT_FILE') or None)

if __name__=='__main__':main()
