#!/usr/bin/env python
# -*- coding: UTF-8 -*-
# chmod 777 
#######################################################
#GEO 410 - Johannes Senf & Marcus Engelke - 31.08.2022#
#######################################################

#Import der Module
import os  
import sys  
import glob
import zipfile
import numpy as np
import py_gamma as pg  #Gamma Befehle
import datetime as dt  #Schleife für das Datum 
import shutil  #Ordner und Daten verschieben, löschen usw.
from datetime import datetime, timedelta  #Schleife für das Datum

def walk_days(start_date, end_date,x,liste,path,out,srtm_location):  #Funktion zur Bestimmung der Kohärenz zwischen den Datumspaaren 
   
    if start_date <= end_date:  #so lange Datum <= als das Endatum ist ist die Funktion aktiv
        date=start_date.strftime("%Y%m%d")
        
        date=str(date)   #Umwandlung aktuelles Datum in einen String (für Liste usw.)
        liste.append(date)  #Neues Datum wird der Datumsliste angehängt
        
        print(start_date.strftime("%Y%m%d"))   #aktuelles Datum wird ausgegeben
         
        # Fehlendes Datum
        if date == '20171020':  #Wenn 20.10.2017 erreicht wird. wird dieses übersprungen und der letzte Eintrag (20.10.2017) aus der Datumsliste entfernt
            liste.pop()
            next_date = start_date + timedelta(days=6)  #6 Tage weiter im Datum
            x=x  #x = x, weil das fehlende Datum nicht in die Liste eingeht
            walk_days(next_date, end_date,x,liste,path,out,srtm_location)  
        
        #Auswahl des entzippten Sentinels Ordner für das jeweilige Datum
        #Auswahl der benötigten Daten innerhalb des Ordners 
        product=glob.glob( path + '/*'+date+'*SAFE')[0]  
        slc=glob.glob( product + '/measurement/*iw2*vv*tiff')[0]  
        ann=glob.glob( product + '/annotation/*iw2*vv*xml')[0]
        cal=glob.glob( product + '/annotation/calibration/cal*iw2*vv*xml')[0]
        noise=glob.glob( product + '/annotation/calibration/noi*iw2*vv*xml')[0]
        
        #Bestimmung des Arbeitsverzeichnisses (=out Pfad)
        wdir=out  
        os.chdir(wdir)
        
        #Erstellung des temporären Ordners für Zwischenergebnisse bzw. Überprüfung, ob dieser schon erstellt wurde
        dir = os.path.join(out+'Temp')
        if not os.path.exists(dir):
            os.mkdir(dir)
        
        #Bestimmung Arbeitsverzeichnis (temporärer Ordner)    
        wdir=os.path.join(out+'Temp/')
        os.chdir(wdir)
        
        # Startdatum und Referenzaufnahme für Geocodierung und Koregistrierung   
        if date == '20170105':
            
            #Erstellung des individuellen Datumsordners für Produkte des Datums bzw. Überprüfung, ob dieser schon erstellt wurde
            dir = os.path.join(out,date)
            if not os.path.exists(dir):
                os.mkdir(dir)
            
            
            #Erstellung SLC
            slcpar_out=os.path.join(out,date+'/'+date+'_slc.par')
            slc_out=os.path.join(out,date+'/'+date+'_slc')
            tops_out=os.path.join(out,date+'/'+date+'_tops.par')
            pg.par_S1_SLC(slc, ann, cal, noise, slcpar_out, slc_out, tops_out)
            
            
            #Erstellung SLC_tab
            SLC_tab=os.path.join(out,date+'/'+date+'_tab')
            tab_arr=[slc_out,slcpar_out,tops_out]
            pg.write_tab(tab_arr, SLC_tab)
            
            
            #Range u Azimuth festlegen
            ml_rg=8
            ml_az=2
            
            
            #Output SLC mit gewählten Bursts
            rslc_out=os.path.join(out,date+'/'+date+'_rslc')
            rslc_par_out=os.path.join(out,date+'/'+date+'_rslc.par')
            rslc_tops_out=os.path.join(out,date+'/'+date+'_rslc_tops.par')
            
            #Erstellung Tab Datei für den Burst Output
            RSLC_tab=os.path.join(out,date+'/'+date+'_tab_r')
            tab_arr=[rslc_out,rslc_par_out,rslc_tops_out]
            pg.write_tab(tab_arr, RSLC_tab)
            
            
            burst_tab=os.path.join(out,date+'/'+date+'_bursttab')
            #Burst 5 bis 7 (Datum 1) - See in Burst 6
            tab_arr=[5,7]
            pg.write_tab(tab_arr, burst_tab)
            
            #Erstellung SLC mit gefilterten Burts
            pg.SLC_copy_ScanSAR(SLC_tab,RSLC_tab,burst_tab)
            
            
            #Erstellung Mosaik
            mslc_out=os.path.join(out,date+'/'+date+'_mslc')
            mslc_par_out=os.path.join(out,date+'/'+date+'_mslc.par')
            
            pg.SLC_mosaic_S1_TOPS(RSLC_tab, mslc_out, mslc_par_out, ml_rg, ml_az) 
            
            
            #Multilooking
            ml_out_mli=os.path.join(out,date+'/'+date+'_mli')
            ml_out_par=os.path.join(out,date+'/'+date+'_mli.par')
            
            pg.multi_look(mslc_out,mslc_par_out,ml_out_mli,ml_out_par,ml_rg,ml_az)
            
            #MLI width u lines aus Par auslesen
            mlidict=pg.ParFile(ml_out_par)
            mli_width=int(mlidict.get_value('range_samples'))
            mli_lines=int(mlidict.get_value('azimuth_lines'))
            
            #Import DEM
            srtm_par=os.path.join(out,date+'/'+date+'srtm_par')
            srtm_out=os.path.join(out,date+'/'+date+'srtm_out')
            pg.create_dem_par(srtm_par,ml_out_par,'-','-0.000833333333333','0.000833333333333','4326','0')
            pg.dem_import(srtm_location,srtm_out,srtm_par,'0','0',pg.which('egm2008-5.dem'),pg.which('egm2008-5.dem_par')) 
           
           
            #Erstellung geocoding LUT
            lookup=os.path.join(out,date+'/'+date+'.lt')
            ls_map=os.path.join(out,date+'/'+date+'ls_map')
            inc=os.path.join(out,date+'/'+date+'inc')
            dem_seg_par=os.path.join(out,date+'/'+date+'dem_seg.par')
            dem_seg=os.path.join(out,date+'/'+date+'dem_seg')
            simsar=os.path.join(out,date+'/'+date+'.EQA.simsar')
            pg.gc_map2(ml_out_par,srtm_par,srtm_out,dem_seg_par,dem_seg,lookup,'1','1','-','-','-','-','-',simsar)
            
            
            #DEM width auslesen
            demdict=pg.ParFile(dem_seg_par)
            dem_width=int(demdict.get_value('width'))
            dem_lines=int(demdict.get_value('nlines'))
            
            
            #Umwandlung des simulierten SAR Bildes in Radargeometrie
            geocode_simsar=os.path.join(out,date+'/'+date+'.simsar')
            pg.geocode(lookup,simsar,dem_width,geocode_simsar,mli_width,mli_lines,'0','0')
            
            
            #Refinement of lookup table, generation of offset parameter file
            diff_par=os.path.join(out,date+'/'+date+'.diff.par')
            pg.create_diff_par(ml_out_par,'-',diff_par,'1','0')
             
            
            # Refinement of lookup table, estimation of local offsets (1)
            pg.offset_pwrm(geocode_simsar,ml_out_mli,diff_par,'offs','snr','256','256','offsets','2','6','6','0.1')
            
            
            # Refinement of lookup table, estimation of offset polynomial (1)
            pg.offset_fitm('offs','snr',diff_par,'coffs','coffsets','0.1',',')
            
            
            # Refinement of lookup table
            lut_fine=os.path.join(out,date+'/'+date+'.lt_fine')
            pg.gc_map_fine(lookup,dem_width,diff_par,lut_fine,'1')
            
            
            # Resample DEM to RDC geometry:
            geocode_out=os.path.join(out,date+'/'+date+'_hgt')
            pg.geocode(lut_fine,dem_seg,dem_width,geocode_out,mli_width,mli_lines,'0','0')
            
            
            
            x= x + 1  #x = x + 1, weil das Datum in die Liste eingeht
            next_date = start_date + timedelta(days=6)
            walk_days(next_date, end_date,x,liste,path,out,srtm_location)
            date=start_date.strftime("%Y%m%d")
            
        #alle anderen Daten   
        #Koregistrierung der Daten mit dem ersten Datum  + Berechnung der Kohärenz der Datenpaare + Geokodierung der Ergebnisse
        else:
        
            #Erstellung des individuellen Datumsordners für Produkte des Datums bzw. Überprüfung, ob dieser schon erstellt wurde
            dir = os.path.join(out,date)
            if not os.path.exists(dir):
                os.mkdir(dir)
            
            #Variablen für die Bildung von aufeinanderfolgenden Datenpaaren anhand der generierten Datumsliste
            bild1=x-1 #Datum 1 
            bild2=x  #Datum 2
            
            #Erstellung SLC
            slcpar_out=os.path.join(out,date+'/'+date+'_slc.par')
            slc_out=os.path.join(out,date+'/'+date+'_slc')
            tops_out=os.path.join(out,date+'/'+date+'_tops.par')
            
            pg.par_S1_SLC(slc, ann, cal, noise, slcpar_out, slc_out, tops_out)
            
           
            #Erstellung SLC_tab 
            SLC_tab=os.path.join(out,date+'/'+date+'_tab')
            tab_arr=[slc_out,slcpar_out,tops_out]
            pg.write_tab(tab_arr, SLC_tab)
            
            
            #ML Variablen 
            ml_rg=8
            ml_az=2
            
            #Auswahl der Bursts anhand des Referenzdatums
            rslc_out=os.path.join(out,date+'/'+date+'_rslc')
            rslc_par_out=os.path.join(out,date+'/'+date+'_rslc.par')
            rslc_tops_out=os.path.join(out,date+'/'+date+'_rslc_tops.par')
            
            #Erstellung Tab Datei für den Burst Output
            RSLC_tab=os.path.join(out,date+'/'+date+'_tab_r')
            tab_arr=[rslc_out,rslc_par_out,rslc_tops_out]
            pg.write_tab(tab_arr, RSLC_tab)
            
            reftab=os.path.join(out,liste[0]+'/'+liste[0]+'_tab_r')  #Definition des Referenztabs (05.01.2017)
            rlsc_out_dir=os.path.join(out,date+'/')
            
            #Auswahl der Bursts anhand der Referenzaufnahme
            pg.ScanSAR_coreg_check(reftab,SLC_tab,RSLC_tab,rlsc_out_dir) 
            
            #Erstellung Mosaik
            mslc_out=os.path.join(out,date+'/'+date+'_mslc')
            mslc_par_out=os.path.join(out,date+'/'+date+'_mslc.par')
            
            pg.SLC_mosaic_S1_TOPS(RSLC_tab, mslc_out, mslc_par_out, ml_rg, ml_az)
            
            
            # neue Tab Datei für coreg burst
            coreg_tab=os.path.join(out,date+'/'+date+'_tab_coreg')
            crslc=os.path.join(out,date+'/'+date+'_crslc')
            crslc_par=os.path.join(out,date+'/'+date+'_crslc.par')
            crslc_tops_par=os.path.join(out,date+'/'+date+'_crslc_tops.par')
            tab_arr=[crslc,crslc_par,crslc_tops_par]
            pg.write_tab(tab_arr, coreg_tab)
            
            
            #Koregistrierung der beiden Bilder aufeinander (Referenzdatum (05.01.2017 mit aktuellen Datum)
            RSLC_tab1=os.path.join(out,liste[0]+'/'+liste[0]+'_tab_r')
            geocode_out=os.path.join(out,liste[0]+'/'+liste[0]+'_hgt')
            pg.S1_coreg_TOPS(RSLC_tab1,liste[0],RSLC_tab,liste[bild2],coreg_tab,geocode_out,ml_rg,ml_az)
            
                          
            #Multilook der koregistrierten Aufnahme und speichern im jeweiligen Datumsordner
            rslc2=os.path.join(wdir+date+'.rslc')
            rslc_par2=os.path.join(wdir+date+'.rslc.par')
            ml_out2=os.path.join(out,date+'/'+date+'_rmli')
            ml_par_out2=os.path.join(out,date+'/'+date+'_rmli.par')
            
            pg.multi_look(rslc2,rslc_par2,ml_out2,ml_par_out2,ml_rg,ml_az,'-','-')
        
            #Erstellung des Ergebnisordners bzw. Überprüfung, ob dieser schon erstellt wurde
            dir = os.path.join(out+'Results')
            if not os.path.exists(dir):
                os.mkdir(dir)
            
            results=os.path.join(out+'Results/')  #Pfad zum Resultordner
             
            #zweites Aufnahmedatum gesondert für das Speichern des rslc + rmli für das Referenzdatum und 2. Datum       
            if date == '20170111':
            
                rmli=os.path.join(wdir+liste[bild1]+'.rmli')
                rmli_par=os.path.join(wdir+liste[bild1]+'.rmli.par')
                target1=os.path.join(out,liste[bild1]+'/'+liste[bild1]+'_rmli')
                target2=os.path.join(out,liste[bild1]+'/'+liste[bild1]+'_rmli.par')
                shutil.copyfile(rmli,target1)
                shutil.copyfile(rmli_par,target2)
                
                rslc=os.path.join(wdir+liste[bild1]+'.rslc')
                rslc_par=os.path.join(wdir+liste[bild1]+'.rslc.par')
                target1=os.path.join(out,liste[bild1]+'/'+liste[bild1]+'_rslc')
                target2=os.path.join(out,liste[bild1]+'/'+liste[bild1]+'_rslc.par')
                shutil.copyfile(rslc,target1)
                shutil.copyfile(rslc_par,target2)
                
                rslc=os.path.join(wdir+liste[bild2]+'.rslc')
                rslc_par=os.path.join(wdir+liste[bild2]+'.rslc.par')
                target1=os.path.join(out,liste[bild2]+'/'+liste[bild2]+'_rslc')
                target2=os.path.join(out,liste[bild2]+'/'+liste[bild2]+'_rslc.par')
                shutil.copyfile(rslc,target1)
                shutil.copyfile(rslc_par,target2)
            
            #Speichern des rslc im jeweiligen Datumsordner
            else:
            
                rslc=os.path.join(wdir+liste[bild2]+'.rslc')
                rslc_par=os.path.join(wdir+liste[bild2]+'.rslc.par')
                target1=os.path.join(out,liste[bild2]+'/'+liste[bild2]+'_rslc')
                target2=os.path.join(out,liste[bild2]+'/'+liste[bild2]+'_rslc.par')
                shutil.copyfile(rslc,target1)
                shutil.copyfile(rslc_par,target2)
            
                        
            #Erstellung des Offsets zwischen Datum 1 und Datum 2 anhand der Parameter Datein mittels Cross-Corelation of Intensity
            ml_out_par=os.path.join(out,liste[0]+'/'+liste[0]+'_rmli.par')
            mlidict=pg.ParFile(ml_out_par)
            mli_width=int(mlidict.get_value('range_samples'))
            rslcpar1=os.path.join(out,liste[bild1]+'/'+liste[bild1]+'_rslc.par')
            rslcpar2=os.path.join(out,liste[bild2]+'/'+liste[bild2]+'_rslc.par')
            off=os.path.join(wdir+liste[bild1]+'_'+liste[bild2]+'_off')
            pg.create_offset(rslcpar1,rslcpar2,off,'-',ml_rg,ml_az,'0')
            
            #Erstellung der simulierten unwrapped interferometrischen Phase mit Referenz DEM 
            geocode_out=os.path.join(out,liste[0]+'/'+liste[0]+'_hgt')
            sim_orb=os.path.join(wdir+liste[bild1]+'_'+liste[bild2]+'_sim_orb')
            refpar=os.path.join(out,liste[0]+'/'+liste[0]+'_rslc.par')
            pg.phase_sim_orb(rslcpar1,rslcpar2,off,geocode_out,sim_orb,refpar)
            
            #Erstellung des differential Interferogram aus koregistrierten Datum 1 + 2 und des simulierten Interferogramms
            rslc1=os.path.join(out,liste[bild1]+'/'+liste[bild1]+'_rslc')
            rslc2=os.path.join(out,liste[bild2]+'/'+liste[bild2]+'_rslc')
            phase_diff=os.path.join(wdir+liste[bild1]+'_'+liste[bild2]+'_diff')
            pg.SLC_diff_intf(rslc1,rslc2,rslcpar1,rslcpar2,off,sim_orb,phase_diff,ml_rg,ml_az,'0','0','0.2','1','1')
            
            #Bestimmung der Kohärenz
            ml_out_par=os.path.join(out,liste[0]+'/'+liste[0]+'_rmli.par')
            mlidict=pg.ParFile(ml_out_par)
            mli_width=int(mlidict.get_value('range_samples'))
            coh_out=os.path.join(wdir+liste[bild1]+'_'+liste[bild2]+'_coherence.cc_ad')
            ml_out1=os.path.join(out,liste[bild1]+'/'+liste[bild1]+'_rmli')
            ml_out2=os.path.join(out,liste[bild2]+'/'+liste[bild2]+'_rmli')
            pg.cc_ad(phase_diff,ml_out1,ml_out2,'-','-',coh_out,mli_width,3,7,1)
            
            #Geokodierung des Kohärenz Bildes anhand der Lookuptable des Referenzbildes
            coh_coded_out=os.path.join(wdir+liste[bild1]+'_'+liste[bild2]+'_coherence.geo.cc_ad')
            lut_fine=os.path.join(out,liste[0]+'/'+liste[0]+'.lt_fine')
            dem_seg_par=os.path.join(out,liste[0]+'/'+liste[0]+'dem_seg.par')
            demdict=pg.ParFile(dem_seg_par)
            dem_width=int(demdict.get_value('width'))
            pg.geocode_back(coh_out,mli_width,lut_fine,coh_coded_out,dem_width)
            
            #Umwandlung der geokodierten Kohärenz in das Tif Format
            coh_coded_tif=os.path.join(results+liste[bild1]+'_'+liste[bild2]+'_coherence.geo.cc_ad.tif')
            pg.data2geotiff(dem_seg_par,coh_coded_out,'2',coh_coded_tif)  
            
            print(liste)
            
            #Löschen des temporären Ordners nach jedem Durchlauf der Schleife
            shutil.rmtree(wdir, ignore_errors=True)
        
            x= x + 1  #x = x + 1, weil das Datum in die Liste eingeht
            next_date = start_date + timedelta(days=6)
            walk_days(next_date, end_date,x,liste,path,out,srtm_location)
            date=start_date.strftime("%Y%m%d")
                     
                    
