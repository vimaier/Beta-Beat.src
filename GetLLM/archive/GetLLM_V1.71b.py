## Python script to obtain Linear Lattice function and More -> GetLLM
## Version 1.51
## Version-up history:V1.0, 11/Feb/2008 by Masa. Aiba
##                    V1.1, 18/Feb/2008 Debugging, add model phase and tunes to output
##                                      add function to obtain DY
##                                      add chromatic parameter (phase for non zero DPP)
##                    V1.2, 22/Feb/2008 test version for beta with all BPM
##                    V1.3, 29/Feb/2008 beta from phases is improved, averaging beta1, 2 and 3
##                    V1.31, 12/Mar/2008 debugged on alpha3
##                    V1.4, 12/Mar/2008 modify output to fit latest TSF format and to meet requests from Rogelio
##                                      fix buggs in r.m.s. beta-beat and added to the output of getbetax/y.out
##                    V1.5 Update to option parser, include BPMdictionary to filter BPMs not in MOdel
##                                  Rogelio, 13 March 2008
##                    V1.51, 13/Mar/2008 Modify output to fit latest TSF format again. Add STD to beta.
##                    V1.6, 15/Jul/2008 Add the integer part of tunes - assuming that the phase advance is always less than 1.0.
##                    V1.71 27/Jul/2008 Add GetCO. Filter in Get
##

## Usage1 >python2.5 ../GetLLM25_V1.5.py -m ../../MODEL/SPS/twiss.dat -f ../../MODEL/SPS/SimulatedData/ALLBPMs.3 -o ./
## Usage2 >python2.5 ../GetLLM25_V1.5.py -m ../../MODEL/SPS/twiss.dat -d mydictionary.py -f 37gev270amp2_12.sdds.new -o ./


## lin files as many as you like

## Some rules for variable name: Dictionary is used to contain the output of function
##                               Valiable containing 'm' is a value directly obtained from measurment data
##                               Valiable containing 'mdl' is a value related to model




from metaclass import *
from Numeric import *
import sys, pickle,os
#import operator
from string import *


#######################################################
#                 Functions                           #
#######################################################

#------------

def modelIntersect(expbpms, model):
	bpmsin=[]
	for bpm in expbpms:
		try:
			check=model.indx[bpm[1].upper()]
			bpmsin.append(bpm)
		except:
			print bpm, "Not in Model"
	if len(bpmsin)==0:
		print "Zero intersection of Exp and Model"
		print "Please, provide a good Dictionary"
		print "Now we better leave!"
		sys.exit()			
	return bpmsin


def intersect(ListOfFile): 
	'''Pure intersection of all bpm names in all files '''
	if len(ListOfFile)==0:
		print "Nothing to intersect!!!!"
		sys.exit()
	z=ListOfFile[0].NAME
	for b in ListOfFile:
		z=filter(lambda x: x in z   , b.NAME)
		#print "len",len(z)
	#SORT by S
	result=[]
	x0=ListOfFile[0]
	for bpm in z:
		result.append((x0.S[x0.indx[bpm]], bpm))	
		
	result.sort()
	return result


#------------ Get phases

def GetPhases(MADTwiss,ListOfFiles,plane,outputpath):

	try:
		fdi=open(outputpath+'Drive.inp','r')  # Drive.inp file is normally in the outputpath directory in GUI operation
		for line in fdi:
			if "TUNE X" in line:
				fracxinp=line.split("=")
				fracx=fracxinp[1]
			if "TUNE Y" in line:
				fracyinp=line.split("=")
				fracy=fracyinp[1]
		fdi.close()
	except:
		fracx=0.1 # Otherwise, the fractional part is assumed to be below 0.5
		fracy=0.1 # Tentatively set 0.1

	


	commonbpms=intersect(ListOfFiles)
	commonbpms=modelIntersect(commonbpms, MADTwiss)
	#zdpp=len(ListOfFiles)
	
	mu=0.0
        tunem=[]
	phase={} # Dictionary for the output containing [average phase, rms error]
	for i in range(1,len(commonbpms)+1):
		if i==len(commonbpms)-1:
			bn1=upper(commonbpms[i-1][1])
			bn2=upper(commonbpms[i][1])
			bn3=upper(commonbpms[0][1])
			bns1=commonbpms[i-1][0]
			bns2=commonbpms[i][0]
		elif i==len(commonbpms):
			bn1=upper(commonbpms[i-1][1])
			bn2=upper(commonbpms[0][1])
			bn3=upper(commonbpms[1][1])
			bns1=commonbpms[i-1][0]
			bns2=commonbpms[0][0]
		else :
			bn1=upper(commonbpms[i-1][1])
			bn2=upper(commonbpms[i][1])
			bn3=upper(commonbpms[i+1][1])
			bns1=commonbpms[i-1][0]
			bns2=commonbpms[i][0]	
		phi12=[]
		phi13=[]
		tunemi=[]
		for j in ListOfFiles:
			# Phase has units of 2pi
			if plane=='H':
				phm12=(j.MUX[j.indx[bn2]]-j.MUX[j.indx[bn1]])
				phm13=(j.MUX[j.indx[bn3]]-j.MUX[j.indx[bn1]])
				tunemi.append(j.TUNEX[j.indx[bn1]])
			elif plane=='V':
				phm12=(j.MUY[j.indx[bn2]]-j.MUY[j.indx[bn1]])
				phm13=(j.MUY[j.indx[bn3]]-j.MUY[j.indx[bn1]])
				tunemi.append(j.TUNEY[j.indx[bn1]])
			if phm12<0: phm12+=1
			if phm13<0: phm13+=1
			if phm12>0.9 and i !=len(commonbpms):
				print 'Warning: there seems too large phase advance! '+bn1+' to '+bn2+' = '+str(phm12)
			phi12.append(phm12)
			phi13.append(phm13)
		phi12=array(phi12)
		phi13=array(phi13)
		phstd12=sqrt(average(phi12*phi12)-(average(phi12))**2.0)
		phstd13=sqrt(average(phi13*phi13)-(average(phi13))**2.0)
		phi12=average(phi12)
		phi13=average(phi13)
		tunemi=array(tunemi)
		tunem.append(average(tunemi))
		if i==len(commonbpms):
			tunem=array(tunem)
			tune=average(tunem)
			if plane=='H' and fracx > 0.0:
				phi12=phi12+tune
				if phi12>1.0: phi12=phi12-1.0
				mu=mu+phi12
			elif plane=='H' and fracx <= 0.0:
				phi12=phi12+(1.0+tune)
				if phi12>1.0: phi12=phi12-1.0
				mu=mu+phi12
			if plane=='V' and fracy > 0.0:
				phi12=phi12+tune
				if phi12>1.0: phi12=phi12-1.0
				mu=mu+phi12
			elif plane=='V' and fracy <= 0.0:
				phi12=phi12+(1.0+tune)
				if phi12>1.0: phi12=phi12-1.0
				mu=mu+phi12
		else:
			mu=mu+phi12
		phase[bn1]=[phi12,phstd12,phi13,phstd13]

	return [phase,tune,mu,commonbpms]


