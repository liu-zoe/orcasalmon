## Project Name: Orcasound Salmon
### Program Name: peakmod.R
### Purpose: To make a dash board for the Chinook salmon data
### Date Created: Sept 17th 2023
### Credit: code heavily adapting from https://github.com/AileneKane/srkwphen

library(dplyr)
library(mgcv)
library(scales)
library(RColorBrewer)
library(scales)
library(matrixStats)
library(plotfunctions)
library(igraph)
library(brms)
library(rstan)

proj_folder="~/orcasalmon/"
setwd(paste(proj_folder,"data/peak/", sep=""))

srkwpres<-read.csv(paste(proj_folder,"data/srkw_presence.csv", sep=""))
albiondat<-read.csv(paste(proj_folder,"data/albion_long.csv", sep=""))


###------SRKW-------###
#Fit multilevel bernouli gams with presence of SRKWs as the response, fit using brms package
srkwpres$yr<-srkwpres$year
srkwpres$year<-as.factor(srkwpres$year)

m2 <- brm(AllSRpres ~ s(day_of_year) + (day_of_year|year),
          data=srkwpres,
          family =bernoulli(), cores = 2,
          iter = 4000, warmup = 1000, thin = 10,
          control = list(adapt_delta = 0.99, max_treedepth=15))
#save(m2, file="srkw.brms.Rda")
#or, if already saved:
#load("srkw.brms.Rda")

j2 <- brm(Jpres ~ s(day_of_year) + (day_of_year|year),
          data=srkwpres,
          family =bernoulli(), cores = 2,
          iter = 4000, warmup = 1000, thin = 10,
          control = list(adapt_delta = 0.99, max_treedepth=15))

save(j2, file="j.brms.Rda")
# or, if already saved:
# load("j.brms.Rda")

k2 <- brm(Kpres ~ s(day_of_year) + (day_of_year|year),
          data=srkwpres,
          family =bernoulli(), cores = 2,
          iter = 4000, warmup = 1000, thin = 10,
          control = list(adapt_delta = 0.99, max_treedepth=15))
save(k2, file="k.brms.Rda")
# or, if already saved:
# load("k.brms.Rda")

l2 <- brm(Lpres ~ s(day_of_year) + (day_of_year|year),
          data=srkwpres,
          family =bernoulli(), chains = 2,
          iter = 4000, warmup = 1000, thin = 10,
          control = list(adapt_delta = 0.99, max_treedepth=15 ))
save(l2, file="l.brms.Rda")
# or, if already saved:
# load("l.brms.Rda")

prob.occ.95<-cbind(srkwpres$yr, srkwpres$year,srkwpres$day_of_year,
                   fitted(m2),fitted(j2),fitted(k2),fitted(l2)
)

colnames(prob.occ.95)<-c("yr","year","doy", 
                         paste("SRprob",colnames(fitted(m2)),sep="."),
                         paste("Jprob",colnames(fitted(j2)),sep="."),
                         paste("Kprob",colnames(fitted(k2)),sep="."),
                         paste("Lprob",colnames(fitted(l2)),sep=".")
)
prob.occ.90<-cbind(srkwpres$yr, srkwpres$year,srkwpres$day_of_year,
                   fitted(m2,probs=c(0.05,0.95)),
                   fitted(j2,probs=c(0.05,0.95)),
                   fitted(k2,probs=c(0.05,0.95)),
                   fitted(l2,probs=c(0.05,0.95))
)

colnames(prob.occ.90)<-c("yr","year","doy", paste("SRprob",colnames(fitted(m2,probs=c(0.05,0.95))),sep="."),
                         paste("Jprob",colnames(fitted(j2,probs=c(0.05,0.95))),sep="."),
                         paste("Kprob",colnames(fitted(k2,probs=c(0.05,0.95))),sep="."),
                         paste("Lprob",colnames(fitted(l2,probs=c(0.05,0.95))),sep=".")
)
prob.occ.50<-cbind(srkwpres$yr, srkwpres$year,srkwpres$day_of_year,
                   fitted(m2,probs=c(0.25,0.75)),
                   fitted(j2,probs=c(0.25,0.75)),
                   fitted(k2,probs=c(0.25,0.75)),
                   fitted(l2,probs=c(0.25,0.75))
)

colnames(prob.occ.50)<-c("yr","year","doy", paste("SRprob",colnames(fitted(m2,probs=c(0.25,0.75))),sep="."),
                         paste("Jprob",colnames(fitted(j2,probs=c(0.25,0.75))),sep="."),
                         paste("Kprob",colnames(fitted(k2,probs=c(0.25,0.75))),sep="."),
                         paste("Lprob",colnames(fitted(l2,probs=c(0.25,0.75))),sep=".")
)

