﻿""" Python wrapper for ASPEN olxapi.dll

"""
__author__ = "ASPEN"
__copyright__ = "Copyright 2022, Advanced Systems for Power Engineering Inc."
__license__ = "All rights reserved"
__version__ = "15.8.4"
__email__ = "support@aspeninc.com"
__status__ = "Release"

from ctypes import *
import sys,os.path
from .OlxAPIConst import *

class OlxAPIException(Exception):
    """Raise this exeption to report OlxAPI error messages

    """
    def __init__(self, msg):
        self.msg = msg
    def __str__(self):
        return self.msg
#
def encode3(s):
    """
    convert string => bytes
    for compatibility python 2/3
    """
    if type(s)==str:
        return s.encode('UTF-8')
    return s
#
def decode(s):
    """
    convert bytes => string
    """
    if type(s)==bytes:
        try:
            return s.decode('UTF-8')
        except:
            try:
                return s.decode('ANSI')
            except:
                return str(s)
    return s
#
def getASPENFile(path,sfile):
    """
    return: abs path of sfile
            None if not found
    """
    if not os.path.isfile( os.path.join(path,sfile) ) :
        path = "C:\\Program Files (x86)\\ASPEN\\1LPFv15"
    if not os.path.isfile( os.path.join(path,sfile) ) :
        path = "C:\\Program Files\\ASPEN\\1LPFv15"
    if not os.path.isfile( os.path.join(path,sfile) ) :
        path = "C:\\Program Files (x86)\\ASPEN\\1LPFv14\\OlrxAPI"
    if not os.path.isfile( os.path.join(path,sfile) ) :
        path = "C:\\Program Files\\ASPEN\\1LPFv14\\OlrxAPI"
    #
    sf = os.path.join(path,sfile)
    if os.path.isfile(sf) :
        return os.path.abspath(sf)
    else:
        return None
#
ASPENOlxAPIDLL = None
#
def InitOlxAPI(dllPath,prt=True):
    """Initialize OlxAPI session.

    Successfull initialization is required before any
    other OlxAPI call can be executed.

    Args:
        dllPath (string): Full path name ASPEN program folder
                          where olxapi.dll and related
                          program components are located
                          if ="" => find automatic on disc C

    Returns:
        None

    Raises:
        OlxAPIException
    """
    global ASPENOlxAPIDLL
    if ASPENOlxAPIDLL != None:
        return
    #
    olxapi = getASPENFile(dllPath,"olxapi.dll")
    if olxapi ==None:
        raise OlxAPIException("Failed to locate: " + olxapi )
    #
    path = os.path.dirname(olxapi)
    if path not in sys.path:
        os.environ['PATH'] = path + ";" + os.environ['PATH']
    # Attempt to copy hasp_rt.exe to the executable path.
    # (Required in network key applications)
    ph1 = os.path.join(os.path.dirname(sys.executable),"hasp_rt.exe")
    if not os.path.isfile(ph1):
        ph2 = os.path.join(path,"hasp_rt.exe")
        if os.path.isfile(ph2):
            try:
                from shutil import copyfile
                copyfile(ph2,ph1)
            except :
                #raise Exception("\nPermission denied: " +os.path.dirname(sys.executable))
                pass
    # Load the OlxAPI.dll
    ASPENOlxAPIDLL = WinDLL(olxapi , use_last_error=True)
    if ASPENOlxAPIDLL == None:
        raise OlxAPIException("Failed to setup olxapi.dll")
    # OlxAPI.dll is hardcoded to return ErrorString() of "No Error"
    # when and only when the session is successfully initialzed and active
    errorAPIInit = "OlxAPI Init Error"
    try:
        # Attempt to get error string
        errorAPIInit = ErrorString()
    except:
        pass
    if errorAPIInit != "No Error":
        raise OlxAPIException(errorAPIInit)
    #
    if prt:
        buf = create_string_buffer(b'\000' * 1028)
        ASPENOlxAPIDLL.OlxAPIVersionInfo(buf)
        vData = decode(buf.value).split("\n")
        v1 = vData[0].split()
        v2 = vData[1].split()
        Version = v1[2]
        BuildNumber = v1[4]
        DBXVersion = int(v2[2])
        print ( "OlxAPI Version:"+Version+" Build: "+BuildNumber + " Path: " + path)
        if OLXAPI_DBX_VER<DBXVersion:
            print('\tWarning DLL DBX version (%i) > DBX Python(%i)\n'%(DBXVersion,OLXAPI_DBX_VER))
#
def UnloadOlxAPI():
    """Unload the OlxAPI.dll

    Returns:
        None

    Raises:
        OlxAPIException
    """
    global ASPENOlxAPIDLL
    if ASPENOlxAPIDLL != None:
        if 0!= windll.kernel32.FreeLibrary(ASPENOlxAPIDLL._handle):
            ASPENOlxAPIDLL = None
        else:
            raise OlxAPIException("Failed to unload olxapi.dll")

# API function prototypes
def Version():
    """OlxAPI engine version string in format version_major.version_minor
    """
    buf = create_string_buffer(b'\000' * 1028)
    ASPENOlxAPIDLL.OlxAPIVersionInfo(buf)
    vData = decode(buf.value).split(" ")
    return vData[2]

def BuildNumber():
    """OlxAPI engine build number
    """
    buf = create_string_buffer(b'\000' * 1028)
    ASPENOlxAPIDLL.OlxAPIVersionInfo(buf)
    vData = decode(buf.value).split(" ")
    return int(vData[4])

#
def SaveDataFile(filePath):
    """Save ASPEN OLR data file to disk

    Args:
        filePath (c_char_p) : Full path name of ASPEN OLR file.

    Returns:
        OLXAPI_FAILURE: Failure
        OLXAPI_OK     : Success
    """
    ASPENOlxAPIDLL.OlxAPISaveDataFile.argtypes = [c_char_p]
    return ASPENOlxAPIDLL.OlxAPISaveDataFile( encode3(filePath) )

def CloseDataFile():
    """Close the network data file that had been loaded previously
       with a call to OlxAPILoadDataFile

    Args: None

    Returns:
        OLXAPI_FAILURE: Failure
        OLXAPI_OK     : Success

    Remarks:
    """
    return ASPENOlxAPIDLL.OlxAPICloseDataFile()

def LoadDataFile(filePath,readonly):
    """Read ASPEN OLR data file from disk

    Args:
        filePath (c_char_p) : Full path name of ASPEN OLR file.
        readonly (c_int): open in read-only mode. 1-true; 0-false

    Returns:
        OLXAPI_FAILURE: Failure
        OLXAPI_OK     : Success
        OLXAPI_DATAFILEANOMALIES: File opened with data errors

    Remarks:
        The OneLiner’s TTY output during the data file reading operation execution
        is atomatically saved in the log file PowerScriptTTYLog.txt in the
        Windows %TEMP% folder. When this funtions return value is other than OLXAPI_OK,
        you must check the content of this log file for details of data errors and
        warnings that were found when reading the file and proceed accordingly.
    """
    ASPENOlxAPIDLL.OlxAPILoadDataFile.argtypes = [c_char_p,c_int]
    return ASPENOlxAPIDLL.OlxAPILoadDataFile( encode3(filePath) ,readonly)

def ReadChangeFile(filePath):
    """Read ASPEN CHF file from disk

    Args:
        filePath (c_char_p) : Full path name of ASPEN OLR file.
        flag (c_int): Change file processing flag: 1-true; 0-false

    Returns:
        OLXAPI_FAILURE: Failure
        OLXAPI_OK     : Success
        1xxx           : Change file applied with xxx warnings
    """
    ASPENOlxAPIDLL.OlxAPIReadChangeFile.argtypes = [c_char_p]
    return ASPENOlxAPIDLL.OlxAPIReadChangeFile( encode3(filePath) )

def GetEquipment(otype, p_hnd):
    """Retrieves handle of the next equipment of given type in the system.

    This function will return the handle of all the objectsof the given type,
    one by one, in the order they are stored in the OLR file

    Set hnd to 0 to retrieve the first object

    Args:
        otype (c_int): Object type
        p_hnd (pointer(c_int)): Object handle

    Returns:
        OLXAPI_FAILURE: Failure
        OLXAPI_OK     : Success

    """
    ASPENOlxAPIDLL.OlxAPIGetEquipment.argstype = [c_int,c_void_p]
    return ASPENOlxAPIDLL.OlxAPIGetEquipment(otype, p_hnd)



def EquipmentType(hnd):
    """Returns the equipment type of the given handle.

    Args:
        hdn (c_int): Object handle

    Returns:
        OLXAPI_FAILURE: Failure
        OLXAPI_OK     : Success

    """
    ASPENOlxAPIDLL.OlxAPIEquipmentType.argstype = [c_int]
    return ASPENOlxAPIDLL.OlxAPIEquipmentType(hnd)

