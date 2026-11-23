"""Generate a quarter-symmetric elastic sphere-on-plane contact fixture in SI."""

import argparse
import json
import math
from pathlib import Path

def fixed(name,*data):
    if len(data)>9 or any(len(str(x))>8 for x in data):
        raise ValueError((name,data))
    return f'{name:<8}'+''.join(f'{x:>8}' for x in data)

def list_set(key, ids):
    tokens = [str(node) for node in ids]
    lines = []
    for offset in range(0, len(tokens), 9):
        prefix = ' ' if offset else f'SET {key} = '
        remainder = ',' if offset + 9 < len(tokens) else ''
        lines.append(prefix + ','.join(tokens[offset:offset+9]) + remainder)
    return lines

def region(n, faces):
    start=[]
    for i,(e,a,b,c) in enumerate(faces):
        label=f"+C{n}{i+1:04}"
        if i==0:
            start.append(fixed('BSURFS',n,'','','',e,a,b,c,label if len(faces)>1 else ''))
        else:
            start.append(fixed(f"+C{n}{i:04}",e,a,b,c,'','','','',label if i<len(faces)-1 else ''))
    start.append(fixed('BCRPARA',n,'','0.','FLEX'))
    return start

def discretize(h, length, fine_radius, factor):
    xs=[0.]
    while xs[-1]<fine_radius*.999:
        xs.append(xs[-1]+h)
    dx=h
    while xs[-1]<length:
        dx=min(dx*factor,length-xs[-1])
        xs.append(xs[-1]+dx)
    if len(xs)>2 and xs[-1]-xs[-2]<(xs[-2]-xs[-3])*.45:
        xs.pop(-2)
    return xs

