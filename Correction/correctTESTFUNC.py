


##
## version November updated for LHC by Glenn Vanbavinckhove + removing mad2dev (handled in GUI now)
## + also removed option j (one beam or both beam, was not used for anything)
##################################################################################################
##
##
##
##

import sys
sys.path.append('/afs/cern.ch/eng/sl/lintrack/Python_Classes4MAD/')
import pickle
from Numeric import *
from os import system
from metaclass import twiss
import random,re,sys
from LinearAlgebra import *
from optparse import OptionParser
from GenMatrix import *
from BCORR import *

########### START ###############




def  correctpy(options, args):



    print "Selected accelerator:", options.ACCEL
    print "Path to measurements:", options.path
    betapath = options.rpath
    print "Path to Repository:", betapath
    accelpath=betapath+'/MODEL/'+options.ACCEL+'/'+options.OPT+'/'
    print "Path to Accelerator model", accelpath
    print "Selected algorithm:", options.TECH


    if options.TECH=="MICADO":
        ncorr=int(options.ncorr)
        print "Number of Correctors Used:", options.ncorr
    else:
        if options.ACCEL=="SPS":
            MinStr =0.0
        else:
            MinStr = float(options.MinStr)
        print "Minimum corrector strength", MinStr
    modelcut=float(options.modelcut)
    errorcut=float(options.errorcut)
    cut= float(options.cut)
    print "Model, error and SVD cuts:", modelcut, errorcut, cut
    print "Starting loading Full Response optics"
    FullResponse=pickle.load(open(accelpath+'/FullResponse.Numeric','r'))
    print "Loading ended"




    x=twiss(options.path+'/getphasex.out')
    y=twiss(options.path+'/getphasey.out')
    try:
	dx=twiss(options.path+'/getNDx.out') # changed by Glenn Vanbavinckhove (26/02/09)
    except:
	print "WARNING: No good dispersion or inexistent file getDx"
	print "WARNING: Correction will not take into account NDx"
	dx=[]

    var=['']
    variable=''
    execfile(accelpath+'/AllLists.py')
    # extra depdency to be able to handle to different magnets group
    listvar=options.var.split(",")
    varslist=[]
    for var in listvar:
            
            #exec('variable='+var+'()')
            varslist=varslist+eval(var+'()')
    

    intqx=int(FullResponse['0'].Q1)
    intqy=int(FullResponse['0'].Q2)

    print "Integer part of tunes: ", intqx, intqy

    # remember to add integer part of the tunes to exp data!!!
    if x.Q1 > 0.0:
        x.Q1=x.Q1+intqx
    else:
        x.Q1=x.Q1+intqx+1.0
    if y.Q2 > 0.0:
        y.Q2=y.Q2+intqy
    else:
        y.Q2=y.Q2+intqy+1.0


    print "Experiment tunes: ", x.Q1, y.Q2

    variables=varslist
    phasexlist=MakePairs(x, FullResponse['0'], modelcut=modelcut, errorcut=errorcut)
    phaseylist=MakePairs(y, FullResponse['0'], modelcut=modelcut, errorcut=errorcut)
    betaxlist=[]
    betaylist=betaxlist
    displist=MakeList(dx, FullResponse['0'])
    print "Input ready"
    wei=[1,1,1,1,1,10] # Weights of phasex phasey betax betay disp and tunes
    print "weight=",wei
    beat_inp=beat_input(varslist, phasexlist, phaseylist, betaxlist, betaylist, displist, wei)

    sensitivity_matrix=beat_inp.computeSensitivityMatrix(FullResponse)



    if options.TECH=="SVD":
        [deltas, varslist ] = correctbeatEXP(x,y,dx, beat_inp, cut=cut, app=0, path=options.path)
        if 1:                           #All accelerators
            iteration=0
            # Let's remove too low useless correctors
            while (len(filter(lambda x: abs(x)< MinStr, deltas))>0):
                iteration=1+iteration
                il=len(varslist)
                print len(deltas),len(varslist)
                varslist_t=[]
                for i in range(0,il):
                  #print MinStr, deltas[i]
                  if (abs(deltas[i]) > MinStr):
                      varslist_t.append(varslist[i])
                  varslist=varslist_t
                  if len(varslist)==0:
                      print "You want to correct with too high cut on the corrector strength"
                      sys.exit()
                  beat_inp=beat_input(varslist, phasexlist, phaseylist, betaxlist, betaylist, displist, wei)
                  sensitivity_matrix=beat_inp.computeSensitivityMatrix(FullResponse)
                  [deltas, varslist ] = correctbeatEXP(x,y,dx, beat_inp, cut=cut, app=0, path=options.path)
                  print "Initial correctors:", il, ". Current: ",len(varslist), ". Removed for being lower than:", MinStr, "Iteration:", iteration
                  print deltas
    
    
    if options.TECH=="MICADO":
        bNCorrNumeric(x,y,dx,beat_inp, cut=cut,ncorr=ncorr,app=0,path=options.path)
    
    if options.ACCEL=="SPS":
	b=twiss(options.path+"/changeparameters.tfs")
	execfile(accelpath+'/Bumps.py')    # LOADS corrs
	execfile(accelpath+'/BumpsYASP.py') # LOADS corrsYASP
        #Output for YASP...
	f=open(options.path+"/changeparameters.yasp", "w")
        #Output for Knob...
        g=open(options.path+"/changeparameters.knob", "w")
        f.write("#PLANE H\n")
	f.write("#UNIT RAD\n")
	
        g.write("* NAME  DELTA \n")
        g.write("$ %s    %le   \n")
	plane = 'H'
	beam = '1'
	for corr in corrsYASP:
		print >>f, "#SETTING", corr,  corrsYASP[corr]
	for corr in corrs:
                print >>g, "K"+corr, corrs[corr]
	f.close()
        g.close()
        
    if "LHC" in options.ACCEL:   #.knob should always exist to be sent to LSA!
        system("cp "+options.path+"/changeparameters.tfs "+options.path+"/changeparameters.knob")

        # madx table
        b=twiss(options.path+"/changeparameters.tfs")
        mad=open(options.path+"/changeparameters.madx", "w")
        names=b.NAME
        delta=b.DELTA

        for i in range(len(names)):

            if cmp(delta[i],0)==1:
                mad.write(names[i]+" = "+names[i]+" + "+str(delta[i])+";\n");
            else:
                mad.write(names[i]+" = "+names[i]+" "+str(delta[i])+";\n");


            mad.write("return;");

        mad.close()
    return 0    