def GetData(hnd, token, dataBuf):
    """Get object data field

    Args:
        hnd (c_int):        Object handle
        token (c_int):      field token
        dataBuf (c_void_p): data buffer

    Returns:
        OLXAPI_FAILURE: Failure
        OLXAPI_OK     : Success
    """
    ASPENOlxAPIDLL.OlxAPIGetData.argtypes = [c_int,c_int,c_void_p]
    return ASPENOlxAPIDLL.OlxAPIGetData(hnd, token, dataBuf)

def FindBus(name, kv):
    """Find handle of bus with given name and kv

    Args:
        name (c_char_p):    Bus name
        kv (c_double):      Bus nominal kv

    Returns:
        OLXAPI_FAILURE: Failure
        hnd     : bus handle
    """
    ASPENOlxAPIDLL.OlxAPIFindBus.argtypes = [c_char_p,c_double]
    return ASPENOlxAPIDLL.OlxAPIFindBus( encode3(name) , kv)

def FindEquipmentByTag(tags, devType, hnd):
    """Find handle of object of devType that has
       the given tags

    Args:
        tags (c_char_p): Tag string
        tags (c_int):    Object type: TC_BUS, TC_LOAD, TC_SHUNT, TC_GEN , TC_SVD,
                         TC_LINE, TC_XFMR, TC_XFMR3, TC_PS, TC_SCAP, TC_MU,
                         TC_RLYGROUP, TC_RLYOCG, TC_RLYOCP, TC_RLYDSG, TC_RLYDSP,
                         TC_FUSE,   TC_SWITCH, TC_RECLSRP, TC_RECLSRG or zero.
        hnd (POINTER(c_int)):  Object handle
    Returns:
        OLXAPI_FAILURE: Failure
        OLXAPI_OK     : Success
    Remarks: To get the first object in the list, call this function with *hnd equal 0.
             Call this function with devType equal 0 to search all object types.
    """
    ASPENOlxAPIDLL.OlxAPIFindEquipmentByTag.argtypes = [c_char_p,c_int,POINTER(c_int)]
    return ASPENOlxAPIDLL.OlxAPIFindEquipmentByTag( encode3(tags) , devType, hnd)

def FindBusNo(no):
    """Find handle of bus with given number.

    Args:
        no (c_int):    Bus number (must non zero)

    Returns:
        OLXAPI_FAILURE: Failure
        hnd     : bus handle
    """
    ASPENOlxAPIDLL.OlxAPIFindBusNo.argtypes = [c_int]
    return ASPENOlxAPIDLL.OlxAPIFindBusNo(no)

def SetData(hnd, token, p_data):
    """Assign a value to an object data field

    Args:
        hnd (c_int): Object handle
        token (c_int): Object field token
        p_data (c_void_p): New field value

    Returns:
        OLXAPI_FAILURE: Failure
        OLXAPI_OK     : Success
    """
    ASPENOlxAPIDLL.OlxAPISetData.argstype = [c_int, c_int, c_void_p]
    return ASPENOlxAPIDLL.OlxAPISetData(hnd, token, p_data)

def GetBusEquipment(hndBus, TC_type, pHnd):
    """Retrieves the handle of the next equipment of a given type
    that is attached to a bus.

    The equipment TC_type can be one of the following:
    TC_GEN: 	to get the handle for the generator.
                There can be at most one at a bus.
    TC_LOAD: 	to get the handle for the load.
                There can be at most one at a bus.
    TC_SHUNT:	to get the handle for the shunt.
                There can be at most one at a bus.
    TC_SVD:	    to get the handle for the switched shunt.
                There can be at most one at a bus.
    TC_GENUNIT: 	to get the handle for the next generating unit.
    TC_LOADUNIT: 	to get the handle for the next load unit.
    TC_SHUNTUNIT: 	to get the handle for the next shunt unit.
    TC_BRANCH: 	to get the handle for the next branch object.

    Set p_hnd to zero to get the first equipment handle.

    Args:
        hndBus (c_int): bus handle
        TC_type (c_int): object type code
        p_hnd (byref(c_int): object handle

    Returns:
        OLXAPI_FAILURE: Failure
        OLXAPI_OK     : Success
    """
    ASPENOlxAPIDLL.OlxAPIGetBusEquipment.argtypes = [c_int,c_int,c_void_p]
    return ASPENOlxAPIDLL.OlxAPIGetBusEquipment( hndBus, TC_type, pHnd)

def PostData(hnd):
    """Perform validation and update objct data in the network database

        Changes to the equipment data made through SetData function will
        not be committed to the program network database until after
        this function has been executed with success.

    Args:
        hnd (c_int): Object handle

    Returns:
        OLXAPI_FAILURE: Failure
        OLXAPI_OK     : Success
    """
    ASPENOlxAPIDLL.OlxAPIPostData.argtypes = [c_int]
    return ASPENOlxAPIDLL.OlxAPIPostData(hnd)

def DeleteEquipment(hnd):
    """Delete network object.

    Args:
        hnd (c_int): Object handle

    Returns:
        OLXAPI_FAILURE: Failure
        OLXAPI_OK     : Success
    """
    ASPENOlxAPIDLL.OlxAPIDeleteEquipment.argtypes = [c_int]
    return ASPENOlxAPIDLL.OlxAPIDeleteEquipment(hnd)

def GetPSCVoltage( hnd, vdOut1, vdOut2, style ):
    """Retrieves pre-fault voltage of a bus, or of connected buses of
    a line, transformer, switch or phase shifter.

    Args:
        hnd	(c_int): object handle
        vdOut1 (c_double*3): voltage result, real part or magnitude,
                             at equipment terminals
        vdOut2 (c_double*3): voltage result, imaginary part or angle in degree
                             at equipment terminals
        style (c_int)     : voltage result style
                             1: output voltage in kV
                             2: output voltage in per-unit
    Returns:
        OLXAPI_FAILURE: Failure
        OLXAPI_OK     : Success
    """
    ASPENOlxAPIDLL.OlxAPIGetPSCVoltage.argtypes = [c_int, c_double*3, c_double*3, c_int]
    return ASPENOlxAPIDLL.OlxAPIGetPSCVoltage( hnd, vdOut1, vdOut2, style )

def GetSCVoltage( hnd, vdOut1, vdOut2, style ):
    """Retrieves post-fault voltage of a bus, or of connected buses of
    a line, transformer, switch or phase shifter.

    Args:
        hnd	(c_int): object handle
        vdOut1 (c_double*9): voltage result, real part or magnitude,
                             at equipment terminals
        vdOut2 (c_double*9): voltage result, imaginary part or angle in degree
                             at equipment terminals
        style (c_int)     : voltage result style
                                1: output 012 sequence voltage in rectangular form
                                2: output 012 sequence voltage in polar form
                                2: output ABC phase voltage in rectangular form
                                4: output ABC phase voltage in polar form
    Returns:
        OLXAPI_FAILURE: Failure
        OLXAPI_OK     : Success
    """
    ASPENOlxAPIDLL.OlxAPIGetSCVoltage.argtypes = [c_int, c_double*9, c_double*9, c_int]
    return ASPENOlxAPIDLL.OlxAPIGetSCVoltage( hnd, vdOut1, vdOut2, style )

def GetSCCurrent( hnd, vdOut1, vdOut2, style ):
    """Retrieve post fault current for a generator, load, shunt, switched shunt,
    generating unit, load unit, shunt unit, transmission line, transformer,
    switch or phase shifter.

    You can get the total fault current by calling this function with the
    pre-defined handle of short circuit solution, HND_SC.

    Args:
        hnd	(c_int): object handle
        vdOut1 (c_double*12): current result, real part or magnitude, into
                             equipment terminals
        vdOut2 (c_double*12): current result, imaginary part or angle in degree,
                             into equipment terminals
        style (c_int)      : current result style
                            1: output 012 sequence current in rectangular form
                            2: output 012 sequence current in polar form
                            3: output ABC phase current in rectangular form
                            4: output ABC phase current in polar form

    Returns:
        OLXAPI_FAILURE: Failure
        OLXAPI_OK     : Success
    """
    ASPENOlxAPIDLL.OlxAPIGetSCCurrent.argtypes = [c_int, c_double*12, c_double*12, c_int]
    return ASPENOlxAPIDLL.OlxAPIGetSCCurrent( hnd, vdOut1, vdOut2, style )

