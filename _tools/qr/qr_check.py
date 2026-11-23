# 따로 짠 읽기 검사(만든 도구의 함수는 쓰지 않음)
import json,sys
d=json.load(open(sys.argv[1])); M=[[c=='1' for c in r] for r in d['matrix']]; n=len(M); v=(n-17)//4
# 1) 형식 정보 읽기(왼쪽 위 사본) → 알려진 M 표와 맞대기
bits=[M[i][8] for i in range(6)]+[M[7][8],M[8][8],M[8][7]]+[M[8][14-i] for i in range(9,15)]
fv=sum(b<<i for i,b in enumerate(bits))
KNOWN_M={0:'101010000010010',1:'101000100100101',2:'101111001111100',3:'101101101001011',
         4:'100010111111001',5:'100000011001110',6:'100111110010111',7:'100101010100000'}
fs=format(fv,'015b'); mask=[k for k,s in KNOWN_M.items() if s==fs]
print('format',fs,'mask',mask)
# 두 번째 사본
bits2=[M[8][n-1-i] for i in range(8)]+[M[n-15+i][8] for i in range(8,15)]
print('format copy same',sum(b<<i for i,b in enumerate(bits2))==fv)
# 2) 판 정보(v>=7) → 알려진 값
if v>=7:
    vb=0
    for i in range(18): vb|=M[i//3][n-11+i%3]<<i
    print('version info',hex(vb),'known v8 0x85bc ok' if (v==8 and vb==0x85BC) else '')
mask=mask[0]
# 3) 기능 칸 지도(새로 짬)
fn=[[False]*n for _ in range(n)]
for y in range(n):
    for x in range(n):
        if x==6 or y==6: fn[y][x]=True
        if (x<9 and y<9) or (x>=n-8 and y<9) or (x<9 and y>=n-8): fn[y][x]=True
        if v>=7 and ((x>=n-11 and y<6) or (y>=n-11 and x<6)): fn[y][x]=True
ap={2:[6,18],7:[6,22,38],8:[6,24,42]}[v] if v in (2,7,8) else None
for cy in ap:
    for cx in ap:
        if fn[cy][cx] and not (cx==6 or cy==6) : continue
        if (cx==6 and cy==6) or (cx==6 and cy==ap[-1]) or (cx==ap[-1] and cy==6): continue
        for dy in range(-2,3):
            for dx in range(-2,3): fn[cy+dy][cx+dx]=True
fm=[lambda x,y:(x+y)%2==0,lambda x,y:y%2==0,lambda x,y:x%3==0,lambda x,y:(x+y)%3==0,
    lambda x,y:(x//3+y//2)%2==0,lambda x,y:x*y%2+x*y%3==0,lambda x,y:(x*y%2+x*y%3)%2==0,
    lambda x,y:((x+y)%2+x*y%3)%2==0][mask]
# 4) 지그재그 읽기
out=[]; col=n-1; up=True
while col>0:
    if col==6: col-=1
    rows=range(n-1,-1,-1) if up else range(n)
    for y in rows:
        for x in (col,col-1):
            if not fn[y][x]: out.append(M[y][x]^fm(x,y))
    up=not up; col-=2
cw=[int(''.join('1' if b else '0' for b in out[i:i+8]),2) for i in range(0,len(out)//8*8,8)]
print('codewords',len(cw))
# 5) 블록 풀기(v8-M = 2×(38+22) · 2×(39+22))
spec={8:[(2,38),(2,39)]}[v]; ecc=22
lens=[dl for c,dl in spec for _ in range(c)]
blocks=[[] for _ in lens]; k=0
for i in range(max(lens)):
    for j,L in enumerate(lens):
        if i<L: blocks[j].append(cw[k]); k+=1
eccb=[[] for _ in lens]
for i in range(ecc):
    for j in range(len(lens)): eccb[j].append(cw[k]); k+=1
# 6) RS 증후군 = 0 (α^i 에 넣어 셈 · 나눗셈 안 씀)
EXP=[0]*512; LOG=[0]*256; x=1
for i in range(255): EXP[i]=x; LOG[x]=i; x<<=1; x^=0x11D if x&0x100 else 0
for i in range(255,512): EXP[i]=EXP[i-255]
def mul(a,b): return 0 if a==0 or b==0 else EXP[LOG[a]+LOG[b]]
okrs=True
for j in range(len(lens)):
    word=blocks[j]+eccb[j]
    for r in range(ecc):
        a=EXP[r]; s=0
        for c in word: s=mul(s,a)^c
        if s: okrs=False
print('RS syndromes zero',okrs)
data=sum(blocks,[]); bs=''.join(format(c,'08b') for c in data)
mode=int(bs[:4],2); ln=int(bs[4:12],2)
txt=bytes(int(bs[12+8*i:20+8*i],2) for i in range(ln)).decode()
print('mode',mode,'len',ln); print('text',txt); print('MATCH',txt==d['text'])
