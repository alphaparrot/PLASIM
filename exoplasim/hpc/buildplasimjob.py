import os
import numpy as np
import time
from batch_system import SUB, BATCHSCRIPT
from identity import USER
import glob

# Options:
#   noutput
#   pCO2     (ubars)
#   pressure
#   flux
#   gravity
#   radius
#   year
#   restart
#   ncarbon
#   volcanCO2
#   wmax
#   nglacier
#   glacelim
#   sidday   (hours)
#   solday   (hours)
#   sidyear  (days)
#   solyear  (days)
#   rotspd
#   obliq
#   eccen
#   vernlon
#   radius
#   snowmax
#   soilh2o
#   naqua
#   script
#   extra
#   nfixorb
#   nwpd     (writes per day)
#   months   (runtime)
#   days     (runtime)
#   steps    (runtime)
#   timestep (minutes/timestep)
#   runyears
#   fixedlon (longitude of fixed substellar point)
#   source
#   notify



def edit_namelist(home,filename,arg,val): 
  f=open(home+"/"+filename,"r")
  fnl=f.read().split('\n')
  f.close()
  found=False
  fnl1=fnl[1].split(' ')
  if '=' in fnl1:
    mode='EQ'
  else:
    mode='CM'
  #print fnl1
  item = fnl1[-1]
  if item=='':
    item = fnl1[-2]
  if item.strip()[-1]!=",":
    mode='EQ'
  
  for l in range(1,len(fnl)-2):
    fnl[l]=fnl[l].split(' ')
    #if '=' in fnl[l]:
      #mode='EQ'
    #else:
      #mode='CM'
    #print fnl[l][-1]
    #print fnl[l][-1].strip()
    #if fnl[l][-1].strip()[-1]!=",":
      #mode='EQ'
    if arg in fnl[l]:
      fnl[l]=['',arg,'','=','',str(val),'']
      found=True
    elif (arg+'=') in fnl[l]:
      tag = ','
      item = fnl[l][-1]
      if item=='':
        item = fnl[l][-2]
      if item.strip()[-1]!=',':
        tag = ''
      fnl[l]=['',arg+'=','',str(val),'',tag]
      found=True
    fnl[l]=' '.join(fnl[l])
  if not found:
    if mode=='EQ':
      fnl.insert(-3,' '+arg+' = '+val+' ')
    else:
      fnl.insert(-3,' '+arg+'= '+val+' ,')
  f=open(home+"/"+filename,"w")
  f.write('\n'.join(fnl))
  f.close() 
  
def edit_postnamelist(home,filename,arg,val):
  with open(home+"/"+filename,"r") as f:
      pnl = f.read().split('\n')
  flag=False
  pnl = [y for y in pnl if y!='']
  for n in range(len(pnl)):
      if pnl[n].split('=')[0].strip()==arg:
          pnl[n]=arg+"="+val
          flag=True
          break
  if not flag:
      pnl.append(arg+'='+val)
  pnl.append('')
  with open(home+"/"+filename,"w") as f:
      f.write('\n'.join(pnl))