def GetRelay( hndRlyGroup, hndRelay ):
    """Retrieve handle of the next relay object in a relay group.

    Set hndRelay=0 to get the first relay.

    Args:
        hndRlyGroup (c_int): Relay group handle
        hndRelay (byref(c_int)): relay handle
    Returns:
        OLXAPI_FAILURE: Failure
        OLXAPI_OK     : Success
    """
    ASPENOlxAPIDLL.OlxAPIGetRelay.argtypes = [c_int, c_void_p]
    return ASPENOlxAPIDLL.OlxAPIGetRelay( hndRlyGroup, hndRelay );

def GetLogicScheme( hndRlyGroup, hndScheme ):
    """Retrieve handle of the next logic scheme object in a relay group.

    Set hndScheme=0 to get the first scheme.

    Args:
        hndRlyGroup (c_int): Relay group handle
        hndScheme (byref(c_int)): Logic scheme handle
    Returns:
        OLXAPI_FAILURE: Failure
        OLXAPI_OK     : Success
    """
    ASPENOlxAPIDLL.OlxAPIGetLogicScheme.argtypes = [c_int, c_void_p]
    return ASPENOlxAPIDLL.OlxAPIGetLogicScheme( hndRlyGroup, hndScheme );

def GetRelayTime( hndRelay, mult, consider_signalonly, trip, device ):
    """Retrieve operating time for a fuse, an overcurrent relay
    (phase or ground), recloser (phase or ground), or a distance relay (phase or ground)
    in fault simulation result.

    Args:
        hndRelay (c_int): [in] relay object handle
        mult (c_double) : [in] relay current multiplying factor
        consider_signalonly: [in] Consider relay element signal-only flag
                           1 - Yes; 0 - No
        trip (byref(c_double)) : [out] relay operating time in seconds
        device (c_char_p): [out] relay operation code. Required buffer size 128 bytes.
                     NOP  No operation.
                     ZGn  Ground distance zone n tripped.
                     ZPn  Phase distance zone n tripped.
                     TOC=value Time overcurrent element operating quantity in secondary amps
                     IOC=value Instantaneous overcurrent element operating quantity in secondary amps
    Returns:
        OLXAPI_FAILURE: Failure
        OLXAPI_OK     : Success
    """
    ASPENOlxAPIDLL.OlxAPIGetRelayTime.argtypes = [c_int, c_double, c_void_p, c_char_p, c_int]
    return ASPENOlxAPIDLL.OlxAPIGetRelayTime( hndRelay, mult, trip, device, consider_signalonly )