if __name__ == '__main__':


    parser = OptionParser()
    parser.add_option("-a", "--accel", 
                 help="What accelerator: LHCB1 LHCB2 SPS RHIC",
		 metavar="ACCEL", default="LHCB1",dest="ACCEL")
    parser.add_option("-t", "--tech", 
		 help="Which algorithm: SVD MICADO",
		 metavar="TECH", default="SVD",dest="TECH")
    parser.add_option("-n", "--ncorr", 
		 help="Number of Correctors for MICADO",
		 metavar="NCORR", default=5,dest="ncorr")
    parser.add_option("-p", "--path",
		 help="Path to experimental files",
		 metavar="PATH", default="./",dest="path")
    parser.add_option("-c", "--cut",
                  help="Singular value cut for the generalized inverse",
                  metavar="CUT", default=0.1 , dest="cut")
    parser.add_option("-e", "--errorcut",
                  help="Maximum error allowed for the phase measurement",
                  metavar="ERRORCUT", default=0.013 , dest="errorcut")
    parser.add_option("-m", "--modelcut",
                  help="Maximum difference allowed between model and measured phase",
                  metavar="MODELCUT", default=0.02 , dest="modelcut")
    parser.add_option("-r", "--rpath",
                  help="Path to BetaBeat repository (default is the afs repository)",
                  metavar="RPATH", default="/afs/cern.ch/eng/sl/lintrack/Beta-Beat.src/" , dest="rpath")
    parser.add_option("-o", "--optics",
                  help="optics",
                  metavar="OPT", default="nominal.opt" , dest="OPT")
    parser.add_option("-s", "--MinStr",
                  help="Minimum strength of correctors in SVD correction (default is 1e-6)",
                  metavar="MinStr", default=0.000001 , dest="MinStr")
    parser.add_option("-v", "--Variables",
                  help="variables split with ,",
                  metavar="var", default="MQTb1" , dest="var")
    parser.add_option("-j", "--JustOneBeam",
                  help="0 Just quads from one beam are used, 1 all quads (default is 0)",
                  metavar="JUSTONEBEAM", default=0 , dest="JustOneBeam")

    (options, args) = parser.parse_args()

    correctpy(options, args)
