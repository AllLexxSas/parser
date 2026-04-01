import NXOpen
import NXOpen.CAM


import CSEWrapper

from CSEWrapper import Matrix4
from CSEWrapper import ChannelState


import math
import os.path
import os
import pathlib
import re

def DisplayNxMessage(msg:str):

    theUI = NXOpen.UI.GetUI()
    theUI.NXMessageBox.Show("Message", NXOpen.NXMessageBoxDialogType.Error ,"Не задан параметр цикла {} ", msg )
    return True 

def DisplayMessage1(msg: str):
    lw = GetSession().ListingWindow

    if lw.IsOpen == False:
        lw.Open()
    lw.WriteLine(str(msg))
    return True

def DisplayMessage(x,y,z):
    lw = GetSession().ListingWindow

    if lw.IsOpen == False:
        lw.Open()
    lw.WriteLine('x = '+str(x) + ' y = ' + str(y)+ ' z = ' + str(z))
    return True


def FindToolName(operName: str):
    part = GetPart();
    oper = FindOperationByName(operName);
    tool = oper.GetParent(NXOpen.CAM.CAMSetup.View.MachineTool);
    head = tool.GetParent().Name;
    return [tool.Name, head]

def GetZOffset(channel, operName: str):
    oper = FindOperationByName(operName);
    nc = oper.GetParent(NXOpen.CAM.CAMSetup.View.ProgramOrder);
    ude = None

    while ude == None:
        builder = CreateGroupBuilder(nc)
        listUDE = builder.StartUdeSet.UdeList.GetContents()
        #DisplayMessage(str(listUDE))
        ude = FiandUdeByName(listUDE)
        if ude == None:
            nc = nc.GetParent()
    #channle.SetVariable("#77777",float( ude.GetParameter("Z_offset").DoubleValue))
    GetTrafoMatirx(channel,"FIXED2",float( ude.GetParameter("Z_offset").DoubleValue))
    SetWTransformation(channel)
    channel.SetTargetJointValue("W",-220)
    #DisplayMessage(str(ude.GetParameter("Z_offset").DoubleValue))

    return True

def GetVariable(channel):
    if channel.GetChannelName() == '1':
        return
    part = GetPart()
    full_path = part.FullPath
    p = pathlib.Path(full_path)
    p.is_file()
    n = 'cse_files\subprog'
    ff = pathlib.Path( p.parents[0] , n)
    ff.mkdir(parents=True, exist_ok=True)
    f = ff /'zoffset.ini'
    fi = None
    if os.path.exists(f) == False:
        try:
            fi = open(f , 'w')
            fi.write('#99999 = 100(вылет детали из SUB - шпинделя)\n')
            fi.write('#99998 = 100(длина детали)\n')

            channel.SetVariable('#99999', 100)
            fi.close()
            #DisplayMessage1('file '+ str(f) +' not created')
            theUI = NXOpen.UI.GetUI()
            theUI.NXMessageBox.Show("Message", NXOpen.NXMessageBoxDialogType.Information , "Для настройки привязки противошпирделя нужно задать два параметра: Длину детали и вылет детали из котр-шпинделя\r\n"+
                                    "Для этого, при первом запуске симуляции, в папке с проектом по пути: \'\\cse_files\subprog\\\' создается файл zoffset.ini, в котором будут две переменные:\r\n"+
                                   "#99999 = 100 - вылет детали из SUB - шпинделя\r\n"+
                                   "#99998 = 100 - длина детали\r\n"+
                                   "Задайте необходимые параметры в файле, сохраните файл и перезапустите симуляцию");
        except OSError:
            DisplayMessage1('file '+ str(f) +' not created')
        else:
            DisplayMessage1('file created')

    else:
        if channel.GetChannelName() == '2':
            #fi = open(f,'r')
            #strr = fi.read().split('=')
            with  open(f,'r') as f:
                ddd = f.read().splitlines()
            for s_param in ddd:
                ser = re.findall(r"#?[+-]?\d+[.]?\d+", s_param)
                #DisplayMessage1(str(ser))
                channel.SetVariable(ser[0], float(ser[1]))





    return True