def Run1LPFCommand(Params):
    """Run OneLiner command

    Args:
        Params (c_char_p): XML string, or full path name to XML file, containing a XML node
                        - Node name: OneLiner command
                        - Node attributes: required command parameters

            Command: ARCFLASHCALCULATOR - Faults | Arc-flash hazard calculator
            Attributes:
                REPORTPATHNAME	(*) Full pathname of report file.
                APPENDREPORT            [0] Append to existing report 0-No;1-Yes
                OUTFILETYPE 	[2] Output file type 1- TXT; 2- CSV
                SELECTEDOBJ	Arcflash bus. Must  have one of following values
                           "PICKED " 	the highlighted bus on the 1-line diagram
                           "'BNAME1                ,KV1;’BNAME2’,KV2;..."  Bus name and nominal kV.
                TIERS	[0] Number of tiers around selected object. This attribute is ignored if SELECTEDOBJ is not found.
                AREAS	[0-9999] Comma delimited list of area numbers and ranges to check relaygroups agains backup.
                               This attribute is ignored if SELECTEDOBJ is found.
                ZONES	[0-9999] Comma delimited list of zone numbers and ranges to check relaygroups agains backup.
                            This attribute is ignored if AREAS or SELECTEDOBJ are found.
                KVS	[0-999] Comma delimited list of KV levels and ranges to check relaygroups agains backup.
                            This attribute is ignored if SELECTEDOBJ is found.
                TAGS	Comma delimited list of bus tags. This attribute is ignored if SELECTEDOBJ is found.
                EQUIPMENTCAT	(*) Equipment category: 0-Switch gear; 1- Cable; 2- Open air; 3- MCC                s and panelboards 1kV or lower
                GROUNDED	(*) Is the equipment grounded 0-No; 1-Yes
                ENCLOSED	(*) Is the equipment inside enclosure 0-No; 1-Yes
                CONDUCTORGAP	(*) Conductor gap in mm
                WORKDIST	(*) Working distance in inches
                ARCDURATION	Arc duration calculation method. Must have one of following values:
                          "FIXED" 	Use fixed duration
                          "FUSE " 	Use fuse curve
                          "FASTEST" 	Use fastest trip time of device in vicinity
                          "DEVICE" 	Use trip time of specified device
                          "SEA" 	Use stepped-event analysis
                ARCTIME	Arc duration in second. Must be present when ARCDURATION="FIXED"
                FUSECURVE	Fuse curve for arc duration calculation. Must be present when ARCDURATION=" FUSECURVE"
                BRKINTTIME	Breaker interrupting time in cycle. Must be present when ARCDURATION=" FASTEST" and "DEVICE"
                DEVICETIERS	[1] Number of tiers. Must be present when ARCDURATION=" FASTEST" and ="SEA"
                DEVICE	String  with location of the relaygroup and the relay name
                         "BNO1;                BNAME1                ;KV1;BNO2;                BNAME2                ;KV2;                CKT                ;BTYP; RELAY_ID; ".
                         Format description of these fields are is in OneLiner help section 10.2.
                ARCTIMELIMIT	[1] Perform no energy calculation when arc duration time is longer than 2 seconds

            Command: BUSFAULTSUMMARY : Faults | Bus fault summary
            Attributes:
               REPORTPATHNAME= (*) full valid path to report file
               BASELINECASE= pathname of base-line bus fault summary report in CSV format
               === Only when BASELINECASE is specified
               DIFFBASE= Basis for computing current deviation: [MAX3PH1LG] or MAXPHGND
               FLAGPCNT= [15] Current deviation percent threshold.
               === Only when BASELINECASE is not specified
               BUSLIST= Bus list, one on each row in format 'BusName',kV
               BUSNOLIST= Bus number list, coma delimited.
                          This attribute is ignored when BUSLIST is specified
               === Only when no BUSLIST and BUSNOLIST is  specified
               XGND= Fault reactance X
               RGND= Fault resistance R
               NOTAP= Exclude tap buses: [1]-TRUE; 0-FALSE
               PERUNITV= Report voltage in PU
               PERUNIT= Report current in PU
               AREAS= Area number range
               ZONES= Zone number range. This attribute is ignored when AREAS is specified
               BUSNOS= Additional bus number range
               KVS= Additional bus kV range
               TAGS= Additional tag filter
               TIERS= check lines in vicinity within this tier number
               AREAS= Check all lines in area range
               ZONES= Check all lines in zone range
               KVS=   Additional KV filter

            Command: CHECKRELAYOPERATIONPRC023 - Check | Relay loadability
            Attributes:
               REPORTPATHNAME= (*) full valid pathname of report file
               REPORTCOMMENT= Report comment string. 255 char or shorter
               SELECTEDOBJ=
                    PICKED Check devices in selected relaygroup
                    BNO1;'BNAME1';KV1;BNO2;'BNAME2';KV2;'CKT';BTYP;  location string of branch to check(OneLiner Help section 10.2)
               TIERS= check relaygroups in vicinity within this tier number
               AREAS= Check all relaygroups in area range
               ZONES= Check all relaygroups in zone range
               KVS=   Additional KV filter
               TAGS=  Additional tag filter
               USETAGFLAG= [0]-AND;[1]-OR
               DEVICETYPE= [OCP DSP] Devide type to check. Space delimited
               APPENDREPORT=	Append report file: 0-False; [1]-True
               LINERATINGTYPE=	[3] Line rating to use: 0-first; 1-second; 2-Third;	3-Fourth
               XFMRRATINGTYPE=	[2] Transformer rating to use: 0-MVA1; 1-MVA2; 2-MVA3
               FWRLOADLONLY= [0] Consider load in forward direction only
               VOLTAGEPU= [0.85] Per unit voltage
               LINECURRMULT= [1.5] Line load current multiplier
               XFMRCURRMULT= [1.5] Transformer load current multiplier
               PFANGLE= [30] Power factor angle

            Command: CHECKRELAYOPERATIONPRC026 - run Check | Relay performance in stable power swing (PRC-026-1)
            Attributes:
               REPORTPATHNAME= (*) full valid pathname of report file
               REPORTCOMMENT= Report comment string. 255 char or shorter
               SELECTEDOBJ=
                    PICKED Check devices in selected relaygroup
                    BNO1;'BNAME1';KV1;BNO2;'BNAME2';KV2;'CKT';BTYP;  location string of line to check(Help section 10.2)
               TIERS= check relaygroups in vicinity within this tier number
               AREAS= Check all relaygroups in area range
               ZONES= Check all relaygroups in zone range
               KVS=   Additional KV filter
               TAGS=  Additional tag filter
               DEVICETYPE= [OCP DSP] Devide type to check. Space delimited
               APPENDREPORT=	Append report file: 0-False; [1]-True
               SEPARATIONANGLE=	[120] System separation angle for stable power swing calculation
               DELAYLIMIT= [15] Report violation if relay trips faster than this limit (in cycles)
               CURRMULT= [1.0] Current multiplier to apply in relay trip checking

            Command: CHECKPRIBACKCOORD - Check | Primary/back relay coordination
            Attributes:
                REPORTPATHNAME  (*) Full pathname of report file.
                OUTFILETYPE     [2] Output file type 1- TXT; 2- CSV
                SELECTEDOBJ	Relay group to check against its backup. Must  have one of following values
                PICKED      the highlighted relaygroup on the 1-line diagram
                "BNO1;'BNAME1';KV1;BNO2;'BNAME2';KV2;'CKT';BTYP;"  location string of the relaygroup. Format description is in OneLiner help section 10.2.
                TIERS	[0] Number of tiers around selected object. This attribute is ignored if SELECTEDOBJ is not found.
                AREAS	[0-9999] Comma delimited list of area numbers and ranges to check relaygroups agains backup.
                ZONES	[0-9999] Comma delimited list of zone numbers and ranges to check relaygroups agains backup. This attribute is ignored if AREAS is found.
                KVS	0-999] Comma delimited list of KV levels and ranges to check relaygroups agains backup. This attribute is ignored if SELECTEDOBJ is found.
                TAGS	Comma delimited list of tags to check relaygroups agains backup. This attribute is ignored if SELECTEDOBJ is found.
                COORDTYPE	Coordination type to check. Must  have one of following values
                "0"	OC backup/OC primary (Classical)
                "1"	OC backup/OC primary (Multi-point)
                "2"	DS backup/OC primary
                "3"	OC backup/DS primary
                "4"	DS backup/DS primary
                "5"	OC backup/Recloser primary
                "6"	All types/All types
                LINEPERCENT	Percent interval for sliding intermediate faults. This attribute is ignored if COORDTYPE is 0 or 5.
                RUNINTERMEOP	1-true; 0-false. Check  intermediate faults with end-opened. This attribute is ignored if COORDTYPE is 0 or 5.
                RUNCLOSEIN	1-true; 0-false. Check close-in fault. This attribute is ignored if COORDTYPE is 0 or 5.
                RUNCLOSEINEOP	1-true; 0-false. Check close-in fault with end-opened. This attribute is ignored if COORDTYPE is 0 or 5.
                RUNLINEEND	1-true; 0-false. Check line-end fault. This attribute is ignored if COORDTYPE is 0 or 5.
                RUNREMOTEBUS	1-true; 0-false. Check remote bus fault. This attribute is ignored if COORDTYPE is 0 or 5.
                RELAYTYPE	Relay types to check: 1-Ground; 2-Phase; 3-Both.
                FAULTTYPE	Fault  types to check: 1-3LG; 2-2LG; 4-1LF; 8-LL; or sum of values for desired selection
                OUTPUTALL	1- Include all cases in report; 0- Include only flagged cases in report
                MINCTI	Lower limit of acceptable CTI range
                MAXCTI	Upper limit of acceptable CTI range
                OUTRLYPARAMS	Include relay settings in report: 0-None; 1-OC;2-DS;3-Both
                OUTAGELINES	Run line outage contingency: 0-False; 1-True
                OUTAGEXFMRS	Run transformer outage contingency: 0-False; 1-True
                OUTAGEMULINES	Run mutual line outage contingency: 0-False; 1-True. Ignored if OUTAGEMULINES=0
                OUTAGEMULINESGND		Run mutual line outage and grounded contingency: 0-False; 1-True. Ignored if OUTAGEMULINES=0
                OUTAGE2LINES	Run double line outage contingency: 0-False; 1-True. Ignored if OUTAGEMULINES=0
                OUTAGE1LINE1XFMR	Run double line and transformer outage contingency: 0-False; 1-True. Ignored if OUTAGEMULINES=0 or OUTAGEXFMRS =0
                OUTAGE2XFMRS	Run double and transformer outage contingency: 0-False; 1-True. Ignored if OUTAGEXFMRS =0
                OUTAGE3SOURCES	Outage only  3 strongest sources: 0-False; 1-True. Ignored if OUTAGEMULINES=0 and OUTAGEXFMRS =0

            Command: CHECKRELAYOPERATIONSEA - Check | Relay operation using stepped-events
            Attributes:
                REPORTPATHNAME	(*) Full pathname of folder for report files.
                OPTIONSFILEPATH Full pathname of the checking option file.
                REPORTCOMMENT		Additional comment string to include in all checking report files
                SELECTEDOBJ	Check line with selected relaygroup. Must  have one of following values
                    "PICKED " 	the highlighted relaygroup on the 1-line diagram
                    "BNO1;'BNAME1';KV1;BNO2;'BNAME2';KV2;'CKT';BTYP;"  location string of  the relaygroup. Format description is in OneLiner help section 10.2.
                TIERS	[0] Number of tiers around selected object. This attribute is ignored if SELECTEDOBJ is not found.
                AREAS	[0-9999] Comma delimited list of area numbers and ranges.
                ZONES	[0-9999] Comma delimited list of zone numbers and ranges. This attribute is ignored if AREAS is found.
                KVS	[0-999] Comma delimited list of KV levels and ranges. This attribute is ignored if SELECTEDOBJ is found.
                TAGS	Comma delimited list of tags. This attribute is ignored if SELECTEDOBJ is found.
                DEVICETYPE	Space delimited list of relay type types to take into consideration in stepped-events: OCG, OCP, DSG, DSP, LOGIC, VOLTAGE, DIFF
                FAULTTYPE	Space delimited list of fault  types to take into consideration in stepped-events: 1LF, 3LG
                OUTAGELINES	Run line outage contingency: 0-False; 1-True
                OUTAGEXFMRS	Run transformer outage contingency: 0-False; 1-True
                OUTAGEMULINES	Run mutual line outage contingency: 0-False; 1-True. Ignored if OUTAGEMULINES=0
                OUTAGEMULINESGND		Run mutual line outage and grounded contingency: 0-False; 1-True. Ignored if OUTAGEMULINES=0
                OUTAGE2LINES	Run double line outage contingency: 0-False; 1-True. Ignored if OUTAGEMULINES=0
                OUTAGE1LINE1XFMR	Run double line and transformer outage contingency: 0-False; 1-True. Ignored if OUTAGEMULINES=0 or OUTAGEXFMRS =0
                OUTAGE2XFMRS	Run double and transformer outage contingency: 0-False; 1-True. Ignored if OUTAGEXFMRS =0
                OUTAGE3SOURCES	Outage only  3 strongest sources: 0-False; 1-True. Ignored if OUTAGEMULINES=0 and OUTAGEXFMRS =0
                OUTAGEPILOT    Simulate pilot outage in N and N-1 cases

            Command: CHECKRELAYSETTINGS - Check | Relay settings
            Attributes:
               SELECTEDOBJ=
                    PICKED Check line with selected relaygroup
                    BNO1;'BNAME1';KV1;BNO2;'BNAME2';KV2;'CKT';BTYP;  location string of line to check(Help section 10.2)
               TIERS= check lines in vicinity within this tier number
               AREAS= Check all lines in area range
               ZONES= Check all lines in zone range
               KVS=   Additional KV filter
               TAGS=  Additional tag filter
               REPORTPATHNAME= (*) full valid path to report folder with write access
               OPTIONSFILEPATH Full pathname of the checking option file.
               REPORTCOMMENT= Report comment string. 255 char or shorter
               FAULTTYPE= 1LG, 3LG. Fault type to check. Space delimited
               DEVICETYPE= OCG, OCP, DSG, DSP, LOGIC, VOLTAGE, DIFF Devide type to check. Space delimited
               OUTAGELINES	Run Line outage contingency: 0-False; 1-True
               OUTAGEXFMRS	Run transformer outage contingency: 0-False; 1-True
               OUTAGE3SOURCES= 1 or 0 Outage only 3 strongest sources
               OUTAGEMULINES= 1 or 0 Outage mutually coupled lines
               OUTAGEMULINESGND= 1 or 0 Outage and ground ends of mutually coupled lines
               OUTAGE2LINES= 1 or 0 Double outage lines
               OUTAGE1LINE1XFMR= 1 or 0 Double outage line and transformer
               OUTAGE2XFMR= 1 or 0 Double outage transformers

           Command: DIFFANDMERGE - File | Compare and Merge...
           Attributes:
               FILEPATHA     Full pathname of file A. Can be ommited when and OLR file
                             had been opened.
               FILEPATHB (*) Full pathname of file B.
               FILEPATHBASE	 Full pathname of common base.
               FILEPATHDIFF	 Full pathname of the ADX file with DIFF result.
               FILEPATHMERGED  Full pathname of the OLR file with merge result.

            Command: EXPORTNETWORK = File | Export network data
            Attributes:
               FORMAT     = Output format: [DXT]-ASPEN DXT; PSSE-PSS/E Raw and Seq
                                           XML- ASPEN XML; CSV- ASPEN CSV
               SCOPE      =  Export scope: [0]-Entire network; 1-Area number; 2- Zone number
               AREANO     =  Export area number
               ZONENO	  =  Export zone number
               INCLUDETIES=  Include ties: [0]-False; 1-True
               ====DXT export only:
               DXTPATHNAME= (*) full valid pathname of ouput DXT file
               ====XML export only:

               OUTPUTPATHNAME= (*) full valid pathname of ouput XML file
               DATATYPE   = Types of data to include in the export. Integer number with
                            [Bit 1]-Network; Bit 2- Relay;
               ====PSSE export only:
               RAWPATHNAME= (*) full valid pathname of ouput RAW file
               SEQPATHNAME= (*) full valid pathname of ouput SEQ file
               PSSEVER	  =  [33] PSS/E version
               X3MIDBUSNO =  [18000] First fictitious bus number for 3-w transformer mid point
               NEWBUSNO   =  [15000] First bus number for buses with no bus number

            Command EXPORTRELAY - Relay | Export relay
            Attributes:
               FORMAT     =  Output format: [RAT]-ASPEN RAT;
               SCOPE      =  Export scope: [0]-Entire network; 1-Area number; 2- Zone number; 3-Invicinity of a bus
               AREANO     =  Export area number (*required when SCOPE=1)
               ZONENO	  =  Export zone number (*required when SCOPE=2)
               SELECTEDOBJ=  Selected bus (*required when SCOPE=3). Must be a string with following content
                             PICKED - Selected bus on the 1-line diagram
                             'BusName' kV - Bus name in single quotes and kV separated by space
               TIERS      =  [0] Number of tiers (ignored when SCOPE<>3)
               DEVICETYPE =  Device type to export. Comma delimied list of the following:
                             OC: Overcurrent
                             DS: Distance
                             RC: Recloser
                             VR: Voltage relay
                             DIFF: Differential relay
                             SCHEME: Logic scheme
                             COORDPAIR: Coorination pair
                             [OC,DS,RC,VR,DIFF,COORDPAIR,SCHEME]
               LASTCHANGEDDATE =  [01-01-1986] Cutoff last changed date
               RATPATHNAME= (*) full valid pathname of ouput RAT file

            Command: INSERTTAPBUS - Network | Bus | Insert tap bus
            Attributes:
               BUSNAME1=	(*) Line bus 1 name
               BUSNAME2=	(*) Line bus 2 name
               KV=	(*) Line kV
               CKTID=	(*) Line circuit ID
               PERCENT=	(*) Percent distance to tap from bus 1 (must be between 0-100)
               TAPBUSNAME=	(*) Tap bus name

            Command: SAVEDATAFILE - File | Save and File | Save as
            Attributes:
               PATHNAME     = Name or full pathname of new OLR file for File | Save as command.
                              If only file name is given, file will be saved in the folder
                              where the current OLR file is located.
                              If no attribute is specified, the File | Save command will be executed.

            Command SAVEFLTSPEC - Save desc and spec of faults in the result buffer to XML or CSV files
            Attributes:
                REPORTPATHNAME= (*)Output file pathname
                APPEND= [0]: overwrite existing file; 1: Append to existing file;
                FORMAT= output file format [0]: XML; 1: CSV
                CLEARPREV= Clear previous results flag to be recorded in the XML output
                            [0]: no; 1: yes;
                RANGE= Comma delimited list of fault index numbers and ranges(e.g. 1,3,5-10)
                        Default: save all faults in the results buffer

            Command: SETGENREFANGLE - Network | Set generator reference angle
            Attributes:
                REPORTPATHNAME	Full pathname of folder for report files.
                REFERENCEGEN	Bus name and kV of reference generator in format: 'BNAME', KV.
                EQUSOURCEOPTION	Option for calculating reference angle of equivalent sources. Must have one of the following values
                [ROTATE] 	apply delta angle of existing reference gen
                SKIP   	Leave unchanged. This option will be in effect automatically when old reference is not valid
                ASGEN  	Use angle computed for regular generator

            Command SIMULATEFAULT - Run OneLiner command FAULTS  | BATCH COMMAND & FAULT SPEC FILE | EXECUTE COMMAND
            Attributes:
                <FAULT> The <SIMULATEFAULT> XML node must contain one or more children nodes <FAULT>,
                         one for each fault case to be simulated.
                         The <FAULT> node can include XML attributes to specify the various fault
                         simulation options:
                               PREFAULTV: Prefault voltage flag
                                 0 - From linear network solution
                                 1 - Flat
                                 2 - From load flow
                               VPF: Flat prefault bus voltage
                               GENZTYPE: Generator reactance flag
                                 0 - subtransient
                                 1 - transient
                                 2 - synchronous
                               IGNORE: a bit field array
                                 bit 1 - ignore load
                                 bit 2 - ignore positive sequence shunt
                                 bit 3 - ignore line G and B
                                 bit 4 - ignore transformer B
                               GENILIMIT: generator limit option
                                 0 - Ignore
                                 1 - Enforce limit 1
                                 2 - Enforce limit 2
                               VCCS: Simulate VCCS flag 1-true; 0-false
                               MOV: MOV protected series capacitor iterative
                                    solution flag 1-true; 0-false
                               MOVITERF: MOV protected series capacitor iterative
                                           solution acceleration factor
                               MINZMUPAIR: Ignore mutual coupling threshold
                               MVASTYLE: Fault MVA calculatin method
                               GENW3: Simulate type-3 wind generator flag 1-true; 0-false
                               GENW4: Simulate CIR flag 1-true; 0-false
                               FLTOPTSTR: a space delimited string with all the fault otion fields in the order listed above
                                      PREFAULTV VPF GENZTYPE IGNORE GENILIMIT VCCS MOV MOVITERF MINZMUPAIR MVASTYLE GENW3 GENW4
                <FLTSPEC>  Each of the <FAULT> nodes can include up to 40 fault specifications to be
                           simulated in the case. Fault specification string in the format described in
                           OneLiner’s user manual APPENDIX I:  FAULT SPECIFICATION FILE
                           must be included as the text of children nodes <FLTSPEC>.
                FLTSPCVS= Alternatively, a tab-delimited list of all the fault spec strings can be entered as
                          the attribute "FLTSPCVS" in the <FAULT> node.
                CLEARPREV= Clear previous result buffer flag [0]: no; 1: yes;
            Returns:
                OLXAPI_FAILURE: Failure
                NOfault        : Total number of faults in the solution buffer
            Remark:
                When NOfault is not the expected value, call OlxAPIErrorString() for details of simulation error

            Command SNAPSPC: Run OneLiner command Diagram | Snap to state plane coordinates
            Attributes:
                 CENTERX - Screen center X in SPC
                 CENTERY - Screen center Y in SPC
                 SCALE   - Scaling factor
                 OPTIONS - Bit array options
                           Bit 1: Auto scale (compute center X, Y from
                                  SPC of all objects in the network)
                           Bit 2: Place all hidden buses using SPC
            Returns:
                 OLXAPI_FAILURE: Failure
                 NOmoves       : Total number of buses placed/moved
    """
    ASPENOlxAPIDLL.OlxAPIRun1LPFCommand.argstype = [c_char_p]
    return ASPENOlxAPIDLL.OlxAPIRun1LPFCommand( encode3(Params) )