#-------- Beta from pahses

def BetaFromPhase(MADTwiss,ListOfZeroDPP,phase,plane):

	alfa={}
	beta={}
	commonbpms=intersect(ListOfZeroDPP)
	commonbpms=modelIntersect(commonbpms,MADTwiss)
	alfii=[]
        betii=[]
	delbeta=[]
	for i in range(0,len(commonbpms)-3):
		bn1=upper(commonbpms[i][1])
		bn2=upper(commonbpms[i+1][1])
		bn3=upper(commonbpms[i+2][1])
		ph2pi12=2.*pi*phase[bn1][0]
		ph2pi23=2.*pi*phase[bn2][0]
		ph2pi13=2.*pi*phase[bn1][2]
		# Find the model transfer matrices for beta1
		if plane=='H':
			phmdl12=2.*pi*(MADTwiss.MUX[MADTwiss.indx[bn2]]-MADTwiss.MUX[MADTwiss.indx[bn1]])
			phmdl13=2.*pi*(MADTwiss.MUX[MADTwiss.indx[bn3]]-MADTwiss.MUX[MADTwiss.indx[bn1]])
			phmdl23=2.*pi*(MADTwiss.MUX[MADTwiss.indx[bn3]]-MADTwiss.MUX[MADTwiss.indx[bn2]])
			betmdl1=MADTwiss.BETX[MADTwiss.indx[bn1]]
			betmdl2=MADTwiss.BETX[MADTwiss.indx[bn2]]
			betmdl3=MADTwiss.BETX[MADTwiss.indx[bn3]]
			alpmdl1=MADTwiss.ALFX[MADTwiss.indx[bn1]]
			alpmdl2=MADTwiss.ALFX[MADTwiss.indx[bn2]]
			alpmdl3=MADTwiss.ALFX[MADTwiss.indx[bn3]]
		elif plane=='V':
			phmdl12=2.*pi*(MADTwiss.MUY[MADTwiss.indx[bn2]]-MADTwiss.MUY[MADTwiss.indx[bn1]])
			phmdl13=2.*pi*(MADTwiss.MUY[MADTwiss.indx[bn3]]-MADTwiss.MUY[MADTwiss.indx[bn1]])
			phmdl23=2.*pi*(MADTwiss.MUY[MADTwiss.indx[bn3]]-MADTwiss.MUY[MADTwiss.indx[bn2]])
			betmdl1=MADTwiss.BETY[MADTwiss.indx[bn1]]
			betmdl2=MADTwiss.BETY[MADTwiss.indx[bn2]]
			betmdl3=MADTwiss.BETY[MADTwiss.indx[bn3]]
			alpmdl1=MADTwiss.ALFY[MADTwiss.indx[bn1]]
			alpmdl2=MADTwiss.ALFY[MADTwiss.indx[bn2]]
			alpmdl3=MADTwiss.ALFY[MADTwiss.indx[bn3]]
		# Find beta1 from phases assuming model transfer matrix
		# Matrix M: BPM1-> BPM2
		# Matrix N: BPM1-> BPM3
		M11=sqrt(betmdl2/betmdl1)*(cos(phmdl12)+alpmdl1*sin(phmdl12))
		M12=sqrt(betmdl1*betmdl2)*sin(phmdl12)
		N11=sqrt(betmdl3/betmdl1)*(cos(phmdl13)+alpmdl1*sin(phmdl13))
		N12=sqrt(betmdl1*betmdl3)*sin(phmdl13)
		denom=M11/M12-N11/N12
		numer=1/tan(ph2pi12)-1/tan(ph2pi13)
		beti1=numer/denom
		beterr1=abs(phase[bn1][1]*(1.-tan(ph2pi12)**2.)/tan(ph2pi12)**2.)
		beterr1=beterr1+abs(phase[bn1][3]*(1.-tan(ph2pi13)**2.)/tan(ph2pi13)**2.)
		beterr1=beterr1/abs(denom)
		denom=M12/M11-N12/N11
		numer=-M12/M11/tan(ph2pi12)+N12/N11/tan(ph2pi13)
		alfi1=numer/denom
		alferr1=abs(M12/M11*phase[bn1][1]*(1.-tan(ph2pi12)**2.)/tan(ph2pi12)**2.)
		alferr1=alferr1+abs(N12/N11*phase[bn1][3]*(1.-tan(ph2pi13)**2.)/tan(ph2pi13)**2.)
		alferr1=alferr1/abs(denom)

		# Find beta2 from phases assuming model transfer matrix
		# Matrix M: BPM1-> BPM2
		# Matrix N: BPM2-> BPM3
		M22=sqrt(betmdl1/betmdl2)*(cos(phmdl12)-alpmdl2*sin(phmdl12))
		M12=sqrt(betmdl1*betmdl2)*sin(phmdl12)
		N11=sqrt(betmdl3/betmdl2)*(cos(phmdl23)+alpmdl2*sin(phmdl23))
		N12=sqrt(betmdl2*betmdl3)*sin(phmdl23)
		denom=M22/M12+N11/N12
		numer=1/tan(ph2pi12)+1/tan(ph2pi23)
		beti2=numer/denom
		beterr2=abs(phase[bn1][1]*(1.-tan(ph2pi12)**2.)/tan(ph2pi12)**2.)
		beterr2=beterr2+abs(phase[bn2][1]*(1.-tan(ph2pi23)**2.)/tan(ph2pi23)**2.)
		beterr2=beterr2/abs(denom)
		denom=M12/M22+N12/N11
		numer=M12/M22/tan(ph2pi12)-N12/N11/tan(ph2pi23)
		alfi2=numer/denom
		alferr2=abs(M12/M22*phase[bn1][1]*(1.-tan(ph2pi12)**2.)/tan(ph2pi12)**2.)
		alferr2=alferr2+abs(N12/N11*phase[bn1][3]*(1.-tan(ph2pi23)**2.)/tan(ph2pi23)**2.)
		alferr2=alferr2/abs(denom)
		

		# Find beta3 from phases assuming model transfer matrix
		# Matrix M: BPM2-> BPM3
		# Matrix N: BPM1-> BPM3
		M22=sqrt(betmdl2/betmdl3)*(cos(phmdl23)-alpmdl3*sin(phmdl23))
		M12=sqrt(betmdl2*betmdl3)*sin(phmdl23)
		N22=sqrt(betmdl1/betmdl3)*(cos(phmdl13)-alpmdl3*sin(phmdl13))
		N12=sqrt(betmdl1*betmdl3)*sin(phmdl13)
		denom=M22/M12-N22/N12
		numer=1/tan(ph2pi23)-1/tan(ph2pi13)
		beti3=numer/denom
		beterr3=abs(phase[bn2][1]*(1.-tan(ph2pi23)**2.)/tan(ph2pi23)**2.)
		beterr3=beterr3+abs(phase[bn1][3]*(1.-tan(ph2pi13)**2.)/tan(ph2pi13)**2.)
		beterr3=beterr3/abs(denom)
		denom=M12/M22-N12/N22
		numer=M12/M22/tan(ph2pi23)-N12/N22/tan(ph2pi13)
		alfi3=numer/denom
		alferr3=abs(M12/M22*phase[bn1][1]*(1.-tan(ph2pi23)**2.)/tan(ph2pi23)**2.)
		alferr3=alferr3+abs(N22/N12*phase[bn1][3]*(1.-tan(ph2pi13)**2.)/tan(ph2pi13)**2.)
		alferr3=alferr3/abs(denom)

		betii.append([beti1,beterr1,beti2,beterr2,beti3,beterr3])
		alfii.append([alfi1,alferr1,alfi2,alferr2,alfi3,alferr3])



	i=0
	bn1=upper(commonbpms[i][1])
	beti=betii[i][0]
	beterr=betii[i][1]
	betstd=0.0
	beta[bn1]=(beti,beterr,betstd)
	alfi=alfii[i][0]
	alferr=alfii[i][1]
	alfstd=0.0
	alfa[bn1]=(alfi,alferr,alfstd)
	if plane=='H':
		betmdl1=MADTwiss.BETX[MADTwiss.indx[bn1]]
	elif plane=='V':
		betmdl1=MADTwiss.BETY[MADTwiss.indx[bn1]]
	delbeta.append((beti-betmdl1)/betmdl1)


	i=1
	bn1=upper(commonbpms[i][1])
	beti=(betii[i][0]+betii[i-1][2])/2.
	beterr=sqrt(betii[i][1]**2.+betii[i-1][3]**2.)/sqrt(2.)
	betstd=sqrt((betii[i][0]**2.+betii[i-1][2]**2.)/2.-((betii[i][0]+betii[i-1][2])/2.)**2.)
	beta[bn1]=(beti,beterr,betstd)
	alfi=(alfii[i][0]+alfii[i-1][2])/2.
	alferr=sqrt(alfii[i][1]**2.+alfii[i-1][3]**2.)/sqrt(2.)
	alfstd=sqrt((alfii[i][0]**2.+alfii[i-1][2]**2.)/2.-((alfii[i][0]+alfii[i-1][2])/2.)**2.)
	alfa[bn1]=(alfi,alferr,alfstd)
	if plane=='H':
		betmdl1=MADTwiss.BETX[MADTwiss.indx[bn1]]
	elif plane=='V':
		betmdl1=MADTwiss.BETY[MADTwiss.indx[bn1]]
	delbeta.append((beti-betmdl1)/betmdl1)

	for i in range(2,len(commonbpms)-3):
		bn1=upper(commonbpms[i][1])
		beti=(betii[i][0]+betii[i-1][2]+betii[i-2][4])/3.
		# error?
		beterr=sqrt(betii[i][1]**2.+betii[i-1][3]**2.+betii[i-2][5]**2.)/sqrt(3.)
		betstd=sqrt((betii[i][0]**2.+betii[i-1][2]**2.+betii[i-2][4]**2.)/3.-((betii[i][0]+betii[i-1][2]+betii[i-2][4])/3.)**2.)
		beta[bn1]=(beti,beterr,betstd)
		alfi=(alfii[i][0]+alfii[i-1][2]+alfii[i-2][4])/3.
		alferr=sqrt(alfii[i][1]**2.+alfii[i-1][3]**2.+alfii[i-2][5]**2.)/sqrt(3.)
		alfstd=sqrt((alfii[i][0]**2.+alfii[i-1][2]**2.+alfii[i-2][4]**2.)/3.-((alfii[i][0]+alfii[i-1][2]+alfii[i-2][4])/3.)**2.)
		alfa[bn1]=(alfi,alferr,alfstd)
		if plane=='H':
			betmdl1=MADTwiss.BETX[MADTwiss.indx[bn1]]
		elif plane=='V':
			betmdl1=MADTwiss.BETY[MADTwiss.indx[bn1]]
		delbeta.append((beti-betmdl1)/betmdl1)
		

	delbeta=array(delbeta)
	rmsbb=sqrt(average(delbeta*delbeta))
	return [beta,rmsbb,alfa,commonbpms]