prob.occ.75<-cbind(srkwpres$yr, srkwpres$year,srkwpres$day_of_year,
                   fitted(m2,probs=c(0.125,0.875)),
                   fitted(j2,probs=c(0.125,0.875)),
                   fitted(k2,probs=c(0.125,0.875)),
                   fitted(l2,probs=c(0.125,0.875))
)

colnames(prob.occ.75)<-c("yr","year","doy", paste("SRprob",colnames(fitted(m2,probs=c(0.125,0.875))),sep="."),
                         paste("Jprob",colnames(fitted(j2,probs=c(0.125,0.875))),sep="."),
                         paste("Kprob",colnames(fitted(k2,probs=c(0.125,0.875))),sep="."),
                         paste("Lprob",colnames(fitted(l2,probs=c(0.125,0.875))),sep=".")
)

#Save model results
write.csv(prob.occ.95,"srkw_prob.occ.95.csv", row.names = FALSE)
write.csv(prob.occ.90,"srkw_prob.occ.90.csv", row.names = FALSE)
write.csv(prob.occ.50,"srkw_prob.occ.50.csv", row.names = FALSE)
write.csv(prob.occ.75,"srkw_prob.occ.75.csv", row.names = FALSE)



###------Chinook-------###
# Prep data for models 
albiondat$calDay<-as.integer(as.character(albiondat$calDay))
dat<-albiondat
season="allyear"#choices are "springsum" or "fall" or "allyear
head(dat)

dat<-dat[dat$year>=1990,]
allyears<-unique(dat$year)
sumalb<-tapply(dat$cpue,list(dat$year),sum)

#select only spring and summer
datsp<-dat[dat$calDay<213,]
cpuesptot<-aggregate(datsp$cpue,list(datsp$year),sum, na.rm= TRUE)
cpuetot<-aggregate(dat$cpue,list(dat$year),sum, na.rm= TRUE)

colnames(cpuetot)<-c("year","cpuetot")
colnames(cpuesptot)<-c("year","cpuesptot")

cpuetot<-cpuetot[cpuetot$year<2018,]
cpuesptot<-cpuesptot[cpuesptot$year<2018,]

#now fit splines suggested analysis
dat$effort<-as.numeric(dat$effort)
dat$year2<-as.factor(dat$year)
dat$calDay<-as.numeric(dat$calDay)
dat$catch<-as.numeric(dat$catch)
dat$cpue1<-dat$cpue+.001
dat$logcpue<-log(dat$cpue1)

#Focal model is cm2:
cm2 <- brm(logcpue~ s(calDay) + (calDay|year2),
          data=dat, chains = 2,
          iter = 6000, warmup = 1000, thin = 10,
          control = list(adapt_delta = 0.99, max_treedepth=15))

plot(cm2)

save(cm2, file="albionchibrms.Rda")

#if already saved,
#load("analyses/output/albionchibrms.Rda")


albgam<-as.data.frame(cbind(dat$year,dat$calDay,fitted(cm2),fitted(cm2,probs=c(0.05,0.95)),fitted(cm2,probs=c(0.25,0.75))))
colnames(albgam)[1:3]<-c("yr","doy", "logcpue.est")
albgam$estcpue<-exp(as.numeric(albgam$logcpue.est))
colnames(albgam)[15]<-c("cpue.est")

#compare fitted to estimated cpue
sumest<-tapply(albgam$cpue.est,list(albgam$year),sum)

write.csv(albgam,"albionbrmsests.csv", row.names = FALSE)


allyears<-unique(albgam$year)

seasons<-c("springsum","fall","allyear")
years<-c()
allseasons<-c()
firstobsdate<-c()
lastobsdate<-c()
midobsdate<-c()
peakobsdate<-c()
peakobsdate.sp<-c()
peakobsdate.fa<-c()
alltotal<-c()
alltotal.sp<-c()
alltotal.fa<-c()