def DoSteppedEvent(hnd, fltOpt, runOpt, noTiers):
    """Run stepped-event simulation

    Remarks:
        After successful call to OlxAPIDoSteppedEvent() you must call
        the function GetSteppedEvent() to retrieve detailed results of
        each step in the simulation.

        To retrieve the fault simulation results at a network element
        in each event, call PickFault() with the event index then use
        GetSCCurrent(), GetSCVoltage() and GetRelayOperation() functions
        accordingly.


    Args:
        hnd (c_int): handle of a bus or a relay group.
        fltOpt (c_double*64): simulation options
            fltOpt(1) - Fault connection code
                            1=3LG
                            2=2LG BC, 3=2LG CA, 4=2LG AB
                            5=1LG A, 5=1LG B, 6=1LG C
                            7=LL BC, 7=LL CA, 8=LL AB
            fltOpt(2) - Intermediate percent between 0.01-99.99. 0 for a
                        close-in fault. This parameter is ignored if nDevHnd
                        is a bus handle.
            fltOpt(3) - Fault resistance, ohm
            fltOpt(4) - Fault reactance, ohm
            fltOpt(4+1) - Zero or Fault connection code for additional user event
            fltOpt(4+2) - Time  of additional user event, seconds.
            fltOpt(4+3) - Fault resistance in additional user event, ohm
            fltOpt(4+4) - Fault reactance in additional user event, ohm
            fltOpt(4+5) - Zero or Fault connection code for additional user event
        ...
        runOpt (c_int*7): simulation options flags. 1 - set; 0 - reset
            runOpt(1)  - Consider OCGnd operations
            runOpt(2)  - Consider OCPh operations
            runOpt(3)  - Consider DSGnd operations
            runOpt(4)  - Consider DSPh operations
            runOpt(5)  - Consider Protection scheme operations
            runOpt(6)  - Consider Voltage relay operations
            runOpt(7)  - Consider Differential relay operations
        nTiers: Study extent. Take into account protective devices located within this number
                of tiers only.
    Returns:
        OLXAPI_FAILURE: Failure
        OLXAPI_OK     : Success
    """
    ASPENOlxAPIDLL.OlxAPIDoSteppedEvent.argstype = [c_int,c_double*64,c_int*7,c_int]
    return ASPENOlxAPIDLL.OlxAPIDoSteppedEvent(hnd, fltOpt, runOpt, noTiers)