###################################################################################################################################    
#Definition der Inputvariablen (fest)
x=0  #x = 0, weil in einer Liste der 1. Eintrag den Index 0 hat
liste=[]  #leere Liste
start_date = datetime(2017, 1, 5) #Startdatum
end_date   = datetime(2017, 12, 31) #Enddatum


#Input durch den Nutzer
print('\nEingabe Pfad zum Ordner mit allen entippten Sentinel Daten. Beispiel: "/work/GEO410/do58mow/Projekt/unzipped_sentinel/"')
path1=input('Sentinel Daten Pfad:\n')
print('\nEingabe Output Pfad. Dort werden alle Zwischenergebniise und Produkte gespeichert. Beispiel: "/work/GEO410/do58mow/Ergebnisse/"')
out1=input('Output Daten Pfad:\n')
print('\nEingabe des Pfades zum DTM. Beispiel: "/work/GEO410/do58mow/srtm_germany_dtm.tif"')
srtm_location1=input('SRTM Pfad:\n')
path = path1.replace('"','')
out = out1.replace('"','')
srtm_location = srtm_location1.replace('"','')

#Start des Prozesses
walk_days(start_date, end_date,x,liste,path,out,srtm_location)

#alle temporäre Ordner löschen
os.chdir(out)
a=0
for i in liste:
    directory=os.path.join(out+liste[a]+'/')
    shutil.rmtree(directory, ignore_errors=True)
    a=a+1

#finale Ausgabe bei erfolgreichem Durchlauf des Skripts    
print('Die Prozessierung ist abgeschlossen. Es sind Kohärenzbilder zwischen',start_date.strftime("%d/%m/%Y"),'und',end_date.strftime("%d/%m/%Y"),'gebildet worden.')