for(y in allyears){
  print(y)
  datyr<-albgam[albgam$year==y,]
  if (dim(datyr)[1]<=1){
    first<-last<-mid<-peak<-NA
    total<-NA
  }
  if (dim(datyr)[1]>0){
    cpue<-as.numeric(datyr$cpue.est)
    cpuesp<-datyr$cpue.est[datyr$doy<213]#213= aug 1
    cpuefa<-datyr$cpue.est[datyr$doy>=213]
    #plot(datyr$doy,count, pch=21, bg="gray", main=paste(y))
    #if(y==min(allyears)){mtext(paste(sites[i], species[p]),side=3, line=3)}
    datdoy<-as.numeric(datyr$doy)
    datdoysp<-as.numeric(datyr$doy[datyr$doy<213])
    datdoyfa<-as.numeric(datyr$doy[datyr$doy>=213])
    first<-min(datdoy[which(cpue>0.005)])
    last<-max(datdoy[which(cpue>0.005)])
    total<-sum(cpue,na.rm=TRUE)
    totalsp<-sum(cpuesp,na.rm=TRUE)
    totalfa<-sum(cpuefa,na.rm=TRUE)
    
    mid<-datdoy[min(which(cumsum(cpue)>(total/2)))]#date at which half of fish have arrived
    peak<-min(datdoy[which(cpue==max(cpue, na.rm=TRUE))])#date of peak number of fish observed, if multiple dates with same number, choose first of these
    peaksp<-min(datdoysp[which(cpuesp==max(cpuesp, na.rm=TRUE))])#date of peak number of fish observed, if multiple dates with same number, choose first of these
    peakfa<-min(datdoyfa[which(cpuefa==max(cpuefa, na.rm=TRUE))])#date of peak number of fish observed, if multiple dates with same number, choose first of these
    print(peak)
  }
  print(y);print(first);print(last);print(total); print(mid)
  years<-c(years,y)
  #allseasons<-c(allseasons,season[s])
  firstobsdate<-c(firstobsdate,first)
  lastobsdate<-c(lastobsdate,last)
  midobsdate<-c(midobsdate,mid)
  peakobsdate<-c(peakobsdate,peak)
  peakobsdate.fa<-c(peakobsdate.fa,peakfa)
  peakobsdate.sp<-c(peakobsdate.sp,peaksp)
  alltotal<-c(alltotal,total)
  alltotal.fa<-c(alltotal.fa,totalfa)
  alltotal.sp<-c(alltotal.sp,totalsp)
}

#Save a file with these estimates in it
albchiphenest<-cbind("ck","albion",years,firstobsdate,lastobsdate,peakobsdate,peakobsdate.sp,peakobsdate.fa,midobsdate,alltotal,alltotal.sp,alltotal.fa)

colnames(albchiphenest)[1:3]<-c("sp","site","year")

#Now estimate trends in phenology
#restrict to time frame consistent with orcas
albchiphenest<-as.data.frame(albchiphenest)
albchiphenest<-albchiphenest[albchiphenest$year>1995,]
albchiphenest$year<-as.numeric(albchiphenest$year)
albchiphenest$firstobsdate<-as.numeric(albchiphenest$firstobsdate)
albchiphenest$peakobsdate<-as.numeric(albchiphenest$peakobsdate)
albchiphenest$lastobsdate
albchiphenest<-albchiphenest[albchiphenest$year<2018,]
firstmod<-lm(firstobsdate~year, data=albchiphenest)
firstcoefs<-coef(firstmod)
firstcoefs.50ci<-confint(firstmod,level = 0.50)
firstcoefs.75ci<-confint(firstmod,level = 0.75)
firstcoefs.95ci<-confint(firstmod,level = 0.95)

lastmod<-lm(lastobsdate~year, data=albchiphenest)
lastcoefs<-coef(lastmod)
lastcoefs.50ci<-confint(lastmod,level = 0.50)
lastcoefs.75ci<-confint(lastmod,level = 0.75)
lastcoefs.95ci<-confint(lastmod,level = 0.95)
peakmod<-lm(peakobsdate~year, data=albchiphenest)
peakcoefs<-coef(peakmod)
peakcoefs.50ci<-confint(peakmod,level = 0.50)
peakcoefs.75ci<-confint(peakmod,level = 0.75)
peakcoefs.95ci<-confint(peakmod,level = 0.95)
abundmod<-lm(alltotal~year, data=albchiphenest)
abundcoefs<-coef(abundmod)
abundcoefs.50ci<-confint(abundmod,level = 0.50)
abundcoefs.75ci<-confint(abundmod,level = 0.75)
abundcoefs.95ci<-confint(abundmod,level = 0.95)

allmodsums<-c(round(firstcoefs, digits=3),round(lastcoefs, digits=3),round(peakcoefs, digits=3))
allmodsums.50ci<-rbind(round(firstcoefs.50ci, digits=3),round(lastcoefs.50ci, digits=3),round(peakcoefs.50ci, digits=3))
allmodsums.75ci<-rbind(round(firstcoefs.75ci, digits=3),round(lastcoefs.75ci, digits=3),round(peakcoefs.75ci, digits=3))

allmodsums.95ci<-rbind(round(firstcoefs.95ci, digits=3),round(lastcoefs.95ci, digits=3),round(peakcoefs.95ci, digits=3))
phen<-c("first","first","last","last","peak","peak")
sums<-cbind("ck","albion",phen,allmodsums,allmodsums.50ci,allmodsums.75ci,allmodsums.95ci)
colnames(sums)<-c("sp","site","phen","est","ci25","ci75","ci12.5","ci87.5","ci2.5","ci97.5")