def GetSteppedEvent( step, timeStamp, fltCurrent, userDef, eventDesc, faultDest ):
    """Retrieve detailed result of a step in stepped-event simulation

    Remarks:
        Call this function with step = 0 to get total number of steps

    Args:
        step (c_int): Sequential index of the event in the simulation.
                      (1 is the initial user-defined event)
        timeStamp (byref(c_double)): Event time in seconds
        fltCurrent (byref(c_double)): Highest phase fault current magnitude
                                      at this step
        userDef (byref(c_double)): User defined event flag. 1= true; 0= false
        eventDesc (c_char_p): Event description string that includes list
                              of all devices that had tripped.
        faultDesc (c_char_p): Fault description string of the event.

    Returns:
        OLXAPI_FAILURE: Failure
        OLXAPI_OK     : Success
    """
    ASPENOlxAPIDLL.OlxAPIGetSteppedEvent.argstype = [c_int,c_void_p,c_void_p,c_void_p,c_char_p,c_char_p]
    return ASPENOlxAPIDLL.OlxAPIGetSteppedEvent( step, timeStamp, fltCurrent, userDef, eventDesc, faultDest )

def DoBreakerRating(Scope, RatingThreshold, OutputOpt, OptionalReport,
                            ReportTXT, ReportCSV, ConfigFile) :
    """Run breaker rating study

    Args:
        Scope -          [1]: 0-IEEE;1-IEC
                         [2]: 0-All;1-Area;2-Zone;3-Selected
                         [3]: Area or zone number
                         ...: or list of bus hnd terminated with -1
        Scope[1] – Breaker rating standard: 0-ANSI/IEEE; 1-IEC.
        Scope[2] – Bus selection: 0-All buses; 1-in Area; 2-in Zone; 3- selected buses
        Scope[3] – Selected area or zone number.
        Scope[4] or list of handle number of selected buses. The last element in the list
                     must be -1.
        RatingThreshold [in] Percent rating threshold.
        OutputOpt  [in] Rating output option:
                        0- Output only overduty cases;
                        1- Output all cases;
                        OR Floating number S (0 < S < 1) -
                                 Check only breakers at buses where ratio
                                 “Bus fault current / Breaker rating” exceeds S.
        OptionalReport  [in] Integer number flag. Enable various bits to enable
                        optional sections in rating report: Bit 1- Detailed fault
                        simulation result; Bit 2- Breaker name plate data;
                        Bit 3- List of connected equipment.
        ReportTXT  [in] Full path name of text report file. Set to emty to omit text report.
        ReportCSV  [in] Full path name of CSV report file. Set to emty to omit CSV report.
        ConfigFile [in] Full path name of  breaker rating configuration file to apply in
                        this study. Set to emty to omit reading configuration file.
    Returns:
        OLXAPI_FAILURE: Failure
        OLXAPI_OK     : Success
    """
    ASPENOlxAPIDLL.OlxAPIDoBreakerRating.argtypes = [POINTER(c_int),c_double,c_double,c_int,c_char_p,c_char_p,c_char_p]
    return ASPENOlxAPIDLL.OlxAPIDoBreakerRating(Scope, RatingThreshold, OutputOpt, OptionalReport,
                            encode3(ReportTXT), encode3(ReportCSV), encode3(ConfigFile))
def BoundaryEquivalent(EquFileName, BusList, FltOpt) :
    """Create boundary equivalent network

    Args:
        EquFileName [in] Path name of the boundary equivalent OLR file.

        BusList   [in]   Array of handles of buses to be retained in the equivalent.
                         The list must be terminated with value -1

        FltOpt    [in] study parameters
                    FltOpt[1]  - Per-unit elimination threshold
                    FltOpt[2]  - Keep existing equipment at retained buses( 1- set; 0- reset)
                    FltOpt[3]  - Keep all existing annotations (1- set; 0-reset)

    Returns:
        OLXAPI_FAILURE: Failure
        OLXAPI_OK     : Success
    """
    ASPENOlxAPIDLL.OlxAPIBoundaryEquivalent.argtypes = [c_char_p,POINTER(c_int),c_double*3]
    return ASPENOlxAPIDLL.OlxAPIBoundaryEquivalent( encode3(EquFileName) , BusList, FltOpt)
def DoFault(hnd, fltConn, fltOpt, outageOpt, outageLst, fltR, fltX, clearPrev):
    """Simulate one or more faults

    Args:
        hnd	(c_int): handle of a bus, branch or a relay group.
        vnFltConn (c_int*4): fault connection flags. 1 - set; 0 - reset
            vnFltConn[1] - 3PH
            vnFltConn[2] - 2LG
            vnFltConn[3] - 1LG
            vnFltConn[4] - LL
        fltOpt(c_double*15): fault options flags. 1 - set; 0 - reset
            vdFltOpt(1)  - Close-in
            vdFltOpt(2)  - Close-in w/ outage
            vdFltOpt(3)  - Close-in with end opened
            vdFltOpt(4)  - Close-in with end opened w/ outage
            vdFltOpt(5)  - Remote bus
            vdFltOpt(6)  - Remote bus w/ outage
            vdFltOpt(7)  - Line end
            vdFltOpt(8)  - Line end w/ outage
            vdFltOpt(9)  - Intermediate %
            vdFltOpt(10) - Intermediate % w/ outage
            vdFltOpt(11) - Intermediate % with end opened
            vdFltOpt(12) - Intermediate % with end opened w/ outage
            vdFltOpt(13) - Auto seq. Intermediate % from (*)
            vdFltOpt(14) - Auto seq. Intermediate % to (*)
            vdFltOpt(15) - Outage line grounding admittance in mho (***).
        vnOutageLst (c_int*100): list of handles of branches to be outaged; 0 terminated
        vnOutageOpt (c_int*4):  branch outage option flags. 1 - set; 0 - reset
            vnOutageOpt(1) - one at a time
            vnOutageOpt(2) - two at a time
            vnOutageOpt(3) - all at once
            vnOutageOpt(4) - breaker failure (**)
        dFltR (c_double): fault resistance, in Ohm
        dFltX (c_double)" fault reactance, in Ohm
        nClearPrev (c_int): clear previous result flag. 1 - set; 0 - reset

    Remarks:
        (*)	To simulate a single intermediate fault without auto-sequencing,
            set both vdFltOpt(13)and vdFltOpt(14) to zero
        (**) Set this flag to 1 to simulate breaker open failure condition
             that caused two lines that share a common breaker to be separated
             from the bus while still connected to each other. TC_BRANCH handle
             of the two lines must be included in the array vnOutageLst.

    Returns:
        OLXAPI_FAILURE: Failure
        OLXAPI_OK     : Success
    """
    ASPENOlxAPIDLL.OlxAPIDoFault.argtypes = [c_int,c_int*4,c_double*15,c_int*4,c_int*100,c_double,c_double,c_int]
    return ASPENOlxAPIDLL.OlxAPIDoFault(hnd, fltConn, fltOpt, outageOpt, outageLst, fltR, fltX, clearPrev)

