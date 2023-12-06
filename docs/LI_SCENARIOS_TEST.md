E1: 501@188
E2: 502@188
E3: 503@188

G1: 91075555@188 > Not Target
G2: 91070003@238 > Not Target
G3: 91070004@238 > Not Target

G1T: 91075555@188 > Target
G3T: 91070004@238 > Target

Z: 91072020@188 (LI)

##########################################################
1- Normal Call
##########################################################

1-1
=================================================
G1T     Call        G2      External (Outbound)
Z       Ring
G2      Answer      G1T

[x] Function
[x] HI2
[x] HI3

1-2
=================================================
G3      Call        G1T     Extension (Inbound)
Z       Ring
G1T     Answer      G3

[x] Function
[x] HI2
[x] HI3


##########################################################
2- Blind-Transfer *1*xyz#
##########################################################

2-1
=================================================
G3      Call        G1T     Extension (Inbound)
Z       Ring
G1T     Answer      G3
G1T     BTransfer   G2
G1T     Call        G2      External (Outbound)
G2      Answer      G1T
G2      Connected   G3

[x] Function
[?] HI2
[x] HI3

2-2
=================================================
G1T     Call        G2      External (Outbound)
Z       Ring
G2      Answer      G1T
G1T     BTransfer   G3
G1T     Call        G3      External (Outbound)
G3      Answer      G1T
G3      Connected   G2       
       
[x] Function
[?] HI2
[x] HI3

2-3
=================================================
G3      Call        G1T     Extension (Inbound)
Z       Ring
G1T     Answer      G3
G1T     BTransfer   E1      G1T == E3    
E3      Call        E1      Extension (Internal)
E1      Answer      E3

[x] Function
[?] No HI2
[x] HI3


##########################################################
3- Attended Transfer *2*xyz#
##########################################################

3-1
=================================================
E1      Call        E3      Extension (Internal)
E3      Answer      E1
E3      ATransfer   G3      G1T == E3
G1T     Call        G3      External (Outbound)
Z       Ring
G3      Answer      G1T
G1T     *
G3      Connected   E1

[x] Function
[?] HI2
[x] HI3

3-2
=================================================
E1      Call        E3      Extension (Internal)
E3      Answer      E1
E3      ATransfer   G3
G1T     Call        G3      External (Outbound)
Z       Ring
G3      Answer      G1T
G1T     #
Z       Hangup
E1      Connected   E3

[x] Function
[?] HI2
[x] HI3

3-3
=================================================
G3      Call        G1T     Extension (Inbound)
Z       Ring
G1T     Answer      G3
G1T     ATransfer   E1      G1T == E3
E3      Call        E1      Extension (Internal)
E1      Answer      E3
E3      *
E1      Connected   G3

[x] Function
[?] HI2
[x] HI3


##########################################################
4- Conference *3*xyz#
##########################################################

4-1
=================================================
E1      Call        E3      Extension (Internal)
E3      Answer      E1
E1      Conference  G3      E1 == G1T
G1T     Call        G3      External (Outbound)
Z       Ring
G3      Answer      G1T
G1T     *
G3      Connected

[x] Function
[?] HI2
[x] HI3

4-2
=================================================
G1T     Call        G3      External (Outbound)
Z       Ring
G3      Answer      G1T
G1T     Conference  E1      G1T == E3
E3      Call        E1      Extension (Internal)
E1      Answer      E3
E3      *
E1      Connected

[x] Function
[?] HI2
[x] HI3

4-3
=================================================
G1T     Call        G3      External (Outbound)
Z       Ring
G3      Answer      G1T
G1T     Conference  G2      
G1T     Call        G2      Extension (Internal)
G2      Answer      G1T
G1T     *
G2      Connected

[x] Function
[?] HI2
[x] HI3