def FiandUdeByName(udelist):
    ude = None
    for item in udelist:
        if item.UdeName =='UZ_Z_OFFSET':
            ude = item
    return ude
        




def GetSession():
    return NXOpen.Session.GetSession()

def GetPart():
    return GetSession().Parts.Work

def FindOperationByName(operName: str):
    return GetPart().CAMSetup.CAMOperationCollection.FindObject(operName)

def CreateGroupBuilder(nCGroup):
    return GetPart().CAMSetup.CAMGroupCollection.CreateProgramOrderGroupBuilder(nCGroup)


def GetTrafoMatirx(channle, nameTrafo, offset):
    trafoMatrix = channle.GetTransformationMatrix(nameTrafo)
    trafoMatrix.mat[3][2] =abs(offset)
    channle.ActivateTransformation(nameTrafo,False,False)
    channle.ResetTransformation(nameTrafo)
    channle.SetTransformationMatrix(nameTrafo , trafoMatrix)
    channle.ActivateTransformation(nameTrafo,True,True)

    return True

def SetWTransformation(channle):
    matrix = Matrix4();
    matrix.mat[3][2] = 220
    channle.ActivateTransformation("TrafoW",False,False)
    channle.ResetTransformation("TrafoW")
    channle.SetTransformationMatrix("TrafoW" , matrix)
    channle.ActivateTransformation("TrafoW",True,True)

    return True




theSession = NXOpen.Session.GetSession()
part = theSession.Parts.Work         
lw = theSession.ListingWindow
lw.Open()




def GetTratsList(channel):
     listTransf = channel.GetTransformationList();
     #listTransf = {"TRANSY","EXTOFFSET","ROT_C","TABLEROTATE","TOOLROTATE","FIXED","FIXEDADDITIONAL","ADDITIONAL","ROTAT_HEAD","ROTATIONAL",
      #             "$TOOL","POLARMODE1","POLARMODE2","POLARMODE3","POLARMODE4"}
     PrintListTrans(channel,listTransf)

def PrintListTrans(channel,l: list):
    for i in l:
        lw.WriteLine('{0}  {1}'.format(i,channel.IsTransformationActive(i)))
        if i == '$KIN':
            lw.WriteLine("________________")
        if i != '$KIN':
            if i != 'TRANSY' :
                PrintMatrix4(channel,i)
        
def PrintMatrix4(channel,nameMatrix: str):
    #lw.WriteLine('{0}  {1}'.format(nameMatrix,channel.IsTransformationActive(nameMatrix)))
    if channel.IsTransformationActive(nameMatrix):
        
        tempMatrix = channel.GetTransformationMatrix(nameMatrix)
        lw.WriteLine(nameMatrix)
        PrintMatrix(tempMatrix)
        
        #lw.WriteLine('{0} = {1}'.format(nameMatrix,str(tempMatrix.mat)))
        #lw.WriteLine(str(channel.DoesTransformationExist(nameMatrix)));
        return True

def PrintMatrix (tempMatrix: Matrix4):
    for value in tempMatrix.mat:            
            lw.WriteLine('{0} {1} {2} {3}'.format(round(value[0],3),round(value[1],3),round(value[2],3),round(value[3],3)))

    lw.WriteLine("-----------------------------")


#motods fot g76

def XZPositionInVariable(ch):
    z_name = 'Z1' if ch.GetChannelName() == '1' else 'Z2'
    x_name = 'X1' if ch.GetChannelName() == '1' else 'X2'

    x = GetTargetJointValue(ch,x_name)
    z = GetTargetJointValue(ch, z_name)
    SetVariable(ch,"#90024", x*2)
    SetVariable(ch,"#90026", z)
    return True

def GetTargetJointValue(ch , axisName):
    return ch.GetTargetJointValue(axisName)

def SetVariable(ch, variableName, value):
    ch.SetVariable(variableName,value)