def PickFault( index, tiers ):
    """Select a specific short circuit simulation case.

    This function must be called before any post fault voltage and current results
    and relay time can be retrieved.

    Args:
        index (c_int): fault number or
                        SF_FIRST: first fault
                        SF_NEXT: next fault
                        SF_PREV: previous fault
                        SF_LAST: last available fault
        tiers (c_int): number of tiers around faulted bus to compute solution results

    Returns:
        OLXAPI_FAILURE: Failure
        OLXAPI_OK     : Success
    """
    ASPENOlxAPIDLL.OlxAPIPickFault.argtypes = [c_int,c_int]
    return ASPENOlxAPIDLL.OlxAPIPickFault( index, tiers)

# These API functions return string
def FaultDescriptionEx(index,flag):
    """Retrieves description and fltspec strings of a fault in the simulation results buffer.

    Call this function with index=0 to get description of the
    current fault simulation.

    Args:
        index (c_int): Index of fault simulation.
        flag  (c_int): Output flag
                       [0] Fautl description string only
                       1   Plus FLTSPCVS on the last line.
                           See SIMULATEFAULT for details of FLTSPCVS string
                       2   Plus FLTOPTSTR on the last line: a string containing the following
                           fault option data fields, separated by blank space:
                           PrefaultV: Prefault voltage flag
                             0 - From linear network solution
                             1 - Flat
                             2 - From load flow
                           FlatBusV: Flat prefault bus voltage
                           GenZType: Generator reactance flag
                             0 - subtransient
                             1 - transient
                             2 - synchronous
                           IgnoreFlag: a bit array
                             bit 1 - ignore load
                             bit 2 - ignore positive sequence shunt
                             bit 3 - ignore line G and B
                             bit 4 - ignore transformer B
                           GenILimitOption: generator limit option
                             0 - Ignore
                             1 - Enforce limit 1
                             2 - Enforce limit 2
                           SimulateCCGen: Simulate VCCS flag 1-true; 0-false
                           IgnoreMOV: MOV protected series capacitor iterative
                                       solution flag 1-true; 0-false
                           AccelFactor: MOV protected series capacitor iterative
                                       solution acceleration factor
                           MuThreshold: Ignore mutual coupling threshold
                           FaultMVAstyle: Fault MVA calculatin method
                           SimulateGenW3: Simulate type-3 wind generator flag 1-true; 0-false
                           SimulateGenW4: Simulate CIR flag 1-true; 0-false
    Returns:
        string (c_char_p)
    """
    ASPENOlxAPIDLL.OlxAPIFaultDescriptionEx.restype = c_char_p
    ASPENOlxAPIDLL.OlxAPIFaultDescriptionEx.argstype = [c_int,c_int]
    return decode (ASPENOlxAPIDLL.OlxAPIFaultDescriptionEx(index,flag) )
def FaultDescription(index):
    """Retrieves description and fltspec strings of a fault in the simulation results buffer.

    Call this function with index=0 to get description of the
    current fault simulation.

    Args:
        index (c_int): Index of fault simulation.

    Returns:
        string (c_char_p)
    """
    return FaultDescriptionEx(index, 0)

def ErrorString():
    """Retrieves error message string
    Returns:
        string (c_char_p)
    """
    ASPENOlxAPIDLL.OlxAPIErrorString.restype = c_char_p
    return decode( ASPENOlxAPIDLL.OlxAPIErrorString() )

def PrintObj1LPF(hnd):
    """Return a text description of network database object
       (bus, generator, load, shunt, switched shunt, transmission line,
       transformer, switch, phase shifter, distance relay,
       overcurrent relay, fuse, recloser, relay group)

    Args:
        hnd (c_int): object handle

    Returns:
        string (c_char_p)
    """
    ASPENOlxAPIDLL.OlxAPIPrintObj1LPF.argstype = [c_int]
    ASPENOlxAPIDLL.OlxAPIPrintObj1LPF.restype = c_char_p
    return decode(ASPENOlxAPIDLL.OlxAPIPrintObj1LPF(hnd))

def FullBusName(hnd):
    """Return string composed of name and kV of the given bus

    Args:
        hnd (c_int): Bus handle

    Returns:
        string (c_char_p)
    """
    ASPENOlxAPIDLL.OlxAPIFullBusName.restype = c_char_p
    ASPENOlxAPIDLL.OlxAPIFullBusName.argstype = [c_int]
    return decode( ASPENOlxAPIDLL.OlxAPIFullBusName(hnd) )

def FullBranchName(hnd):
    """Return a string composed of Bus, Bus2, Circuit ID and type
    of a branch object

    Args:
        hnd (c_int): Branch object handle

    Returns:
        string (c_char_p)
    """
    ASPENOlxAPIDLL.OlxAPIFullBranchName.restype = c_char_p
    ASPENOlxAPIDLL.OlxAPIFullBranchName.argstype = [c_int]
    return decode( ASPENOlxAPIDLL.OlxAPIFullBranchName(hnd) )

def FullRelayName(hnd):
    """Return a string composed of relay type, name and branch location

    Args:
        hnd (c_int): relay object handle

    Returns:
        string (c_char_p)
    """
    ASPENOlxAPIDLL.OlxAPIFullRelayName.restype = c_char_p
    ASPENOlxAPIDLL.OlxAPIFullRelayName.argstype = [c_int]
    return decode( ASPENOlxAPIDLL.OlxAPIFullRelayName(hnd) )

def GetObjJournalRecord(hnd):
    """Retrieve journal jounal record details of a data object in the OLR file.

    Args:
        hnd (c_int): object handle

    Returns:
        JRec (c_char_p): String of journal record fields, separated by new line character:
            -	Create date and time
            -	Created by
            -	Last modified date and time
            -	Modified by

    """
    ASPENOlxAPIDLL.OlxAPIGetObjJournalRecord.argstype = [c_int]
    ASPENOlxAPIDLL.OlxAPIGetObjJournalRecord.restype = c_char_p
    return decode( ASPENOlxAPIDLL.OlxAPIGetObjJournalRecord(hnd) )

def GetObjTags(hnd):
    """Retrieve tag string for a bus, generator, load, shunt, switched shunt,
       transmission line, transformer, switch, phase shifter, distance relay,
       overcurrent relay, fuse, recloser, relay group.

    Args:
        hnd (c_int): object handle

    Returns:
        tags (c_char_p): Tag string

    Note: if the funtion fails to execute the return string will consist of
          error message that begins with the key words: "GetObjTags failure:..."
    """
    ASPENOlxAPIDLL.OlxAPIGetObjTags.argstype = [c_int]
    ASPENOlxAPIDLL.OlxAPIGetObjTags.restype = c_char_p
    return decode( ASPENOlxAPIDLL.OlxAPIGetObjTags(hnd) )

def GetObjMemo(hnd):
    """Retrieve memo string for a bus, generator, load, shunt, switched shunt,
       transmission line, transformer, switch, phase shifter, distance relay,
       overcurrent relay, fuse, recloser, relay group.

    Args:
        hnd (c_int): object handle

    Returns:
        memo (c_char_p): Memo string

    Remarks: if the funtion fails to execute the return string will consist of
          error message that begins with the key words: "GetObjTags failure:..."
    """
    ASPENOlxAPIDLL.OlxAPIGetObjMemo.argstype = [c_int]
    ASPENOlxAPIDLL.OlxAPIGetObjMemo.restype = c_char_p
    return decode( ASPENOlxAPIDLL.OlxAPIGetObjMemo(hnd) )

def SetObjMemo(hnd,memo):
    """Assign memo string for a bus, generator, load, shunt, switched shunt,
       transmission line, transformer, switch, phase shifter, distance relay,
       overcurrent relay, fuse, recloser, relay group.

    Args:
        hnd (c_int): object handle
        memo (c_char_p): Memo string

    Returns:
        OLXAPI_FAILURE: Failure
        OLXAPI_OK     : Success

    Remarks: Line breaks must be included in the memo string as escape
       charater \n
    """
    ASPENOlxAPIDLL.OlxAPISetObjMemo.argstype = [c_int,c_char_p]
    ASPENOlxAPIDLL.OlxAPISetObjMemo.restype = c_int
    return ASPENOlxAPIDLL.OlxAPISetObjMemo(hnd,encode3(memo))


def SetObjTags(hnd,tags):
    """Assign tag string for a bus, generator, load, shunt, switched shunt,
       transmission line, transformer, switch, phase shifter, distance relay,
       overcurrent relay, fuse, recloser, relay group.

    Args:
        hnd (c_int): object handle
        tags (c_char_p): tag string

    Returns:
        OLXAPI_FAILURE: Failure
        OLXAPI_OK     : Success

    Remarks: tags string must be terminated with ; character
    """
    ASPENOlxAPIDLL.OlxAPISetObjTags.argstype = [c_int,c_char_p]
    ASPENOlxAPIDLL.OlxAPISetObjTags.restype = c_int
    return ASPENOlxAPIDLL.OlxAPISetObjTags(hnd,encode3(tags))

