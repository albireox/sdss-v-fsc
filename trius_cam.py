import PyIndi
import time
import sys
import threading
import numpy as np
from astropy.io import fits
     
class IndiClient(PyIndi.BaseClient):
    def __init__(self):
        super(IndiClient, self).__init__()
    def newDevice(self, d):
        pass
    def newProperty(self, p):
        pass
    def removeProperty(self, p):
        pass
    def newBLOB(self, bp):
        global blobEvent
        print("new BLOB ", bp.name)
        blobEvent.set()
        pass
    def newSwitch(self, svp):
        pass
    def newNumber(self, nvp):
        pass
    def newText(self, tvp):
        pass
    def newLight(self, lvp):
        pass
    def newMessage(self, d, m):
        pass
    def serverConnected(self):
        pass
    def serverDisconnected(self, code):
        pass

def connect_to_indi():
    # connect the server
    indiclient=IndiClient()
    indiclient.setServer("localhost",7624)
     
    if (not(indiclient.connectServer())):
         print("No indiserver running on "+indiclient.getHost()+":"+str(indiclient.getPort())+" - Try to run")
         print("  indiserver indi_sx_ccd")
         sys.exit(1)

    return indiclient

def connect_to_ccd(indiclient):
    ccd="SX CCD SXVR-H694"
    device_ccd=indiclient.getDevice(ccd)
    while not(device_ccd):
        time.sleep(0.5)
        device_ccd=indiclient.getDevice(ccd)
        print("Searching for device...")

    print("Found device")
     
    ccd_connect=device_ccd.getSwitch("CONNECTION")
    while not(ccd_connect):
        time.sleep(0.5)
        ccd_connect=device_ccd.getSwitch("CONNECTION")
    if not(device_ccd.isConnected()):
        ccd_connect[0].s=PyIndi.ISS_ON  # the "CONNECT" switch
        ccd_connect[1].s=PyIndi.ISS_OFF # the "DISCONNECT" switch
        indiclient.sendNewSwitch(ccd_connect)

 
    ccd_exposure=device_ccd.getNumber("CCD_EXPOSURE")
    while not(ccd_exposure):
        time.sleep(0.5)
        ccd_exposure=device_ccd.getNumber("CCD_EXPOSURE")
  
    # inform the indi server that we want to receive the
    # "CCD1" blob from this device
    indiclient.setBLOBMode(PyIndi.B_ALSO, ccd, "CCD1")
    ccd_ccd1=device_ccd.getBLOB("CCD1")
    while not(ccd_ccd1):
        time.sleep(0.5)
        ccd_ccd1=device_ccd.getBLOB("CCD1")
        
    return ccd_exposure, ccd_ccd1

def exposure(indiclient, ccd_exposure, ccd_ccd1, expTime):
    blobEvent.clear()    
    
    # set the value for the next exposure
    ccd_exposure[0].value=expTime
    indiclient.sendNewNumber(ccd_exposure)
    name = str(expTime)
    
    # wait for the exposure
    blobEvent.wait()
    
    for blob in ccd_ccd1:
        print("name: ", blob.name," size: ", blob.size," format: ", blob.format)
        # pyindi-client adds a getblobdata() method to IBLOB item
        # for accessing the contents of the blob, which is a bytearray in Python
        image_data=blob.getblobdata()
        print("fits data type: ", type(image_data))

        # write the byte array out to a FITS file
        f = open('/home/vncuser/Pictures/SX CCD/SC-CCD-Test-'+name+'.fits', 'wb')
        f.write(image_data)
        f.close()


if __name__ == "__main__":
    
    indiclient = connect_to_indi()
    ccd_exposure, ccd_ccd1 = connect_to_ccd(indiclient)
    
    flag = True
    while flag:
        expTime = input('$ ')
        
        try:
            float(expTime)
            if float(expTime) >= 0:
                expTime = float(expTime)
                blobEvent=threading.Event()
                exposure(indiclient, ccd_exposure, ccd_ccd1, expTime)
            
        except ValueError:
            print('ERROR: Not a valid exposure time')        