#-------------------------

def GetCO(MADTwiss, ListOfFiles):

	commonbpms=intersect(ListOfFiles)
	commonbpms=modelIntersect(commonbpms, MADTwiss)
	co={} # Disctionary for output
	for i in range(0,len(commonbpms)):
		bn1=upper(commonbpms[i][1])
		bns1=commonbpms[i][0]
		coi=0.0
		coi2=0.0
		for j in ListOfFiles:
			coi=coi + j.CO[j.indx[bn1]]
			coi2=coi2 + j.CO[j.indx[bn1]]**2
		coi=coi/len(ListOfFiles)
		corms=sqrt(coi2/len(ListOfFiles)-coi**2)
		co[bn1]=[coi,corms]
	return [co, commonbpms]


#--------------
def NormDispX(MADTwiss, ListOfZeroDPPX, ListOfNonZeroDPPX, ListOfCOX, COcut):

	nzdpp=len(ListOfNonZeroDPPX) # How many non zero dpp
	zdpp=len(ListOfZeroDPPX)  # How many zero dpp
	if zdpp==0 or nzdpp ==0:
		print 'Error: No data for dp/p=0 or for dp/p!=0.'
		sys.exit() #!?

	coac=ListOfCOX[0] # COX dictionary after cut bad BPMs
	coact={}
	for i in coac:
		if (coac[i][1] < COcut):
			coact[i]=coac[i]
	coac=coact


	#coact={}
	#for i in coac:
		#Dt=[]
		#for j in range(1,len(ListOfCOX)):
			#codpp=ListOfCOX[j]
			#Dj=(codpp[i][0]-coac[i][0])/ListOfNonZeroDPPX[j-1].DPP
			#Dt.append(Dj)
		#Dt=array(Dt)
		#Dt=average(Dt) # Tentative dispersion
		#coj=0.0
		#coj2=0.0
		#for j in range(1,len(ListOfCOX)):
			#codpp=ListOfCOX[j]
			#coj=coj+(codpp[i][0]-coac[i][0])-Dt*ListOfNonZeroDPPX[j-1].DPP
			#coj2=coj2 + ((codpp[i][0]-coac[i][0])-Dt*ListOfNonZeroDPPX[j-1].DPP)**2
		#coj=coj/nzdpp
		#corms=sqrt(coj2/nzdpp-coj**2)
		#if (corms < COcut):
			#coact[i]=coac[i]

	#coac=coact



	nda={} # Dictionary for the output containing [average Disp, rms error]

	ALL=ListOfZeroDPPX+ListOfNonZeroDPPX
	commonbpmsALL=intersect(ALL)
        commonbpmsALL=modelIntersect(commonbpmsALL, MADTwiss)
	
	mydp=[]
	gf=[]
	for j in ListOfNonZeroDPPX:
		mydp.append(j.DPP)
		gf.append(0.0)
	mydp=array(mydp)
	wf=array(mydp)/sum(mydp)*len(mydp) #Weight for the average depending on DPP


	# Find the global factor
	nd=[]
	ndmdl=[]
	for i in range(0,len(commonbpmsALL)):
		bn1=upper(commonbpmsALL[i][1])
		bns1=commonbpmsALL[i][0]
		ndmdli=MADTwiss.DX[MADTwiss.indx[bn1]]/sqrt(MADTwiss.BETX[MADTwiss.indx[bn1]])
		ndmdl.append(ndmdli)

		try:
			coi=coac[bn1]

			ampi=0.0
			for j in ListOfZeroDPPX:
				ampi+=j.AMPX[j.indx[bn1]]
			ampi=ampi/zdpp # Note that ampi is averaged with kick size weighting


			ndi=[]
			for j in range(0,nzdpp): # the range(0,nzdpp) instead of ListOfNonZeroDPPX is used because the index j is used in the loop
				codpp=ListOfCOX[j+1]
				orbit=codpp[bn1][0]-coi[0]
				ndm=orbit/ampi
				gf[j]+=ndm
				ndi.append(ndm)
			nd.append(ndi)
		except:
			coi=0


	ndmdl=array(ndmdl)
	avemdl=average(ndmdl)

	gf=array(gf)
	gf=gf/avemdl/len(commonbpmsALL)




	# Find normalized dispersion and its rms
	nd=array(nd)
	bpms=[]
	for i in range(0,len(commonbpmsALL)):
		ndi=[]
		bn1=upper(commonbpmsALL[i][1])
		bns1=commonbpmsALL[i][0]
		try:
			coac[bn1]
			for j in range(0,nzdpp): # the range(0,nzdpp) instead of ListOfZeroDPPX is used because the index j is used in the loop
				ndi.append(nd[i][j]/gf[j])
			ndi=array(ndi)
			ndstd=sqrt(average(ndi*ndi)-(average(ndi))**2.0)
			ndas=average(wf*ndi)
			nda[bn1]=[ndas,ndstd]
			bpms.append([bns1,bn1]) 
		except:
			0
	return [nda,bpms]