def hertz(sol, div, far, folder, gentle=False):
    E=7.0e10
    nu=.3
    R=.05
    a=(3*100.*R/(4*(E/(2*(1-nu**2)))))**(1/3)
    h=a/div
    growth = 1.24 if gentle else 1.55
    x = discretize(h, far, .00051, growth)
    d = discretize(h, far, .00026, growth)
    n=len(x)-1
    nb=len(d)-1
    coords=[]
    elements=[]
    bottom_ids=[]
    contact_nodes=[]
    source_faces=[]
    target_faces=[]
    for top in (0,1):
        offset=len(coords)
        def g(i,j,k):
            return offset+(n+1)**2*k+(n+1)*j+i+1

        for k,depth in enumerate(d):
            for y in x:
                for u in x:
                    if top:
                        surface = (u*u+y*y)/(R+math.sqrt(R*R-u*u-y*y))
                        z = depth + surface*(1-depth/far)
                    else:
                        # Preserve element orientation and start the fine layers at the interface.
                        z = -d[nb-k]
                    coords.append((u,y,z))
        assert len(coords)==g(n,n,nb)
        for k in range(nb):
            for j in range(n):
                for i in range(n):
                    ns=(g(i,j,k),g(i+1,j,k),g(i+1,j+1,k),g(i,j+1,k),
                        g(i,j,k+1),g(i+1,j,k+1),g(i+1,j+1,k+1),g(i,j+1,k+1))
                    elements.append(ns)
                    has_contact=math.hypot(x[i],x[j])<.0009
                    if not top and k==nb-1 and has_contact:
                        target_faces.append((len(elements),*ns[4:7]))
                    if top and k==0 and has_contact:
                        source_faces.append((len(elements),*ns[:3]))
        contact_k=0 if top else nb
        contact_nodes += [g(i,j,contact_k) for j in range(n+1) for i in range(n+1)
                          if math.hypot(x[i],x[j])<.0011]
        if not top:
            bottom_ids=[g(i,j,0) for j in range(n+1) for i in range(n+1)]
        else:
            load_ids=[g(i,j,nb) for j in range(n+1) for i in range(n+1)]
            top_origin=g(0,0,nb)
            upper_origin=g(0,0,0)
    folder.mkdir(parents=True)
    cc=[f'SOL {sol}','CEND','TITLE = HERTZ SPHERICAL CONTACT','SPC = 1','BCSET = 100','OUTPUT']
    cc+=list_set(17,contact_nodes)+list_set(12,[top_origin,upper_origin,1])
    cc+=['SET 13 = 1 THRU '+str(bottom_ids[-1])]
    cc+=['BCRESULTS(PRINT,TRACTION,FORCE,SEPDIS,STATUS)=17',
         'DISPLACEMENT(PRINT,PLOT)=12','SPCFORCES(PRINT,PLOT)=13',
         'SUBCASE 1',' ANALYSIS=STATICS',' LABEL=HERTZ RAMP',' SEQDEP=YES',' NLCNTL=30',' TSTEP=11',' LOAD=20',
         'BEGIN BULK','PARAM,POST,-2','PARAM,LGDISP,-1','PARAM,LGSTRN,0','PARAM,MATNL,-1',
         'MAT1,1,7.0E10,,0.3','PSOLID,1,1','TSTEP1,11,1.,4,YES','BCTADD,100,110','BCTSET,110,10,11,0.,0.,.000040']
    if sol==401:
        cc+=['NLCNTL,30,MSGLVL,1,MSGLVLC,1,MAXITER,50','BCTPARM,110,INIPENE,0,AUTOSCAL,1.']
    else:
        cc+=['NLCNTL2,30,AUTOTIM,OFF,LVAR,RAMP,ITMA,40','+,MSGLVLC,1','BCTPAR2,110,NSIDE,1,INIPENE,0']
        cc[-2]+=',PRCR,1.E-5,PRCE,1.E-5'
    cc+=region(10,source_faces)+region(11,target_faces)
    for j,(u,v,w) in enumerate(coords,1):
        cc.extend([f'GRID*   {j:16}{0:16}{u:16.9E}{v:16.9E}*G{j:06}',f'*G{j:06}{w:16.9E}'])
    for k,ns in enumerate(elements,1):
        cc.extend([f'CHEXA,{k},1,'+','.join(map(str,ns[:6])), '+,'+','.join(map(str,ns[6:]))])
    for dof,ids in [(1,[i for i,y in enumerate(coords,1) if y[0]==0]),(2,[i for i,y in enumerate(coords,1) if y[1]==0]),(3,bottom_ids)]:
        for j in range(0,len(ids),6):
            cc.append(f'SPC1,1,{dof},'+','.join(map(str,ids[j:j+6])))
    weights=[((x[i+1] if i<n else x[i])-(x[i-1] if i else x[i]))*.5 for i in range(n+1)]
    fload=[25.*u*v/(far*far) for v in weights for u in weights]
    assert math.isclose(sum(fload),25.,rel_tol=1e-9)
    # Use a long free representation on FORCE to preserve the tributary load.
    for k,f in zip(load_ids,fload):
        cc.extend([f'FORCE*  {20:16}{k:16}{0:16}{f:16.9E}*F{k:06}',f'*F{k:06}{0.:16.9E}{0.:16.9E}{-1.:16.9E}'])
    cc.append('ENDDATA')
    (folder/'hertz.dat').write_text('\n'.join(cc)+'\n')
    (folder/'scope.json').write_text(json.dumps({'elements':len(elements),'nodes':len(coords),
        'face_nodes':contact_nodes,'source_face_nodes':contact_nodes[len(contact_nodes)//2:],
        'free_top_node':top_origin,'upper_origin':upper_origin,'h':h,'far':far,'bottom_last':bottom_ids[-1],
        'coordinates':{j:coords[j-1] for j in contact_nodes}},indent=2))
    print(sol,div,far,len(elements),len(coords),flush=True)

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('sol',type=int,choices=(401,402))
    p.add_argument('division',type=int,choices=(4,8,16))
    p.add_argument('far',type=float)
    p.add_argument('folder',type=Path)
    p.add_argument('--gentle',action='store_true',help='Reduce growth away from the contact patch')
    n=p.parse_args()
    if not .002 <= n.far <= .025:
        p.error('the half-width in meters must lie between 0.002 and 0.025')
    hertz(n.sol,n.division,n.far,n.folder,n.gentle)
