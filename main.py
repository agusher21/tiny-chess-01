import os,json,urllib.request
W,B=0,1;P=[0,100,320,330,500,900]
def sq(f,r):return r*8+f
def rk(s):return s//8
def on(f,r):return 0<=f<8 and 0<=r<8
def init():
 b=[0]*64
 for i in range(8):b[sq(i,1)]=1;b[sq(i,6)]=5
 for f,p in [(0,2),(1,3),(2,4),(3,5),(4,4),(5,3),(6,2),(7,2)]:b[sq(f,0)]=p;b[sq(f,7)]=p+6
 return {'b':b,'t':W,'c':15,'e':-1,'h':0,'m':1}
def cp(b):return {'b':list(b['b']),'t':b['t'],'c':b['c'],'e':b['e'],'h':b['h'],'m':b['m']}
def gen(b):
 ms=[];t=b['t'];o=B if t==W else W;q0=0 if t==W else 6
 for i in range(64):
  p=b['b'][i]
  if p==0 or p%6!=q0:continue
  r,f=i//8,i%8;pt=p//6
  if pt==0:
   dr=1 if t==W else -1;n=r+dr
   if on(f,nr) and b['b'][sq(f,nr)]==0:
    ms.append((i,sq(f,nr)))
    if (r==1 and t==W) or (r==6 and t==B) and b['b'][sq(f,n+dr)]==0:ms.append((i,sq(f,n+dr)))
   for df in (-1,1):
    nf=f+df
    if on(nf,n):
     q=b['b'][sq(nf,n)]
     if q and q%6!=o:ms.append((i,sq(nf,n)))
     elif b['e']==sq(nf,n):ms.append((i,sq(nf,n)))
  elif pt==1:
   for df,dr in ((1,2),(2,1),(2,-1),(1,-2),(-1,-2),(-2,-1),(-2,1),(-1,2)):
    nf,nr=f+df,r+dr
    if on(nf,nr):
     q=b['b'][sq(nr,nf)]
     if q==0 or q%6!=o:ms.append((i,sq(nr,nf)))
  elif pt==2:
   for df,dr in ((1,1),(1,-1),(-1,1),(-1,-1)):
    for d in range(1,8):
     nf,nr=f+d*df,r+d*dr
     if not on(nf,nr):break
     q=b['b'][sq(nr,nf)]
     if q==0:ms.append((i,sq(nr,nf)))
     else:
      if q%6!=o:ms.append((i,sq(nr,nf)))
      break
  elif pt==3:
   for df,dr in ((1,0),(-1,0),(0,1),(0,-1)):
    for d in range(1,8):
     nf,nr=f+d*df,r+d*dr
     if not on(nf,nr):break
     q=b['b'][sq(nr,nf)]
     if q==0:ms.append((i,sq(nr,nf)))
     else:
      if q%6!=o:ms.append((i,sq(nr,nf)))
      break
  elif pt==4:
   for df,dr in ((1,1),(1,-1),(-1,1),(-1,-1)):
    for d in range(1,8):
     nf,nr=f+d*df,r+d*dr
     if not on(nf,nr):break
     q=b['b'][sq(nr,nf)]
     if q==0:ms.append((i,sq(nr,nf)))
     else:
      if q%6!=o:ms.append((i,sq(nr,nf)))
      break
  elif pt==5:
   for df in (-1,0,1):
    for dr in (-1,0,1):
     if df==dr==0:continue
     nf,nr=f+df,r+dr
     if on(nf,nr):
      q=b['b'][sq(nr,nf)]
      if q==0 or q%6!=o:ms.append((i,sq(nr,nf)))
 return ms
def mv(b,f,t):
 b=cp(b);p=b['b'][f];b['b'][f]=0;b['b'][t]=p;b['t']=B if b['t']==W else W
 b['h']=b['h']+1 if p//6 in (0,5) else 0
 if p//6==0 and abs(rk(t)-rk(f))==2:
  if t>f:b['b'][7+rk(t)]=0;b['b'][5+rk(t)]=3
  else:b['b'][rk(t)]=0;b['b'][3+rk(t)]=3
 b['m']+=1
 return b
def ev(b):
 s=0
 for i in range(64):
  p=b['b'][i]
  if p:s+=P[p//6] if p%6==W else -P[p//6]
 return s if b['t']==W else -s
tt={}
def ab(b,d,a,c):
 if d==0:return q(b,a,c)
 ms=gen(b)
 if not ms:return -90000
 b=-99999
 for f,t in ms:
  v=-ab(mv(b,f,t),d-1,-c,-a)
  if v>b:b=v
  if v>a:a=v
  if a>=c:break
 return b
def q(b,a,c):
 s=ev(b)
 if s>=c:return c
 if s>a:a=s
 for f,t in [m for m in gen(b) if b['b'][m[1]]]:
  v=-q(mv(b,f,t),-c,-a)
  if v>=c:return c
  if v>a:a=v
 return a
def post(u,p):
 d=json.dumps(p).encode()
 req=urllib.request.Request(u,data=d,headers={'Content-Type':'application/json'})
 try:
  with urllib.request.urlopen(req,timeout=8) as r:return json.loads(r.read())
 except:return {'status':'error'}
def main():
 eu=os.environ.get('MAKEFUN_ENV_URL','')
 g=post(eu+'/game',{})
 while g.get('status')!='done':
  gm=g.get('game');lm=g.get('legal_moves',[])
  if not lm:break
  bs=None;bv=-99999
  for m in lm:
   v=-ab(mv(g,m[0],m[1]),2,-99999,99999)
   if v>bv:bv=v;bs=m
  if bs is None:bs=lm[0]
  g=post(eu+'/move',{'game':gm,'move':bs})
  if g.get('status')=='over':break
 post(eu+'/game',{})
main()
