from __future__ import annotations
import hashlib, json, os, socket, sys, time, urllib.error, urllib.parse, urllib.request
from datetime import datetime, timezone
from pathlib import Path

TAIL=[
('2026-05-09','ST',11),('2026-05-13','HV',9),('2026-05-17','ST',11),('2026-05-20','HV',9),('2026-05-24','ST',11),('2026-05-27','HV',9),('2026-05-31','ST',11),('2026-06-03','HV',9),('2026-06-07','ST',11),('2026-06-10','HV',9),('2026-06-13','ST',11),('2026-06-21','ST',11),('2026-06-24','HV',9),('2026-06-27','ST',11),('2026-07-01','ST',11),('2026-07-04','ST',11),('2026-07-08','HV',9),('2026-07-12','ST',11),('2026-07-15','HV',9)]
ALLOWED={
 'racing.hkjc.com':('/en-us/local/information/resultsall','/en-us/local/information/archive/resultsall','/en-us/local/information/localresults','/en-us/local/information/archive/localresults','/en-us/local/information/racecard','/en-us/local/information/formline','/en-us/local/information/racereportext','/en-us/local/information/veterinaryrecord','/en-us/local/information/exceptionalfactors','/en-us/local/information/localtrackwork','/en-us/local/information/entries','/en-us/local/info/changes','/en-us/local/info/windtracker'),
 'bet.hkjc.com':('/en/racing/wp/',), 'info.cld.hkjc.com':('/graphql/base/',)}
OUT=Path('r6_evidence'); RAW=OUT/'raw'; OUT.mkdir(exist_ok=True); RAW.mkdir(exist_ok=True)

def now(): return datetime.now(timezone.utc).isoformat()
def sha(b): return hashlib.sha256(b).hexdigest()
def valid(url):
 p=urllib.parse.urlparse(url)
 if p.scheme!='https' or p.username or p.password or p.fragment: raise RuntimeError('BAD_URL:'+url)
 if p.hostname not in ALLOWED or not any(p.path.startswith(x) for x in ALLOWED[p.hostname]): raise RuntimeError('URL_NOT_ALLOWED:'+url)
 return p
class NoRedirect(urllib.request.HTTPRedirectHandler):
 def redirect_request(self,*a,**k): return None
opener=urllib.request.build_opener(NoRedirect)

def get(url, headers, max_redirects=5):
 chain=[]
 for _ in range(max_redirects+1):
  valid(url); req=urllib.request.Request(url,headers=headers,method='GET')
  try: r=opener.open(req,timeout=30); return url,r.status,dict(r.headers),r.read(),chain
  except urllib.error.HTTPError as e:
   if e.code in (301,302,303,307,308):
    loc=e.headers.get('Location')
    if not loc: raise
    nxt=urllib.parse.urljoin(url,loc); valid(nxt); chain.append({'from':url,'status':e.code,'to':nxt}); url=nxt; continue
   raise
 raise RuntimeError('TOO_MANY_REDIRECTS')

def write_record(sid,stype,url,body,status,headers,final_url,chain,ledger):
 fn=RAW/(sid+'.bin'); fn.write_bytes(body)
 rec={'source_id':sid,'source_type':stype,'request_url':url,'final_url':final_url,'http_status':status,'content_type':headers.get('Content-Type'),'captured_at_utc':now(),'bytes':len(body),'sha256':sha(body),'raw_file':str(fn),'redirect_chain':chain}
 ledger.write(json.dumps(rec,sort_keys=True)+'\n'); ledger.flush(); return rec

def qurl(path,params): return 'https://racing.hkjc.com'+path+'?'+urllib.parse.urlencode(params)
def tail_targets():
 out=[]
 for date,course,nr in TAIL:
  p={'Racecourse':course,'racedate':date.replace('-','/')}
  out.append((f'tail_{date}_{course}_resultsall','RESULTS_ALL',qurl('/en-us/local/information/resultsall',p)))
  for n in range(1,nr+1):
   q={**p,'RaceNo':n}; out.append((f'tail_{date}_{course}_r{n}_results','RESULTS',qurl('/en-us/local/information/localresults',q)))
 return out

def opening_targets():
 d='2026-09-06'; c='ST'; out=[]
 pages=[('racecard','RACECARD','/en-us/local/information/racecard'),('formline','FORMLINE','/en-us/local/information/formline'),('past_incidents','PAST_INCIDENTS','/en-us/local/information/racereportext'),('vet','VET_RACECARD','/en-us/local/information/veterinaryrecord'),('exceptional','EXCEPTIONAL','/en-us/local/information/exceptionalfactors'),('trackwork','TRACKWORK','/en-us/local/information/localtrackwork')]
 for n in range(1,11):
  p={'RaceNo':n,'Racecourse':c,'racedate':d.replace('-','/')}
  for suffix,stype,path in pages: out.append((f'opening_{d}_{c}_r{n}_{suffix}',stype,qurl(path,p)))
 out += [(f'opening_{d}_{c}_entries','ENTRIES',qurl('/en-us/local/information/entries',{'Racecourse':c,'View':'All','racedate':d.replace('-','/')})),(f'opening_{d}_{c}_changes','CHANGES','https://racing.hkjc.com/en-us/local/info/changes'),(f'opening_{d}_{c}_weather_track','WEATHER_TRACK','https://racing.hkjc.com/en-us/local/info/windtracker'),(f'opening_{d}_{c}_odds_ui_reference','ODDS_UI','https://bet.hkjc.com/en/racing/wp/')]
 return out

