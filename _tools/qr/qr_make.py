# 작은 QR 만들기(바이트 꼴 · 오류 고침 M · 판 자동) · 외부 라이브러리 없음
import sys
ECC_M=[-1,10,16,26,18,24,16,18,22,22,26,30,22,22,24,24,28,28,26,26,26]
BLK_M=[-1,1,1,1,2,2,4,4,4,5,5,5,8,9,9,10,10,11,13,14,16]
def raw_modules(v):
    r=(16*v+128)*v+64
    if v>=2:
        n=v//7+2; r-=(25*n-10)*n-55
        if v>=7: r-=36
    return r
def data_cw(v): return raw_modules(v)//8-ECC_M[v]*BLK_M[v]
def gmul(x,y):
    z=0
    for i in range(7,-1,-1):
        z=(z<<1)^((z>>7)*0x11D); z^=((y>>i)&1)*x
    return z&0xFF
def rs_div(deg):
    r=[0]*(deg-1)+[1]; root=1
    for _ in range(deg):
        for j in range(len(r)):
            r[j]=gmul(r[j],root)
            if j+1<len(r): r[j]^=r[j+1]
        root=gmul(root,2)
    return r
def rs_rem(data,div):
    r=[0]*len(div)
    for b in data:
        f=b^r.pop(0); r.append(0)
        for i,c in enumerate(div): r[i]^=gmul(c,f)
    return r
def align_pos(v):
    if v==1: return []
    n=v//7+2; size=v*4+17
    step=(v*8+n*3+5)//(n*4-4)*2
    return [6]+sorted(size-7-i*step for i in range(n-1))