#-----------

def DYfromOrbit(ListOfZeroDPPY,ListOfNonZeroDPPY,ListOfCOY,COcut):


	coac=ListOfCOY[0] # COX dictionary after cut bad BPMs
	coact={}
	for i in coac:
		if (coac[i][1] < COcut):
			coact[i]=coac[i]

	coac=coact

        ALL=ListOfZeroDPPY+ListOfNonZeroDPPY
	commonbpmsALL=intersect(ALL)

	nzdpp=len(ListOfNonZeroDPPY) # How many non zero dpp
	zdpp=len(ListOfZeroDPPY)  # How many zero dpp


	mydp=[]
	for j in ListOfNonZeroDPPY:
		mydp.append(j.DPP)
	mydp=array(mydp)
	wf=array(mydp)/sum(mydp)*len(mydp) #Weitghs for the average

	dyo={} # Dictionary for the output containing [average Disp, rms error]
	bpms=[]
	for i in range(0,len(commonbpmsALL)):
		bn1=upper(commonbpmsALL[i][1])
		bns1=commonbpmsALL[i][0]

		try:
			coi=coac[bn1]
			dyoi=[]
			for j in ListOfNonZeroDPPY:
				dyoi.append((j.CO[j.indx[bn1]]-coi[0])/j.DPP)
			dyoi=array(dyoi)
			dyostd=sqrt(average(dyoi*dyoi)-(average(dyoi))**2.0)
			dyos=average(wf*dyoi)
			dyo[bn1]=[dyos,dyostd]
			bpms.append([bns1,bn1]) 
		except:
			coi=0
	return [dyo,bpms]
		
#######################################################
#                   Main part                         #
#######################################################


# Path to accelerator setting file
# This path shuold be changed to be compatible to your wourking system.
accpath="/afs/cern.ch/eng/sl/lintrack/Beta-Beat.src/CoreFiles/"


#-- Find index of python command in the system call
#i=0
#for entry in sys.argv:
#	if '.py' in entry: 
#		indpy=i
#		break
#	i=i+1

#-- Reading sys.argv
from optparse import OptionParser
parser = OptionParser()
parser.add_option("-a", "--accel",
                help="Which accelerator: LHCB1 LHCB2 SPS RHIC",
                metavar="ACCEL", default="LHCB1",dest="ACCEL")
