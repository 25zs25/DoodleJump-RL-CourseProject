"""Non-RL references reading exactly the same local observation."""
import math
import numpy as np
def rule_action(o,height=720,width=None):
    width=height*9/16 if width is None else width
    speed=7.2*width/725;g=.16*height/1289;gd=g*1.33
    x=(o[0]+1)*width/2;vy=o[3]*(14*height/1289)
    t_up=max(0.,-vy/g);apex=-max(0.,-vy)**2/(2*g)
    foot=40*height/1289;ph=28*height/1289
    choices=[]
    for i in range(20):
        p=o[5+10*i:15+10*i]
        if p[9]<.5:continue
        dy=p[1]*height-foot-ph/4
        if dy<apex+2:continue
        t=(t_up+math.sqrt(max(0,2*(dy-apex)/gd))) if vy<0 else (-vy+math.sqrt(max(0,vy*vy+2*gd*dy)))/gd if vy*vy+2*gd*dy>=0 else -1
        if t<=1:continue
        target=(x+p[0]*width)%width
        if p[5]>.5:
            lo=p[2]*width/2;span=width-2*lo
            z=(target-lo+p[3]*2*t)%(2*span)
            target=lo+(z if z<span else 2*span-z)
        dx=((target-x+width/2)%width)-width/2
        if abs(dx)>speed*t+p[2]*width/2+8:continue
        danger=0
        hole=o[-4:]
        if hole[3]>.5:
            hx=(x+hole[0]*width)%width
            if abs(((target-hx+width/2)%width)-width/2)<45 and abs(p[1]-hole[1])*height<80:danger=height
        cost=dy+danger+.025*abs(dx)
        choices.append((cost,dx))
    if not choices:return 1
    dx=min(choices,key=lambda c:c[0])[1]
    return 1 if abs(dx)<speed*1.5 else 2 if dx>0 else 0