def encode(text):
    b=text.encode('utf-8')
    for v in range(1,21):
        cap=data_cw(v)*8; ccbits=8 if v<10 else 16
        if 4+ccbits+len(b)*8<=cap: break
    bits=[]
    def put(val,n): bits.extend((val>>i)&1 for i in range(n-1,-1,-1))
    put(4,4); put(len(b),ccbits)
    for x in b: put(x,8)
    put(0,min(4,cap-len(bits)))
    put(0,(-len(bits))%8)
    pad=0xEC
    while len(bits)<cap: put(pad,8); pad^=0xEC^0x11
    data=[int(''.join(map(str,bits[i:i+8])),2) for i in range(0,len(bits),8)]
    nb=BLK_M[v]; ecl=ECC_M[v]; raw=raw_modules(v)//8
    nshort=nb-raw%nb; slen=raw//nb
    div=rs_div(ecl); blocks=[]; k=0
    for i in range(nb):
        dat=data[k:k+slen-ecl+(0 if i<nshort else 1)]; k+=len(dat)
        e=rs_rem(dat,div)
        if i<nshort: dat=dat+[0]
        blocks.append(dat+e)
    cw=[]
    for i in range(len(blocks[0])):
        for j,bl in enumerate(blocks):
            if i!=slen-ecl or j>=nshort: cw.append(bl[i])
    assert len(cw)==raw
    size=v*4+17
    M=[[False]*size for _ in range(size)]; F=[[False]*size for _ in range(size)]
    def s(x,y,d): M[y][x]=d; F[y][x]=True
    for i in range(size): s(6,i,i%2==0); s(i,6,i%2==0)
    for cx,cy in ((3,3),(size-4,3),(3,size-4)):
        for dy in range(-4,5):
            for dx in range(-4,5):
                xx,yy=cx+dx,cy+dy
                if 0<=xx<size and 0<=yy<size: s(xx,yy,max(abs(dx),abs(dy)) not in (2,4))
    ap=align_pos(v); n=len(ap)
    for i in range(n):
        for j in range(n):
            if (i==0 and j==0) or (i==0 and j==n-1) or (i==n-1 and j==0): continue
            for dy in range(-2,3):
                for dx in range(-2,3): s(ap[i]+dx,ap[j]+dy,max(abs(dx),abs(dy))!=1)
    def fmt(mask):
        d=(0<<3)|mask; r=d   # M = 0
        for _ in range(10): r=(r<<1)^((r>>9)*0x537)
        bb=((d<<10)|r)^0x5412
        g=lambda i:(bb>>i)&1==1
        for i in range(6): s(8,i,g(i))
        s(8,7,g(6)); s(8,8,g(7)); s(7,8,g(8))
        for i in range(9,15): s(14-i,8,g(i))
        for i in range(8): s(size-1-i,8,g(i))
        for i in range(8,15): s(8,size-15+i,g(i))
        s(8,size-8,True)
    fmt(0)
    if v>=7:
        r=v
        for _ in range(12): r=(r<<1)^((r>>11)*0x1F25)
        bb=(v<<12)|r
        for i in range(18):
            bt=(bb>>i)&1==1; a=size-11+i%3; c=i//3
            s(a,c,bt); s(c,a,bt)
    i=0; right=size-1
    while right>=1:
        if right==6: right=5
        for vert in range(size):
            for j in range(2):
                x=right-j; up=((right+1)&2)==0
                y=size-1-vert if up else vert
                if not F[y][x] and i<len(cw)*8:
                    M[y][x]=(cw[i>>3]>>(7-(i&7)))&1==1; i+=1
        right-=2
    assert i==len(cw)*8
    MASKS=[lambda x,y:(x+y)%2==0,lambda x,y:y%2==0,lambda x,y:x%3==0,lambda x,y:(x+y)%3==0,
           lambda x,y:(x//3+y//2)%2==0,lambda x,y:x*y%2+x*y%3==0,lambda x,y:(x*y%2+x*y%3)%2==0,
           lambda x,y:((x+y)%2+x*y%3)%2==0]
    def apply(m):
        for y in range(size):
            for x in range(size):
                if not F[y][x] and MASKS[m](x,y): M[y][x]=not M[y][x]
    def penalty():
        p=0
        lines=[row[:] for row in M]+[[M[y][x] for y in range(size)] for x in range(size)]
        pat1=[True,False,True,True,True,False,True,False,False,False,False]
        pat2=pat1[::-1]
        for ln in lines:
            run=1
            for k2 in range(1,size+1):
                if k2<size and ln[k2]==ln[k2-1]: run+=1
                else:
                    if run>=5: p+=3+run-5
                    run=1
            ext=[False]*4+ln+[False]*4
            for k2 in range(len(ext)-10):
                seg=ext[k2:k2+11]
                if seg==pat1 or seg==pat2: p+=40
        for y in range(size-1):
            for x in range(size-1):
                c=M[y][x]
                if c==M[y][x+1]==M[y+1][x]==M[y+1][x+1]: p+=3
        dark=sum(map(sum,M)); tot=size*size
        kk=(abs(dark*20-tot*10)+tot-1)//tot-1
        p+=kk*10
        return p
    best=None
    for m in range(8):
        apply(m); fmt(m); pe=penalty()
        if best is None or pe<best[0]: best=(pe,m)
        apply(m)
    apply(best[1]); fmt(best[1])
    return v,best[1],M
def svg(M,quiet=4):
    n=len(M); tot=n+2*quiet; d=[]
    for y in range(n):
        x=0
        while x<n:
            if M[y][x]:
                x0=x
                while x<n and M[y][x]: x+=1
                d.append(f"M{x0+quiet},{y+quiet}h{x-x0}v1h-{x-x0}z")
            else: x+=1
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {tot} {tot}" width="{tot*6}" height="{tot*6}" shape-rendering="crispEdges">'
            f'<rect width="{tot}" height="{tot}" fill="#FFFFFF"/><path fill="#000000" d="{"".join(d)}"/></svg>\n')
if __name__=="__main__":
    text=sys.argv[1]; out=sys.argv[2]
    v,m,M=encode(text)
    open(out,'w',encoding='utf-8',newline='\n').write(svg(M))
    import json; json.dump({"text":text,"version":v,"mask":m,"matrix":[''.join('1' if c else '0' for c in r) for r in M]},open(out+'.json','w'))
    print("version",v,"mask",m,"size",len(M),"bytes",len(text.encode()))