parser.add_option("-d", "--dictionary",
                help="File with the BPM dictionary",
                metavar="DICT", default="0", dest="dict")
parser.add_option("-m", "--model",
                help="Twiss File",
                metavar="TwissFile", default="0", dest="Twiss")
parser.add_option("-f", "--files",
                help="Files from analysis, separated by comma",
                metavar="TwissFile", default="0", dest="files")
parser.add_option("-o", "--output",
                help="Output Path",
                metavar="OUT", default="./", dest="output")
parser.add_option("-c", "--cocut",
                help="Cut for closed orbit measurement [um]",
                metavar="COCUT", default=1000, dest="COcut")


(options, args) = parser.parse_args()


listOfInputFiles=options.files.split(",")
file0=options.Twiss
outputpath=options.output
if options.dict=="0":
	BPMdictionary={}
else:
	execfile(options.dict)
	BPMdictionary=dictionary   # temporaryly since presently name is not BPMdictionary

#file0=sys.argv[indpy+2]
MADTwiss=twiss(file0, BPMdictionary) # MODEL from MAD


try:
	facc=accpath+str(options.ACCEL)+'/accelerator.dat'
	faccs=twiss(facc)
	BPMU=faccs.BPMUNIT
except:
	BPMU='um'

COcut= float(options.COcut)

if BPMU=='um' or BPMU=='um': COcut=COcut
elif BPMU=='mm' or BPMU=='mm': COcut=COcut/1.0e3
elif BPMU=='cm' or BPMU=='cm': COcut=COcut/1.0e4
elif BPMU=='m' or BPMU=='m': COcut=COcut/1.0e6



#outputpath=sys.argv[indpy+1]

fphasex=open(outputpath+'getphasex.out','w')
fphasey=open(outputpath+'getphasey.out','w')

fphasex.write('@ MAD_FILE %s "'+file0+'"'+'\n')
fphasey.write('@ MAD_FILE %s "'+file0+'"'+'\n')
fphasex.write('@ FILES %s "')
fphasey.write('@ FILES %s "')

fbetax=open(outputpath+'getbetax.out','w')
fbetay=open(outputpath+'getbetay.out','w')
fbetax.write('@ MAD_FILE %s "'+file0+'"'+'\n')
fbetay.write('@ MAD_FILE %s "'+file0+'"'+'\n')
fbetax.write('@ FILES %s "')
fbetay.write('@ FILES %s "')

fcox=open(outputpath+'getCOx.out','w')
fcoy=open(outputpath+'getCOy.out','w')
fcox.write('@ MAD_FILE %s "'+file0+'"'+'\n')
fcoy.write('@ MAD_FILE %s "'+file0+'"'+'\n')
fcox.write('@ FILES %s "')
fcoy.write('@ FILES %s "')

fDx=open(outputpath+'getDx.out','w')
fDy=open(outputpath+'getDy.out','w')
fDx.write('@ MAD_FILE %s "'+file0+'"'+'\n')
fDy.write('@ MAD_FILE %s "'+file0+'"'+'\n')
fDx.write('@ FILES %s "')
fDy.write('@ FILES %s "')



FileOfZeroDPPX=[]
FileOfZeroDPPY=[]
FileOfNonZeroDPPX=[]
FileOfNonZeroDPPY=[]
ListOfZeroDPPX=[]
ListOfNonZeroDPPX=[]
ListOfZeroDPPY=[]
ListOfNonZeroDPPY=[]
woliny=0  # Let's assume there is liny for the moment
woliny2=0
for filein in listOfInputFiles:
	file1=filein+'_linx'
	x1=twiss(file1)
	try:
		dppi=x1.DPP
	except:
		dppi=0.0

	if dppi==0.0:
		ListOfZeroDPPX.append(twiss(file1))
		FileOfZeroDPPX.append(file1)
		fphasex.write(file1+' ')
		fbetax.write(file1+' ')
		fcox.write(file1+' ')
		fDx.write(file1+' ')
	else:
		ListOfNonZeroDPPX.append(twiss(file1))
		FileOfNonZeroDPPX.append(file1)
		fDx.write(file1+' ')

	try:
		file1=filein+'_liny'
		y1=twiss(file1)
		try:
			dppi=y1.DPP
		except:
			dppi=0.0
		if dppi==0.0:
			ListOfZeroDPPY.append(twiss(file1))
			FileOfZeroDPPY.append(file1)
			fphasey.write(file1+' ')
			fbetay.write(file1+' ')
			fcoy.write(file1+' ')
			fDy.write(file1+' ')
		else:
			ListOfNonZeroDPPY.append(twiss(file1))
			FileOfNonZeroDPPY.append(file1)
			fDy.write(file1+' ')
	except:
		print 'Warning: There seems no '+str(file1)+' file in the specified directory.' 


fphasex.write('"'+'\n')
fphasey.write('"'+'\n')
fbetax.write('"'+'\n')
fbetay.write('"'+'\n')
fcox.write('"'+'\n')
fcoy.write('"'+'\n')
fDx.write('"'+'\n')
fDy.write('"'+'\n')




if len(ListOfZeroDPPY)==0 :
	woliny=1  #FLAG meaning there is no _liny file for zero DPPY!
if len(ListOfNonZeroDPPY)==0 :
	woliny2=1  #FLAG meaning there is no _liny file for non-zero DPPY!



#-------- Check monitor compatibility between data and model

ALL=ListOfNonZeroDPPX+ListOfZeroDPPX+ListOfNonZeroDPPY+ListOfZeroDPPY
for j in range(0,len(ALL)) :
	z=ALL[j].NAME
	for bpm in z:
		try:
			check=MADTwiss.NAME[MADTwiss.indx[bpm]]
		except:
			try:
				check=MADTwiss.NAME[MADTwiss.indx[upper(bpm)]]
			except:
				print 'Monitor '+bpm+' cannot be found in the model!'
				#exit()


#-------- START Phases

plane='H'
[phasex,Q1,MUX,bpmsx]=GetPhases(MADTwiss,ListOfZeroDPPX,plane,outputpath)