def preflight():
 rows=[]
 for h in ('racing.hkjc.com','info.cld.hkjc.com','bet.hkjc.com'):
  try: ips=sorted({x[4][0] for x in socket.getaddrinfo(h,443,type=socket.SOCK_STREAM)}); rows.append({'host':h,'status':'PASS','ips':ips})
  except Exception as e: rows.append({'host':h,'status':'BLOCKED','error':type(e).__name__+':'+str(e)})
 obj={'schema':'hkjc-r6-network-preflight-v1','created_at_utc':now(),'status':'PASS' if all(x['status']=='PASS' for x in rows) else 'BLOCKED','hosts':rows}; (OUT/'network_preflight.json').write_text(json.dumps(obj,indent=2,sort_keys=True)+'\n'); return obj

def require_gate():
 email=os.getenv('HKJC_CONTACT_EMAIL','').strip(); confirmed=os.getenv('HKJC_COMPLIANCE_CONFIRMED_AT','').strip()
 if not email or '@' not in email: raise RuntimeError('HKJC_CONTACT_EMAIL_MISSING')
 if not confirmed: raise RuntimeError('HKJC_COMPLIANCE_CONFIRMED_AT_MISSING')
 return {'email':email,'confirmed_at':confirmed}

def graphql(headers,ledger):
 url='https://info.cld.hkjc.com/graphql/base/'; valid(url)
 query='query racing($date: String, $venueCode: String, $oddsTypes: [OddsType], $raceNo: Int) { raceMeetings(date: $date, venueCode: $venueCode) { pmPools(oddsTypes: $oddsTypes, raceNo: $raceNo) { id status sellStatus oddsType lastUpdateTime leg { number races } oddsNodes { combString oddsValue hotFavourite oddsDropValue } } } }'
 payload=json.dumps({'operationName':'racing','query':query,'variables':{'date':'2026-09-06','venueCode':'ST','oddsTypes':['WIN','PLA'],'raceNo':1}},separators=(',',':')).encode()
 req=urllib.request.Request(url,data=payload,headers={**headers,'Content-Type':'application/json'},method='POST')
 try: r=urllib.request.urlopen(req,timeout=30); body=r.read(); status=r.status; hs=dict(r.headers)
 except urllib.error.HTTPError as e: body=e.read(); status=e.code; hs=dict(e.headers)
 fn=RAW/'opening_2026-09-06_ST_r1_graphql_probe.bin'; fn.write_bytes(body)
 rec={'source_id':'opening_2026-09-06_ST_r1_graphql_probe','source_type':'ODDS_GRAPHQL','request_url':url,'http_status':status,'content_type':hs.get('Content-Type'),'captured_at_utc':now(),'bytes':len(body),'sha256':sha(body),'raw_file':str(fn),'request_sha256':sha(payload)}; ledger.write(json.dumps(rec,sort_keys=True)+'\n'); ledger.flush(); return rec

def main():
 pf=preflight(); print(json.dumps(pf,indent=2))
 if pf['status']!='PASS': return 2
 try: gate=require_gate()
 except Exception as e:
  (OUT/'gate_status.json').write_text(json.dumps({'status':'BLOCKED_BEFORE_HTTP_CAPTURE','reason':str(e),'created_at_utc':now()},indent=2)+'\n'); print('BLOCKED',e); return 3
 headers={'User-Agent':'HKJC-Quant-R6/1.0 contact='+gate['email'],'Accept':'text/html,application/xhtml+xml,application/json;q=0.9,*/*;q=0.8'}
 records=[]
 with (OUT/'capture_ledger.jsonl').open('w',encoding='utf-8') as ledger:
  for sid,stype,url in tail_targets()+opening_targets():
   final,status,hs,body,chain=get(url,headers); records.append(write_record(sid,stype,url,body,status,hs,final,chain,ledger)); time.sleep(0.35)
  records.append(graphql(headers,ledger))
 manifest={'schema':'hkjc-r6-network-capture-manifest-v1','created_at_utc':now(),'tail_target_count':len(tail_targets()),'opening_target_count':len(opening_targets()),'graphql_target_count':1,'record_count':len(records),'records_sha256':sha(('\n'.join(json.dumps(x,sort_keys=True) for x in records)+'\n').encode())}
 (OUT/'capture_manifest.json').write_text(json.dumps(manifest,indent=2,sort_keys=True)+'\n'); print(json.dumps(manifest,indent=2)); return 0
if __name__=='__main__': raise SystemExit(main())