def MakeOutageList(hnd, maxTiers, wantedTypes, branchList, listLen):
    """Return list of neighboring branches that can be used as outage list
       in calling the DoFault function on a bus, branch or relay group.

    Args:
        hnd	(c_int): handle of a bus, branch or a relay group.
        maxTiers (c_int): Number of tiers (must be positive)
        wantedTypes (c_int): Branch type to comsider. Sum of one or more
             following values: 1- Line; 2- 2-winding transformer;
             4- Phase shifter; 8- 3-winding transformer; 16- Switch
        branchList (c_void_p): [in] array of c_int*listLen+1 or none
                               [out] zero-terminated list of branch handles.
        listLen (pointer(c_int)): [in] pointer to c_int with length of branchList array
                                  [out] Number of outage branches found.

    Remarks:
        Calling this function with None in place of branchList will let you determine the
        number of outage branches in the number of tiers specified.

    Returns:
        OLXAPI_FAILURE: Failure
        OLXAPI_OK     : Success

    """
    ASPENOlxAPIDLL.OlxAPIMakeOutageList.argtypes = [c_int,c_int,c_int,c_void_p,c_void_p]
    return ASPENOlxAPIDLL.OlxAPIMakeOutageList(hnd, maxTiers, wantedTypes, branchList, listLen)

def ComputeRelayTime(hnd, curMag, curAng, vMag, vAng,vpreMag, vpreAng, opTime, opDevice):
    """Computes operating time for a fuse, recloser, an overcurrent relay (phase or ground),
       or a distance relay (phase or ground) at given currents and voltages.

    Args:
        hnd (c_int): relay object handle
        curMag (c_double*5) [in] array of relay current magnitude in amperes of
                    phase A, B, C, and if applicable, Io currents in neutral
                    of transformer windings P and S.
        curAng (c_double*5):  [in] array of relay current angles in degrees
        vMag (c_double*3):    [in] array of relay voltage magnitude in, line to neutral, in kV
                    of phase A, B and C
        vdVAng (c_double*3): [in] array of relay voltage angle
        vpreMag (c_double): [in] relay pre-fault positive sequence voltage magnitude in kV, line to neutral
        dVpreAng (c_double): [in] relay pre-fault positive sequence voltage angle in degrees
        opTime (pointer(c_double)): [out] relay operating time in seconds
        opDevice (c_char*128): [out] relay operation code:
                            NOP  No operation
                            ZGn  Ground distance zone n  tripped
                            ZPn  Phase distance zone n  tripped
                            Ix    Overcurrent relay operating quantity: Ia, Ib, Ic, Io, I2, 3Io, 3I2
    Returns:
        OLXAPI_FAILURE: Failure
        OLXAPI_OK     : Success
    """
    ASPENOlxAPIDLL.OlxAPIMakeOutageList.argtypes = [c_int,c_double*5,c_double*5,c_double*3,c_double*3,c_double,c_double,c_void_p,c_char*128]
    return ASPENOlxAPIDLL.OlxAPIComputeRelayTime(hnd, curMag, curAng, vMag, vAng,vpreMag, vpreAng, opTime, opDevice)


def FindObj1LPF(obj1LPFStr, hnd):
    """Returns handle number of the object in obj1LPFStr string
    Args:
      obj1LPFStr   [in] Object ID string produced by PrintObj1LPF() or
                        the object GUID
      hnd         [out] Object handle number.
    Returns:
        OLXAPI_FAILURE: Failure
        OLXAPI_OK     : Success
    """
    ASPENOlxAPIDLL.OlxAPIFindObj1LPF.argtypes = [c_char_p, POINTER(c_int)]
    return ASPENOlxAPIDLL.OlxAPIFindObj1LPF(encode3(obj1LPFStr),hnd)

def GetObjUDFByIndex(hnd,fidx,fname,fval):
    """Retrieve user-defined field of an object.
    Args:
      hnd (c_int)             [in] Object handle
      nFIdx (c_int)           [in] Field index number (zero based)
      fname (c_char*MXUDF)    [out] Buffer for field name. Must be MXUDFNAME long. Set to NULL if not needed.
      fval (c_char*MXUDFNAME) [out] Buffer for field value. Must be MXUDF long. Set to NULL if not needed.
    Returns:
      OLXAPI_OK     : Success
      OLXAPI_FAILURE: Field with the given index does not exist
   """
    ASPENOlxAPIDLL.OlxAPIGetObjUDFByIndex.argtypes = [c_int,c_int,c_char*(MXUDFNAME+1),c_char*(MXUDF+1)]
    return ASPENOlxAPIDLL.OlxAPIGetObjUDFByIndex(hnd,fidx,fname,fval)

def GetObjUDF(hnd, fname, fval):
    """Retrieve the value of a user-defined field.
    Parameters:
        hnd (c_int)             [in] Object handle
        fname (c_char_p)        [in] Field name
        fval (c_char*MXUDFNAME) [out] Buffer for field value. Must be MXUDF long
    Returns:
        OLXAPI_OK     : Success
        OLXAPI_FAILURE: Object does not have UDF Field with the given name
    """
    ASPENOlxAPIDLL.OlxAPIGetObjUDF.argtypes = [c_int,c_char_p,c_char*(MXUDF+1)]
    return ASPENOlxAPIDLL.OlxAPIGetObjUDF(hnd,encode3(fname),fval)

def SetObjUDF(hnd, fname, fval):
    """Set the value of a user-defined field.
    Parameters:
        hnd (c_int)       [in] Object handle
        fname (c_char_p)  [in] Field name
        fval (c_char_p)   [in] Field value
    Returns:
        OLXAPI_OK     : Success
        OLXAPI_FAILURE: Object does not have UDF Field with the given name
    """
    ASPENOlxAPIDLL.OlxAPISetObjUDF.argtypes = [c_int,c_char_p,c_char_p]
    return ASPENOlxAPIDLL.OlxAPISetObjUDF(hnd,encode3(fname),encode3(fval))

def GetAreaName(no):
    """Retrieve name of the given area number.
    Args:
        no (c_int): Area number
    Returns:
        name (c_char_p): Name string
    Remarks: if the funtion fails to execute the return string will consist of
          error message that begins with the key words: "GetAreaName failure:..."
    """
    ASPENOlxAPIDLL.OlxAPIAreaName.argstype = [c_int]
    ASPENOlxAPIDLL.OlxAPIAreaName.restype = c_char_p
    return decode( ASPENOlxAPIDLL.OlxAPIGetAreaName(hnd) )

def GetZoneName(no):
    """Retrieve name of the given area number.
    Args:
        no (c_int): Zone number
    Returns:
        name (c_char_p): Name string
    Remarks: if the funtion fails to execute the return string will consist of
          error message that begins with the key words: "GetZoneName failure:..."
    """
    ASPENOlxAPIDLL.OlxAPIZoneName.argstype = [c_int]
    ASPENOlxAPIDLL.OlxAPIZoneName.restype = c_char_p
    return decode( ASPENOlxAPIDLL.OlxAPIGetZoneName(hnd) )

def GetObjGUID(hnd):
    """Retrieve name of the given area number.
    Args:
        hnd (c_int)  [in] Object handle
    Returns:
        guid (c_char_p): GUID string
    Remarks: if the funtion fails to execute the return string will consist of
          error message that begins with the key words: "GetObjGUID failure:..."
    """
    ASPENOlxAPIDLL.OlxAPIGetObjGUID.argstype = [c_int]
    ASPENOlxAPIDLL.OlxAPIGetObjGUID.restype = c_char_p
    return decode( ASPENOlxAPIDLL.OlxAPIGetObjGUID(hnd) )

def OlxAPIEliminateZZBranch( hnd, nOption, pOutBuf ):
    """ Eliminate switch and zmall impeance line and merge two end bues
        if the switch is closed
    Args:
        hnd (c_int)     Switch or line handle
        nOption (c_int) Bit 1: Repeat for all connected switches and lines
                        Bit 2: Output list of retained bus handles (-1 terminated)
                        Bit 3: Output list of eliminated bus handles (-1 terminated)
                        Bit 4: Also eliminate small impedance lines
        pOutBuf   [out] Buffer for outputs. Can be NULL.
    Returns:
        OLXAPI_OK     : Success
        OLXAPI_FAILURE: Failure
    Remarks: None
    """
    ASPENOlxAPIDLL.OlxAPIEliminateZZBranch.argstype = [c_int,c_int,c_void_p]
    ASPENOlxAPIDLL.OlxAPIEliminateZZBranch.restype = c_int
    return ASPENOlxAPIDLL.OlxAPIEliminateZZBranch(hnd, nOption, byref(pOutBuf))