if woliny!=1:
	plane='V'
	[phasey,Q2,MUY,bpmsy]=GetPhases(MADTwiss,ListOfZeroDPPY,plane,outputpath)
	fphasey.write('@ Q1 %le '+str(Q1)+'\n')
	fphasey.write('@ MUX %le '+str(MUX)+'\n')
	fphasey.write('@ Q2 %le '+str(Q2)+'\n')
	fphasey.write('@ MUY %le '+str(MUY)+'\n')
	fphasey.write('* NAME   NAME2  POS1   POS2   COUNT  PHASE  STDPH  PHYMDL MUYMDL\n')
	fphasey.write('$ %s     %s     %le    %le    %le    %le    %le    %le    %le\n')
	#bpms=intersect(ListOfZeroDPPY)
	#bpms=modelIntersect(bpms, MADTwiss)
	for i in range(1,len(bpmsy)-1):
		if i==len(bpmsy):
			bn1=upper(bpmsy[i-1][1])
			bn2=upper(bpmsy[0][1])
			bns1=bpmsy[i-1][0]
			bns2=bpmsy[0][0]
			phmdl=MADTwiss.MUY[MADTwiss.indx[bn2]]+MADTwiss.Q2-MADTwiss.MUY[MADTwiss.indx[bn1]]
		else:
			bn1=upper(bpmsy[i-1][1])
			bn2=upper(bpmsy[i][1])
			bns1=bpmsy[i-1][0]
			bns2=bpmsy[i][0]	
			phmdl=MADTwiss.MUY[MADTwiss.indx[bn2]]-MADTwiss.MUY[MADTwiss.indx[bn1]]
		fphasey.write('"'+bn1+'" '+'"'+bn2+'" '+str(bns1)+' '+str(bns2)+' '+str(len(ListOfZeroDPPY))+' '+str(phasey[bn1][0])+' '+str(phasey[bn1][1])+' '+str(phmdl)+' '+str(MADTwiss.MUY[MADTwiss.indx[bn1]])+'\n' )

fphasey.close()


fphasex.write('@ Q1 %le '+str(Q1)+'\n')
fphasex.write('@ MUX %le '+str(MUX)+'\n')

try:
	fphasex.write('@ Q2 %le '+str(Q2)+'\n')
	fphasex.write('@ MUY %le '+str(MUY)+'\n')
except:
	fphasex.write('@ Q2 %le '+'0.0'+'\n')
	fphasey.write('@ MUY %le '+'0.0'+'\n')
fphasex.write('* NAME   NAME2  POS1   POS2   COUNT  PHASE  STDPH  PHXMDL MUXMDL\n')
fphasex.write('$ %s     %s     %le    %le    %le    %le    %le    %le    %le\n')
#bpms=intersect(ListOfZeroDPPX)
#bpms=modelIntersect(bpms, MADTwiss)
for i in range(1,len(bpmsx)-1):
	if i==len(bpmsx):
		bn1=upper(bpmsx[i-1][1])
		bn2=upper(bpmsx[0][1])
		bns1=bpmsx[i-1][0]
		bns2=bpmsx[0][0]
		phmdl=MADTwiss.MUX[MADTwiss.indx[bn2]]+MADTwiss.Q1-MADTwiss.MUX[MADTwiss.indx[bn1]]
	else:
		bn1=upper(bpmsx[i-1][1])
		bn2=upper(bpmsx[i][1])
		bns1=bpmsx[i-1][0]
		bns2=bpmsx[i][0]	
		phmdl=MADTwiss.MUX[MADTwiss.indx[bn2]]-MADTwiss.MUX[MADTwiss.indx[bn1]]
	fphasex.write('"'+bn1+'" '+'"'+bn2+'" '+str(bns1)+' '+str(bns2)+' '+str(len(ListOfZeroDPPX))+' '+str(phasex[bn1][0])+' '+str(phasex[bn1][1])+' '+str(phmdl)+' '+str(MADTwiss.MUX[MADTwiss.indx[bn1]])+'\n' )

fphasex.close()



#-------- START Beta

plane='H'
betax={}
alfax={}
rmsbbx=0.
[betax,rmsbbx,alfax,bpms]=BetaFromPhase(MADTwiss,ListOfZeroDPPX,phasex,plane)
fbetax.write('@ Q1 %le '+str(Q1)+'\n')
try:
	fbetax.write('@ Q2 %le '+str(Q2)+'\n')
except:
	fbetax.write('@ Q2 %le '+'0.0'+'\n')
fbetax.write('@ RMS-beta-beat %le '+str(rmsbbx)+'\n')
fbetax.write('* NAME   POS    COUNT  BETX   ERRBETX STDBETX ALFX   ERRALFX STDALFX BETXMDL ALFXMDL MUXMDL\n')
fbetax.write('$ %s     %le    %le    %le    %le     %le     %le    %le     %le     %le     %le     %le\n')
#bpms=intersect(ListOfZeroDPPX)
#bpms=modelIntersect(bpms, MADTwiss)
for i in range(1,len(bpms)-3):
	bn1=upper(bpms[i-1][1])
	bn2=upper(bpms[i][1])
	bns1=bpms[i-1][0]
	bns2=bpms[i][0]
	fbetax.write('"'+bn1+'" '+str(bns1)+' '+str(len(ListOfZeroDPPX))+' '+str(betax[bn1][0])+' '+str(betax[bn1][1])+' '+str(betax[bn1][2])+' '+str(alfax[bn1][0])+' '+str(alfax[bn1][1])+' '+str(alfax[bn1][2])+' '+str(MADTwiss.BETX[MADTwiss.indx[bn1]])+' '+str(MADTwiss.ALFX[MADTwiss.indx[bn1]])+' '+str(MADTwiss.MUX[MADTwiss.indx[bn1]])+'\n' )

fbetax.close()

if woliny!=1:
	plane='V'
	betay={}
	alfay={}
	rmsbby=0.
	[betay,rmsbby,alfay,bpms]=BetaFromPhase(MADTwiss,ListOfZeroDPPY,phasey,plane)
	fbetay.write('@ Q1 %le '+str(Q1)+'\n')
	fbetay.write('@ Q2 %le '+str(Q2)+'\n')
	fbetay.write('@ RMS-beta-beat %le '+str(rmsbby)+'\n')
	fbetay.write('* NAME   POS    COUNT  BETY   ERRBETY STDBETY ALFY   ERRALFY STDALFY BETYMDL ALFYMDL MUYMDL\n')
	fbetay.write('$ %s     %le    %le    %le    %le     %le     %le    %le     %le     %le     %le     %le\n')
	#bpms=intersect(ListOfZeroDPPY)
	#bpms=modelIntersect(bpms, MADTwiss)
	for i in range(1,len(bpms)-3):
		bn1=upper(bpms[i-1][1])
		bn2=upper(bpms[i][1])
		bns1=bpms[i-1][0]
		bns2=bpms[i][0]
		fbetay.write('"'+bn1+'" '+str(bns1)+' '+str(len(ListOfZeroDPPY))+' '+str(betay[bn1][0])+' '+str(betay[bn1][1])+' '+str(betay[bn1][2])+' '+str(alfay[bn1][0])+' '+str(alfay[bn1][1])+' '+str(alfay[bn1][2])+' '+str(MADTwiss.BETY[MADTwiss.indx[bn1]])+' '+str(MADTwiss.ALFY[MADTwiss.indx[bn1]])+' '+str(MADTwiss.MUY[MADTwiss.indx[bn1]])+'\n' )