def prep(job):

  sig=job.name
  home=job.home
  args=job.args
  fields=job.fields
  
  workdir = home
  
  if "source" in job.parameters:
    source = job.parameters["source"]
  else:
    source = "clean"

  if "westeros" in job.parameters:
    source = "westeros"
    
  if "source" in job.parameters:
    source = job.parameters["source"]
  
  print("Setting stuff for job "+sig+" in "+workdir)
  print("Arguments are:",fields[:])
  
  notify = 'ae'
  scriptfile = "run.sh"
  
  
  #PlaSim
  
  p0 = 1010670.0
  
  #os.system("rm "+workdir+"/*.sh")
  #os.system("mkdir plasim/errorlogs/")
  #os.system("cp "+workdir+"/*.e* plasim/errorlogs/")
  #os.system("rm "+workdir+"/*")
  print("copying files.....")
  print("cp "+source+"/* "+workdir+"/")
  os.system("cp "+source+"/* "+workdir+"/")
  print(("rm "+workdir+"/plasim_restart"))
  os.system("rm "+workdir+"/plasim_restart")
  print(("cp "+scriptfile+" "+workdir+"/"))
  os.system("cp "+scriptfile+" "+workdir+"/")
  print(("cp synthoutput.py "+workdir+"/"))
  os.system("cp synthoutput.py "+workdir+"/")
  print(("cp jobdefs.py "+workdir+"/"))
  os.system("cp jobdefs.py "+workdir+"/")
  print(("cp identity.py "+workdir+"/"))
  os.system("cp identity.py "+workdir+"/")
  
  #if "cleanup" in job.parameters:
    #cleanup = job.parameters["cleanup"]
  #else:
    #cleanup = 'release-plasim.py'
  #os.system("cp "+cleanup+" "+workdir+"/")
  
  tag = 'all'
  
  keeprs = False
  monitor = False
  yearini = 0
  weathrestart = False
  nlevs = 10
  nsn = False
  nwesteros = False
  
  for name in job.fields[2:]:
    val = job.parameters[name]
    found=False    
        
    if name=="noutput":
      edit_namelist(home,"plasim_namelist","NOUTPUT",val)  
      found=True
      
    if name=="flux":
      edit_namelist(home,"planet_namelist","GSOL0",val) 
      found=True
      
    if name=="startemp":
      edit_namelist(home,"radmod_namelist","NSTARTEMP","1")
      edit_namelist(home,"radmod_namelist","STARBBTEMP",val)
      found=True
      
    if name=="pCO2":
      found=True
      gotpress=False
      if "pN2" in fields:
        p0 = float(job.parameters["pN2"])
        p0 *= 1.0e6
        p0 += float(val)
        p0 *= 1.0e-6
        edit_namelist(home,"plasim_namelist","PSURF",str(p0*1.0e5))
        gotpress=True
      if not gotpress:
        p0 += float(val)
        p0 *= 1.0e-6
        edit_namelist(home,"plasim_namelist","PSURF",str(p0*1.0e5))
    
      pCO2 = float(val)/(p0*1.0e6)*1.0e6 #ppmv
      edit_namelist(home,"radmod_namelist","CO2",str(pCO2))      
      
    if name=="pN2":
      found=True
      
      p0 = float(val)*1.0e6
      if "pCO2" in fields:
          p0 += float(job.parameters["pCO2"])
          edit_namelist(home,"radmod_namelist","CO2",str(float(job.parameters["pCO2"])/p0*1.0e6))
      edit_namelist(home,"plasim_namelist","PSURF",str(p0*0.1))
       
    if name=="alloutput":
      found=True
      if int(job.parameters["alloutput"])==0:
          tag=''
      
    if name=="keeprestart":
      found=True
      if int(job.parameters["keeprestart"])==1:
          keeprs = True
        
    if name=="monitor":
      found=True
      if int(job.parameters["monitor"])==1:
          monitor = True
      
    if name=="year": #In days
      found=True
      edit_namelist(home,"plasim_namelist","N_DAYS_PER_YEAR",val) 
             
    if name=="sidyear": #In days
      found=True
      year = float(val)*24.0*3600.0
      val = str(year)
      edit_namelist(home,"planet_namelist","SIDEREAL_YEAR",val) 
             
    if name=="solyear": #In days
      found=True
      year = float(val)*24.0*3600.0
      val = str(year)
      edit_namelist(home,"planet_namelist","TROPICAL_YEAR",val) 
            
    if name=="sidday": #In hours
      found=True
      day = float(val)*3600.0
      val = str(day)
      edit_namelist(home,"planet_namelist","SIDEREAL_DAY",val) 
             
    if name=="solday": #In hours
      found=True
      day = float(val)*3600.0
      val = str(day)
      edit_namelist(home,"planet_namelist","SOLAR_DAY",val)
      
    if name=="nlevs":
      found=True
      nlevs = int(val)
      
    if name=="vtype":
      found=True
      edit_namelist(home,"plasim_namelist","NEQSIG",val)
     
    if name=="rotspd":
      found=True
      edit_namelist(home,"planet_namelist","ROTSPD",val)
      
    if name=="lockedyear": #Year length in days for a tidally-locked planet_namelist, and lon0.
      found=True
      val0 = val.split('/')[0]
      val1 = val.split('/')[1]
      edit_namelist(home,"planet_namelist","ROTSPD",str(1.0/float(val0)))
      #edit_namelist(home,"planet_namelist","SIDEREAL_DAY","86400.0")
      #edit_namelist(home,"planet_namelist","SOLAR_DAY","86400.0")
      #edit_namelist(home,"planet_namelist","TROPICAL_YEAR","31536000.0")
      #edit_namelist(home,"planet_namelist","SIDEREAL_YEAR","31536000.0")
      edit_namelist(home,"radmod_namelist","NFIXED","1")
      edit_namelist(home,"radmod_namelist","FIXEDLON",val1)
      
    if name=="restart":
      found=True
      if val!="none":
        os.system("cp hopper/"+val+" "+workdir+"/plasim_restart")
      else:
        os.system("rm "+workdir+"/plasim_restart")
        
    if name=="hweathering":
      found=True
      os.system("cp hopper/"+val+" "+workdir+"/")
      wfile = val
      weathrestart = True
      
    if name=="year_init":
      found=True
      yearini = int(val)      
      
    if name=="pressurebroaden":
      found=True
      edit_namelist(home,"radmod_namelist","NPBROADEN",val)
     
    if name=="gravity":
      found=True
      edit_namelist(home,"planet_namelist","GA",val) 
      postnls = glob.glob(home+"/*.nl")
      for postf in postnls:
        pf = postf.split("/")[-1]
        edit_postnamelist(home,pf,"gravity",val)
       
    if name=="radius":
      found=True
      edit_namelist(home,"planet_namelist","PLARAD",str(float(val)*6371220.0))
      postnls = glob.glob(home+"/*.nl")
      for postf in postnls:
        pf = postf.split("/")[-1]
        edit_postnamelist(home,pf,"radius",str(float(val)*6371220.0))
     
    if name=="eccen":
      found=True
      edit_namelist(home,"planet_namelist","ECCEN",val) 
     
    if name=="obliq":
      found=True
      edit_namelist(home,"planet_namelist","OBLIQ",val) 
       
    if name=="vernlon":
      found=True
      edit_namelist(home,"planet_namelist","MVELP",val) 
           
    if name=="nfixorb":
      found=True
      edit_namelist(home,"planet_namelist","NFIXORB",val) 
      
    if name=="oroscale":
      found=True
      edit_namelist(home,"landmod_namelist","OROSCALE",val)
      edit_namelist(home,"glacier_namelist","NGLACIER",'1') 
       
    if name=="nglacier":
      found=True
      edit_namelist(home,"glacier_namelist","NGLACIER",val) 
      
    if name=="glacelim":
      found=True
      edit_namelist(home,"glacier_namelist","GLACELIM",val) 
      
    if name=="icesheets":
      found=True
      os.system("rm "+workdir+"/*174.sra "+
                   ""+workdir+"/*1740.sra "+
                   ""+workdir+"/*210.sra "+
                   ""+workdir+"/*232.sra")
      edit_namelist(home,"glacier_namelist","ICESHEETH",val)
    
    if name=="lowerANTGRN":
      found=True
      if int(val)==1:
        os.system("cp plasim/glacsra/*.sra "+workdir+"/")
    
    if name=="ncarbon":
      found=True
      edit_namelist(home,"carbonmod_namelist","NCARBON",val) 
      
    if name=="co2evolve":
      found=True
      edit_namelist(home,"carbonmod_namelist","NCO2EVOLVE",val)
      
    if name=="filtertype":
      found=True
      if source == "gibbs":
        edit_namelist(home,"plasim_namelist","NSPFILTER",val)
        
    if name=="filtervars":
      found=True
      if source == "gibbs":
        vals = val.split(',')
        if "q" in vals:
          edit_namelist(home,"plasim_namelist","FILTERQ","1")
        else:
          edit_namelist(home,"plasim_namelist","FILTERQ","0")
        if "d" in vals:
          edit_namelist(home,"plasim_namelist","FILTERD","1")
        else:
          edit_namelist(home,"plasim_namelist","FILTERD","0")
        if "z" in vals:
          edit_namelist(home,"plasim_namelist","FILTERZ","1")
        else:
          edit_namelist(home,"plasim_namelist","FILTERZ","0")
        if "t" in vals:
          edit_namelist(home,"plasim_namelist","FILTERT","1")
        else:
          edit_namelist(home,"plasim_namelist","FILTERT","0")
          
    if name=="filterpower":
      found=True
      if source=="gibbs":
        edit_namelist(home,"plasim_namelist","NFILTEREXP",val)
        
    if name=="filterkappa":
      found=True
      if source=="gibbs":
        edit_namelist(home,"plasim_namelist","FILTERKAPPA",val)
      
    if name=="filtertime":
      found=True
      if source=="gibbs":
        edit_namelist(home,"plasim_namelist","FILTERTIME",val)
        
    if name=="filterLHN0":
      found=True
      if source=="gibbs":
        edit_namelist(home,"plasim_namelist","LANDHOSKN0",val)
        
    if name=="nsupply":
      found=True
      edit_namelist(home,"carbonmod_namelist","NSUPPLY",val) 
      
    if name=="volcanCO2":
      found=True
      edit_namelist(home,"carbonmod_namelist","VOLCANCO2",val) 
      
    if name=="wmax":
      found=True
      edit_namelist(home,"carbonmod_namelist","WMAX",val) 
      
    if name=="snowmax":
      found=True
      edit_namelist(home,"landmod_namelist","DSMAX",val)
      
    if name=="soilalbedo":
      found=True
      os.system("rm "+workdir+"/*0174.sra")
      edit_namelist(home,"landmod_namelist","ALBLAND",val)
      #edit_namelist(home,"landmod_namelist","NEWSURF","2") #Ignore surface files
      
    if name=="wetsoil":
      found=True
      edit_namelist(home,"landmod_namelist","NWETSOIL",val)
      
    if name=="soilh2o":
      found=True
      edit_namelist(home,"landmod_namelist","WSMAX",val) 
      
    if name=="naqua":
      found=True
      edit_namelist(home,"plasim_namelist","NAQUA",val)
      os.system("rm "+workdir+"/*.sra")
      
    if name=="ndesert":
      found=True
      edit_namelist(home,"plasim_namelist","NDESERT",val)
      edit_namelist(home,"landmod_namelist","NWATCINI","1")
      edit_namelist(home,"landmod_namelist","DWATCINI","0.0")
      os.system("rm "+workdir+"/*.sra")
      
    if name=="drycore":
      found=True
      if int(val)==1:
        #edit_namelist(home,"plasim_namelist","NQSPEC","0") #Turn off water advection
        edit_namelist(home,"fluxmod_namelist","NEVAP","0") #Turn off evaporation
      
    if name=="soilheat": # 0.001 J/m^3/K = 1 J/kg/K. Ocean = 4180 J/kg/K = 4.18e6 J/m^3/K
      found=True
      edit_namelist(home,"landmod_namelist","SOILCAP",val)
      
    if name=="soildepth":
      found=True
      depth = np.array([0.4,0.8,1.6,3.2,6.4]) #meters
      depth *= float(val)
      strvals = []
      for d in depth:
          strvals.append(str(d))
      edit_namelist(home,"landmod_namelist","DSOILZ",",".join(strvals))
      
    if name=="nwpd":
      found=True
      edit_namelist(home,"plasim_namelist","NWPD",val)
      
    if name=="months":
      found=True
      edit_namelist(home,"plasim_namelist","N_RUN_MONTHS",val)
      
    if name=="rhum_c":
      found=True
      edit_namelist(home,"rainmod_namelist","RCRITMOD",val)
      
    if name=="rhum_m":
      found=True
      edit_namelist(home,"rainmod_namelist","RCRITSLOPE",val)
      #if negative, cloud formation will be suppressed at high altitudes
      #if positive, cloud formation will be encouraged at high altitudes
      
    if name=="rcrit":
      found=True
      exec("critlevs="+val)
      edit_namelist(home,"rainmod_namelist","RCRIT",','.join(critlevs.astype(str)))
      
    if name=="days":
      found=True
      edit_namelist(home,"plasim_namelist","N_RUN_DAYS",val)
      
    if name=="steps":
      found=True
      edit_namelist(home,"plasim_namelist","N_RUN_STEPS",val)
      
    if name=="o3":
      found=True
      edit_namelist(home,"radmod_namelist","NO3",val)
      
    if name=="ptop":
      found=True
      edit_namelist(home,"plasim_namelist","NEQSIG","3")
      edit_namelist(home,"plasim_namelist","PTOP",str(float(val)*100.0))
      
    if name=="timestep":
      found=True
      edit_namelist(home,"plasim_namelist","MPSTEP",val)
      edit_namelist(home,"plasim_namelist","NSTPW",str(7200/int(float(val))))
      edit_namelist(home,"plasim_namelist","NSNAPSHOT","1")
      edit_namelist(home,"plasim_namelist","NSTPS",str(21600/int(float(val))))
      nsn = True
      
    if name=="rayleigh":
      found=True
      edit_namelist(home,"radmod_namelist","NEWRSC",val)
      
    if name=="script":
      found=True
      scriptfile=val
      os.system("cp "+val+" "+workdir+"/")
      
    if name=="postprocessor":
      found=True
      os.system("cp "+source+"/"+val+" "+workdir+"/example.nl")
      
    if name=="notify":
      found=True
      notify = val

      
    if name=="columnmode":
      found=True
      parts = val.split("|")
      if "static" in parts:
          edit_namelist(home,"plasim_namelist","NADV","0")
      if "clear" in parts:
          edit_namelist(home,"radmod_namelist","NCLOUDS","0")
          edit_namelist(home,"radmod_namelist","ACLLWR","0.0")
      
    if name=="snapshots":
      found=True
      edit_namelist(home,"plasim_namelist","NSNAPSHOT","1")
      edit_namelist(home,"plasim_namelist","NSTPS",val)
      nsn = True
      
    if name=="extra":
      found=True
      os.system("cp -r "+val+" "+workdir+"/")
      
    if name=="runyears":
      found=True
      f=open(""+workdir+"/most_plasim_run","r")
      fnl=f.read().split('\n')
      f.close()
      for l in range(0,len(fnl)-2):
        line=fnl[l].split("=")
        if len(line)>0:
            if line[0]=="YEARS":
                fnl[l] = "YEARS="+val
      fnl='\n'.join(fnl)
      f=open(""+workdir+"/most_plasim_run","w")
      f.write(fnl)
      f.close()
      
      
    if name=="fixedlon":
      found=True
      edit_namelist(home,"radmod_namelist","NFIXED","1")
      edit_namelist(home,"radmod_namelist","FIXEDLON",val)
      
    if name=="source":
      found=True #We already took care of it
      
    if name=='cleanup':
      found=True #We already took care of it
      
    if name=="westeros":
      found=True
      edit_namelist(home,"plasim_namelist","NWESTEROS",val)
      edit_namelist(home,"planet_namelist","NFIXORB","1") 
      if "runyears" in job.parameters:
        nrunyears = int(job.parameters["runyears"])
      else:
        nrunyears = 100
      nwesteros=True
      
    if name=="binarystar":
      found=True
      edit_namelist(home,"radmod_namelist","NDOUBLESTAR",val)
      
    if name=="flux2":
      found=True
      edit_namelist(home,"planet_namelist","GSOL1",val)
      
    if name=="initialmzv":
      found=True
      parts = val.split('/')
      manom0 = parts[0]
      x0 = parts[1]
      v0 = parts[2]
      edit_namelist(home,"planet_namelist","MEANANOM0",manom0)
      edit_namelist(home,"planet_namelist","ZWZZ",x0)
      edit_namelist(home,"planet_namelist","ZWVV",v0)
      
    if name=="semimajor":
      found=True
      edit_namelist(home,"planet_namelist","SEMIMAJOR",val)
      
    if name=="maxflux":
      found=True
      edit_namelist(home,"radmod_namelist","SOLMAX",val)
      
    if not found: #Catchall for options we didn't include
      found=True
      args = name.split('@')
      if len(args)>1:
        namelist=args[1]
        name=args[0]
        edit_namelist(home,namelist,name,val)
      else:
        print("Unknown parameter "+name+"! Submit unsupported parameters as KEY@NAMELIST in the header!")
      
  print("Arguments set")
  
  histargs = ''
  if weathrestart:
      histargs = wfile+" "+str(yearini)
  if nwesteros:
      histargs = str(nrunyears)
  
  # You may have to change this part
  jobscript =(BATCHSCRIPT(job,notify)+
              "rm keepgoing                                                     \n"+
              "mkdir /mnt/node_scratch/"+USER+"/"+home+"            \n")
  if nsn:
      jobscript+=("mkdir /mnt/node_scratch/"+USER+"/"+home+"/snapshots         \n"+
                  "tar cvzf stuff.tar.gz --exclude='*_OUT*' --exclude='*_REST*' --exclude='*.nc' --exclude='snapshots/' ./* \n")
  jobscript +=("rsync -avzhur stuff.tar.gz /mnt/node_scratch/"+USER+"/"+home+"/         \n"+
              "rm -rf stuff.tar.gz                     \n"+
              "cd /mnt/node_scratch/"+USER+"/"+home+"/              \n"+
              "tar xvzf stuff.tar.gz                   \n"+
              "rm stuff.tar.gz          \n"+
              "./"+scriptfile+" "+str(job.ncores)+" "+str(nlevs)+" "+histargs+"   \n"+
              "tar cvzf stuff.tar.gz *                                          \n"+
              "rsync -avzhur stuff.tar.gz $PBS_O_WORKDIR/                                          \n"+
              "rm -rf *                                                         \n"+
              "cd $PBS_O_WORKDIR                                                \n"+
              "tar xvzf stuff.tar.gz                                \n"+
              "rm stuff.tar.gz          \n"+
              "if [ -e keepgoing ]                                              \n"+
              "then                                                            \n"+
              "      qsub runplasim                                             \n"+
              "else        \n")
  #if keeprs:
      #jobscript+= "cp plasim_restart ../output/"+job.name+"_restart            \n"
  #if monitor:
      #jobscript+= "python monitor_balance.py                                   \n"
      
  jobscript += ("   python synthoutput.py MOST 1                                      \n"+
                "fi \n")
  
  rs = open(workdir+"/runplasim","w")
  rs.write(jobscript)
  rs.close()
  
def submit(job):
    
  os.system("cd "+job.home+" && "+SUB+" runplasim && cd "+job.top)
  time.sleep(1.0)
  tag = job.getID()
  job.write()