fbetay.close()

#-------- START Orbit

[cox,bpms]=GetCO(MADTwiss, ListOfZeroDPPX)

fcox.write('@ Q1 %le '+str(Q1)+'\n')

try:
	fcox.write('@ Q2 %le '+str(Q2)+'\n')
except:
	fcox.write('@ Q2 %le '+'0.0'+'\n')
fcox.write('* NAME   POS1   COUNT  COX    STDCOX COXMDL MUXMDL\n')
fcox.write('$ %s     %le    %le    %le    %le    %le    %le\n')
for i in range(0,len(bpms)):
	bn1=upper(bpms[i][1])
	bns1=bpms[i][0]
	fcox.write('"'+bn1+'" '+str(bns1)+' '+str(len(ListOfZeroDPPX))+' '+str(cox[bn1][0])+' '+str(cox[bn1][1])+' '+str(MADTwiss.X[MADTwiss.indx[bn1]])+' '+str(MADTwiss.MUX[MADTwiss.indx[bn1]])+'\n' )

fcox.close()

ListOfCOX=[]
ListOfCOX.append(cox)


if woliny!=1:
	[coy,bpms]=GetCO(MADTwiss, ListOfZeroDPPY)
	fcoy.write('@ Q1 %le '+str(Q1)+'\n')
	fcoy.write('@ Q2 %le '+str(Q2)+'\n')
	fcoy.write('* NAME   POS1   COUNT  COY    STDCOY COYMDL MUYMDL\n')
	fcoy.write('$ %s     %le    %le    %le    %le    %le    %le\n')
	for i in range(0,len(bpms)):
		bn1=upper(bpms[i][1])
		bns1=bpms[i][0]
		fcoy.write('"'+bn1+'" '+str(bns1)+' '+str(len(ListOfZeroDPPY))+' '+str(coy[bn1][0])+' '+str(coy[bn1][1])+' '+str(MADTwiss.Y[MADTwiss.indx[bn1]])+' '+str(MADTwiss.MUY[MADTwiss.indx[bn1]])+'\n' )

fcoy.close()

ListOfCOY=[]
ListOfCOY.append(coy)

#-------- Orbit for non-zero DPP

k=0
for j in ListOfNonZeroDPPX:
	SingleFile=[]
	SingleFile.append(j)
	file1=outputpath+'getCOx_dpp_'+str(k+1)+'.out'
	fcoDPP=open(file1,'w')
	fcoDPP.write('@ MAD_FILE: %s "'+file0+'"'+'\n')
	fcoDPP.write('@ FILE %s "')
	fcoDPP.write(FileOfNonZeroDPPX[k]+' "'+'\n')
	fcoDPP.write('@ DPP %le '+str(j.DPP)+'\n')
	fcoDPP.write('@ Q1 %le '+str(Q1)+'\n')
	try:
		fcoDPP.write('@ Q2 %le '+str(Q2)+'\n')
	except:
		fcoDPP.write('@ Q2 %le '+'0.0'+'\n')
	[codpp,bpms]=GetCO(MADTwiss, SingleFile)
	fcoDPP.write('* NAME   POS1   COUNT  COX    STDCOX COYMDL MUYMDL\n')
	fcoDPP.write('$ %s     %le    %le    %le    %le    %le    %le\n')
	for i in range(0,len(bpms)-1):
		bn1=upper(bpms[i][1])
		bns1=bpms[i][0]
		fcoDPP.write('"'+bn1+'" '+str(bns1)+' '+str(len(ListOfZeroDPPX))+' '+str(codpp[bn1][0])+' '+str(codpp[bn1][1])+' '+str(MADTwiss.X[MADTwiss.indx[bn1]])+' '+str(MADTwiss.MUX[MADTwiss.indx[bn1]])+'\n' )
	fcoDPP.close()
	ListOfCOX.append(codpp)
	k+=1

if woliny2!=1:
	k=0
	for j in ListOfNonZeroDPPY:
		SingleFile=[]
		SingleFile.append(j)
		file1=outputpath+'getCOy_dpp_'+str(k+1)+'.out'
		fcoDPP=open(file1,'w')
		fcoDPP.write('@ MAD_FILE: %s "'+file0+'"'+'\n')
		fcoDPP.write('@ FILE %s "')
		fcoDPP.write(FileOfNonZeroDPPY[k]+' "'+'\n')
		fcoDPP.write('@ DPP %le '+str(j.DPP)+'\n')
		fcoDPP.write('@ Q1 %le '+str(Q1)+'\n')
		try:
			fcoDPP.write('@ Q2 %le '+str(Q2)+'\n')
		except:
			fcoDPP.write('@ Q2 %le '+'0.0'+'\n')
		[codpp,bpms]=GetCO(MADTwiss, SingleFile)
		fcoDPP.write('* NAME   POS1   COUNT  COX    STDCOX COYMDL MUYMDL\n')
		fcoDPP.write('$ %s     %le    %le    %le    %le    %le    %le\n')
		for i in range(0,len(bpms)-1):
			bn1=upper(bpms[i][1])
			bns1=bpms[i][0]
			fcoDPP.write('"'+bn1+'" '+str(bns1)+' '+str(len(ListOfZeroDPPY))+' '+str(codpp[bn1][0])+' '+str(codpp[bn1][1])+' '+str(MADTwiss.Y[MADTwiss.indx[bn1]])+' '+str(MADTwiss.MUX[MADTwiss.indx[bn1]])+'\n' )
		fcoDPP.close()
		ListOfCOY.append(codpp)
		k+=1



#-------- START Dispersion

[nda,bpms]=NormDispX(MADTwiss, ListOfZeroDPPX, ListOfNonZeroDPPX, ListOfCOX,COcut)
fDx.write('@ Q1 %le '+str(Q1)+'\n')
try:
	fDx.write('@ Q2 %le '+str(Q2)+'\n')
except:
	fDx.write('@ Q2 %le '+'0.0'+'\n')
fDx.write('* NAME   POS    COUNT  NDX    STDNDX DX     NDXMDL DXMDL  MUXMDL\n')
fDx.write('$ %s     %le    %le    %le    %le    %le    %le    %le    %le\n')
ALL=ListOfZeroDPPX+ListOfNonZeroDPPX
for i in range(0,len(bpms)):
	bn1=upper(bpms[i][1])
	bns1=bpms[i][0]
	ndmdl=MADTwiss.DX[MADTwiss.indx[bn1]]/sqrt(MADTwiss.BETX[MADTwiss.indx[bn1]])
	try:
		dxi=nda[bn1][0]*sqrt(betax[bn1][0])
	except:
		dxi=0.0
	fDx.write('"'+bn1+'" '+str(bns1)+' '+str(len(ListOfNonZeroDPPX))+' '+str(nda[bn1][0])+' '+str(nda[bn1][1])+' '+str(dxi)+' '+str(ndmdl)+' '+str(MADTwiss.DX[MADTwiss.indx[bn1]])+' '+str(MADTwiss.MUX[MADTwiss.indx[bn1]])+'\n' )

fDx.close()



if woliny!=1 and woliny2!=1:
	[dyo,bpms]=DYfromOrbit(ListOfZeroDPPY,ListOfNonZeroDPPY,ListOfCOY,COcut)
	fDy.write('@ Q1 %le '+str(Q1)+'\n')
	fDy.write('@ Q2 %le '+str(Q2)+'\n')
	fDy.write('* NAME   POS    COUNT  DY     STDDY  MUYMDL\n')
	fDy.write('$ %s     %le    %le    %le    %le    %le\n')
	ALL=ListOfZeroDPPY+ListOfNonZeroDPPY
	for i in range(0,len(bpms)):
		bn1=upper(bpms[i][1])
		bns1=bpms[i][0]
		fDy.write('"'+bn1+'" '+str(bns1)+' '+str(len(ListOfNonZeroDPPY))+' '+str(dyo[bn1][0])+' '+str(dyo[bn1][1])+' '+str(MADTwiss.MUY[MADTwiss.indx[bn1]])+'\n' )

fDy.close()

#-------- Phase for non-zero DPP

k=0
for j in ListOfNonZeroDPPX:
	SingleFile=[]
	SingleFile.append(j)
	file1=outputpath+'getphasex_dpp_'+str(k+1)+'.out'
	fphDPP=open(file1,'w')
	fphDPP.write('@ MAD_FILE: %s "'+file0+'"'+'\n')
	fphDPP.write('@ FILE %s "')
	fphDPP.write(FileOfNonZeroDPPX[k]+' ')
	fphDPP.write('"'+'\n')
	fphDPP.write('@ Q1 %le '+str(Q1)+'\n')
	try:
		fphDPP.write('@ Q2 %le '+str(Q2)+'\n')
	except:
		fphDPP.write('@ Q2 %le '+'0.0'+'\n')
	plane='H'
	[phase,Q1DPP,MUX,bpms]=GetPhases(MADTwiss,SingleFile,plane,outputpath)
	fphDPP.write('@ Q1DPP %le '+str(Q1DPP)+'\n')
	fphDPP.write('* NAME   NAME2  POS1   POS2   COUNT  PHASE  STDPH  PHXMDL MUXMDL\n')
	fphDPP.write('$ %s     %s     %le    %le    %le    %le    %le    %le    %le\n')
	for i in range(0,len(bpms)-1):
		bn1=upper(bpms[i][1])
		bns1=bpms[i][0]
		phmdl=MADTwiss.MUX[MADTwiss.indx[bn2]]-MADTwiss.MUX[MADTwiss.indx[bn1]]
		fphDPP.write('"'+bn1+'" '+'"'+bn2+'" '+str(bns1)+' '+str(bns2)+' '+str(1)+' '+str(phase[bn1][0])+' '+str(phase[bn1][1])+' '+str(phmdl)+' '+str(MADTwiss.MUX[MADTwiss.indx[bn1]])+'\n' )
	fphDPP.close()
	k+=1


if woliny2!=1:
	k=0
	for j in ListOfNonZeroDPPY:
		SingleFile=[]
		SingleFile.append(j)
		file1=outputpath+'getphasey_dpp_'+str(k+1)+'.out'
		fphDPP=open(file1,'w')
		fphDPP.write('@ MAD_FILE %s "'+file0+'"'+'\n')
		fphDPP.write('@ FILE %s "')
		fphDPP.write(FileOfNonZeroDPPY[k]+' ')
		fphDPP.write('"'+'\n')
		fphDPP.write('@ Q1 %le '+str(Q1)+'\n')
		try:
			fphDPP.write('@ Q2 %le '+str(Q2)+'\n')
		except:
			fphDPP.write('@ Q2 %le '+'0.0'+'\n')
		plane='V'
		[phase,Q2DPP,MUY,bpms]=GetPhases(MADTwiss,SingleFile,plane,outputpath)
		fphDPP.write('@ Q2DPP %le '+str(Q2DPP)+'\n')
		fphDPP.write('* NAME   NAME2  POS1   POS2   COUNT  PHASE  STDPH  PHYMDL MUYMDL\n')
		fphDPP.write('$ %s     %s     %le    %le    %le    %le    %le    %le    %le\n')
		for i in range(0,len(bpms)-1):
			bn1=upper(bpms[i][1])
			bns1=bpms[i][0]
			phmdl=MADTwiss.MUY[MADTwiss.indx[bn2]]-MADTwiss.MUY[MADTwiss.indx[bn1]]
			fphDPP.write('"'+bn1+'" '+'"'+bn2+'" '+str(bns1)+' '+str(bns2)+' '+str(1)+' '+str(phase[bn1][0])+' '+str(phase[bn1][1])+' '+str(phmdl)+' '+str(MADTwiss.MUY[MADTwiss.indx[bn1]])+'\n' )
		fphDPP.close()
		k+=1

