from socket import timeout
from PyQt5 import QtWidgets
from PyQt5.QtWidgets import (QFileDialog)
from SetPostureHumanoidUI_QT5 import Ui_Form
import time
import serial
import sys
import serial.tools.list_ports
from configobj import ConfigObj

class HumanoidMainWindow(QtWidgets.QMainWindow,Ui_Form):
    int_id_L =[1,2,3,4,5,6]
    int_id_R =[11,12,13,14,15,16]
    int_id_LArm =[21,22,23]
    int_id_RArm =[31,32,33]
    int_id_H =[41,42,43]
    int_id_All = int_id_L + int_id_R + int_id_LArm + int_id_RArm
    #int_id_All = int_id_L + int_id_R + int_id_LArm + int_id_RArm + int_id_H

    int_motor_Amount = 23
    int_keyframe_Amount = 30
    int_time_Initial = 20

    def __init__(self, parent=None):
        super(HumanoidMainWindow, self).__init__(parent)
        self.ui = Ui_Form()
        self.ui.setupUi(self)
        self.InitVariable()
        self.InitUI()
        self.SetButtonAndSpinCtrlDisable()
        self.setReadMotorPacket(1,0x84,0x04)


    def InitVariable(self):

        self.config_setup = ConfigObj("setup.ini")
        print(self.config_setup)
        self.str_fileName = self.config_setup['fileName']
        self.str_baudrate = self.config_setup['baudrate']

        self.int_stepTime = 0.03
        self.str_keyframeSelected ='Keyframe1'
        self.int_keyframeSelected = 1
        self.bool_comportConnected = False
        self.int_numberOfKeyframe = 0
        self.str_postureName = 'center'
        self.str_comport = None
        self.int_keyframe = 0
        self.int_motorID = 0
        self.bool_activeKeyframe =[False for x in range (self.int_keyframe_Amount)]

        self.ui.fileName_label.setText(self.str_fileName)
        config_default = ConfigObj(self.str_fileName)
        self.config_current = config_default


        self.str_motorType = config_default['motors type']['left leg'] + config_default['motors type']['right leg'] + \
                             config_default['motors type']['left arm'] + config_default['motors type']['right arm'] + \
                             config_default['motors type']['head']
        #print(self.str_motorType)
        self.int_motorCenterValue = config_default['motors center']['left leg'] + config_default['motors center'][
            'right leg'] + config_default['motors center']['left arm'] + config_default['motors center']['right arm'] + \
                                    config_default['motors center']['head']
        #print(self.int_motorCenterValue)

        self.int_motorCenterValue = [int(self.int_motorCenterValue[x]) for x in range (self.int_motor_Amount)]


        self.int_old_motorValue = [self.int_motorCenterValue[x] for x in range (self.int_motor_Amount)]
        self.int_backup_motorValue = [self.int_motorCenterValue[x] for x in range (self.int_motor_Amount)]
        self.int_motorValue = [[self.int_motorCenterValue[x] for x in range (self.int_motor_Amount)] for y in range (self.int_keyframe_Amount)]

        self.dic_motorIndexID = {'id1':0,'id2':1,'id3':2,'id4':3,'id5':4,'id6':5,
                                 'id11':6,'id12':7,'id13':8,'id14':9,'id15':10,'id16':11,
                                 'id21':12,'id22':13,'id23':14,'id24':15,
                                 'id31':16,'id32':17,'id33':18,'id34':19,
                                 'id41':20,'id42':21,'id43':22}
        self.int_time = [self.int_time_Initial for x in range (self.int_keyframe_Amount)]






    def InitUI(self):

        self.SetMotorCenterLabel()

        baudrateList = ['9600','115200','1000000']
        self.ui.baudrate_comboBox.addItems(baudrateList)
        self.ui.baudrate_comboBox.setCurrentIndex(baudrateList.index(self.str_baudrate))

        self.postureList = ['center','front_getup','back_getup','p1','p2','p3']
        self.ui.posture_comboBox.addItems(self.postureList)

        self.keyframeList = [str(i) for i in range(1, 31)]

        self.ui.keyFrame_comboBox.addItems(self.keyframeList)

        self.ui.connectionStatus_label.setText("Status : Disconnect")

        self.ui.activeKeyframe_checkBox.clicked.connect(self.ActiveKeyframe_CheckBox)
        self.ui.keyFrame_comboBox.activated[str].connect(self.OnSelect_ComboboxKeyframe)
        self.ui.posture_comboBox.activated[str].connect(self.OnSelect_ComboboxPosture)
        self.ui.comport_comboBox.activated[str].connect(self.OnSelect_ComboboxComport)
        self.ui.baudrate_comboBox.activated[str].connect(self.OnSelect_ComboboxBaudrate)

        self.ui.comport_comboBox.currentIndexChanged[str].connect(self.OnIndexChange_ComboboxComport)

        self.ui.connect_Button.clicked.connect(self.OnButton_connect)
        self.ui.loadPosture_pushButton.clicked.connect(self.OnButton_Load)
        self.ui.savePosture_pushButton.clicked.connect(self.OnButton_Save)
        self.ui.setReady_Button.clicked.connect(self.OnButton_ready)
        self.ui.playAll_Button.clicked.connect(self.OnButton_playAll)
        self.ui.setTime_pushButton.clicked.connect(self.OnButton_time)
        self.ui.play_pushButton.clicked.connect(self.OnButton_play)

        self.ui.setAll_pushButton.clicked.connect(self.OnButton_setAll)
        self.ui.setLAll_pushButton.clicked.connect(self.OnButton_setLAll)
        self.ui.setRAll_pushButton.clicked.connect(self.OnButton_setRAll)
        self.ui.setLArmAll_pushButton.clicked.connect(self.OnButton_setLArmAll)
        self.ui.setRArmAll_pushButton.clicked.connect(self.OnButton_setRArmAll)
        self.ui.setHAll_pushButton.clicked.connect(self.OnButton_setHAll)

        ### set text motor type ###
        for id in self.int_id_All:
            eval("self.ui.motorType{}_label".format(id)).setText(self.str_motorType[self.dic_motorIndexID['id'+str(id)]])


        for id in self.int_id_All:
            eval("self.ui.motor{}Set_pushButton".format(id)).clicked.connect(lambda ignore, id=id: self.OnButton_Set(id))

            #QtCore.QObject.connect(getattr(self.ui,'motor'+str(i)+'Set_pushButton'),QtCore.SIGNAL("clicked()"), getattr(self,'OnButton_id'+str(i)+'Set'))
        ###### QtCore.QObject.connect(self.ui.motor1Set_pushButton,QtCore.SIGNAL("clicked()"), self.OnButton_id1Set)


        self.ui.getAll_pushButton.clicked.connect(self.OnButton_getAll)
        self.ui.getLAll_pushButton.clicked.connect(self.OnButton_getLAll)
        self.ui.getRAll_pushButton.clicked.connect(self.OnButton_getRAll)
        self.ui.getLArmAll_pushButton.clicked.connect(self.OnButton_getLArmAll)
        self.ui.getRArmAll_pushButton.clicked.connect(self.OnButton_getRArmAll)
        self.ui.getHAll_pushButton.clicked.connect(self.OnButton_getHAll)

        for id in self.int_id_All:
            eval("self.ui.motor{}Get_pushButton".format(id)).clicked.connect(
                lambda ignore, id=id: self.OnButton_Get(id))

            #QtCore.QObject.connect(getattr(self.ui,'motor'+str(i)+'Get_pushButton'),QtCore.SIGNAL("clicked()"), getattr(self,'OnButton_id'+str(i)+'Get'))


        self.ui.disTAll_pushButton.clicked.connect(self.OnButton_DisableTorqueAll)
        self.ui.disTLAll_pushButton.clicked.connect(self.OnButton_DisableTorqueLAll)
        self.ui.disTRAll_pushButton.clicked.connect(self.OnButton_DisableTorqueRAll)
        self.ui.disTLArmAll_pushButton.clicked.connect(self.OnButton_DisableTorqueLArmAll)
        self.ui.disTRArmAll_pushButton.clicked.connect(self.OnButton_DisableTorqueRArmAll)
        self.ui.disTHAll_pushButton.clicked.connect(self.OnButton_DisableTorqueHAll)

        ######QtCore.QObject.connect(self.ui.motor1DisT_pushButton,QtCore.SIGNAL("clicked()"), self.OnButton_id1DisableTorque)
        for id in self.int_id_All:
            eval("self.ui.motor{}DisT_pushButton".format(id)).clicked.connect(
                lambda ignore, id=id: self.OnButton_DisableTorque(id))

            #QtCore.QObject.connect(getattr(self.ui,'motor'+str(i)+'DisT_pushButton'),QtCore.SIGNAL("clicked()"), getattr(self,'OnButton_id'+str(i)+'DisableTorque'))

        self.ui.saveCenter_pushButton.clicked.connect(self.OnButton_SaveCenter)

        self.Search_Comport()

        self.ui.saveFile_pushButton.clicked.connect(self.OnButton_saveFile)
        self.ui.loadFile_pushButton.clicked.connect(self.OnButton_loadFile)
        self.ui.generateGetupFile_pushButton.clicked.connect(self.OnButton_generateGetupFIle)


    def OnButton_generateGetupFIle(self):
        fileName = self.str_fileName
        fileName = fileName.replace('.ini','.txt')
        #print(self.str_fileName)
        #print(fileName)
        file = open(fileName,'w')
        file.write('/////*** Motors Type Declaration ***/////\n')
        file.write('char c_MotorLeftLeg_Type[c_MotorLeftLeg_Amount] = {')
        last = len(self.config_current['motors type']['left leg']) - 1
        for i, item in enumerate(self.config_current['motors type']['left leg']):
            file.write("'" +str(item.replace('X','')) +"'")
            if i == last:
                file.write(' }; /// ID :: ' + str(self.int_id_L) + ' ///\n')
                break
            else: file.write((' ,'))
        file.write('char c_MotorRightLeg_Type[c_MotorRightLeg_Amount] = {')
        for i, item in enumerate(self.config_current['motors type']['right leg']):
            file.write("'" +str(item.replace('X','')) +"'")
            if i == last:
                file.write(' }; /// ID :: ' + str(self.int_id_R) + ' ///\n')
                break
            else: file.write((' ,'))

        last = len(self.config_current['motors type']['left arm']) - 2
        file.write('char c_MotorLeftArm_Type[c_MotorLeftArm_Amount] = {')
        for i, item in enumerate(self.config_current['motors type']['left arm']):
            file.write("'" + str(item.replace('X', '')) + "'")
            if i == last:
                file.write(' }; /// ID :: ' + str(self.int_id_LArm[:-1]) + ' ///\n')
                break
            else:
                file.write((' ,'))
        file.write('char c_MotorRightArm_Type[c_MotorRightArm_Amount] = {')
        for i, item in enumerate(self.config_current['motors type']['right arm']):
            file.write("'" + str(item.replace('X', '')) + "'")
            if i == last:
                file.write(' }; /// ID :: ' + str(self.int_id_RArm[:-1]) + ' ///\n')
                break
            else:
                file.write((' ,'))

        file.write('\n\n/////*** Motors Center Value Declaration ***/////\n')
        file.write('int i_MotorLeftLeg_Value_Center[c_MotorLeftLeg_Amount] = {')
        last = len(self.config_current['motors center']['left leg']) - 1
        for i, item in enumerate(self.config_current['motors center']['left leg']):
            print("item = ", item)
            file.write(str(item.replace('X', '')))
            if i == last:
                file.write(' }; /// ID :: ' + str(self.int_id_L) + ' ///\n')
                break
            else:
                file.write((' ,'))
        file.write('int i_MotorRightLeg_Value_Center[c_MotorRightLeg_Amount] = {')
        for i, item in enumerate(self.config_current['motors center']['right leg']):
            file.write(str(item.replace('X', '')))
            if i == last:
                file.write(' }; /// ID :: ' + str(self.int_id_R) + ' ///\n')
                break
            else:
                file.write((' ,'))

        last = len(self.config_current['motors center']['left arm']) - 2
        file.write('int i_MotorLeftArm_Value_Center[c_MotorLeftArm_Amount] = {')
        for i, item in enumerate(self.config_current['motors center']['left arm']):
            file.write(str(item.replace('X', '')))
            if i == last:
                file.write(' }; /// ID :: ' + str(self.int_id_LArm[:-1]) + ' ///\n')
                break
            else:
                file.write((' ,'))
        file.write('int i_MotorRightArm_Value_Center[c_MotorRightArm_Amount] = {')
        for i, item in enumerate(self.config_current['motors center']['right arm']):
            file.write(str(item.replace('X', '')))
            if i == last:
                file.write(' }; /// ID :: ' + str(self.int_id_RArm[:-1]) + ' ///\n')
                break
            else:
                file.write((' ,'))

        motor_valur_index = [0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,16,17,18]
        file.write('\n\n/////*** Getup ***/////\n')
        #file.write('const int i_Motion_Parameter_Amount = 19;\n')
        #file.write('const int i_Motion_Parameter_Time_Index = i_Motion_Parameter_Amount - 1;\n')
        file.write('/////*** Front Getup ***/////\n')
        file.write('const int i_Motion_FrontGetup_State_Amount = ' +str(self.config_current['front_getup']['Keyframe_Amount']) +';\n')
        file.write('float f_Motion_FrontGetup_State_Parameter[i_Motion_FrontGetup_State_Amount][i_Motion_Parameter_Amount] = {\n')
        for i in range(int(self.config_current['front_getup']['Keyframe_Amount'])):
            file.write('{')
            for j in motor_valur_index:
                #print(self.config_current['front_getup']['Keyframe_Value']['Keyframe_' + str(i)][j])
                file.write(str(self.config_current['front_getup']['Keyframe_Value']['Keyframe_' + str(i)][j] + ', '))

            file.write('/*Time*/  ' + str(self.config_current['front_getup']['Keyframe_Time'][i]) + '*0.1')
            if(i == int(self.config_current['front_getup']['Keyframe_Amount']) -1): file.write('}\n};\n')
            else: file.write('},\n')


        file.write('/////*** Back Getup ***/////\n')
        file.write('const int i_Motion_BackGetup_State_Amount = ' + str(self.config_current['back_getup']['Keyframe_Amount']) + ';\n')
        file.write('float f_Motion_BackGetup_State_Parameter[i_Motion_BackGetup_State_Amount][i_Motion_Parameter_Amount] = {\n')
        for i in range(int(self.config_current['back_getup']['Keyframe_Amount'])):
            file.write('{')
            for j in motor_valur_index:
                #print(self.config_current['back_getup']['Keyframe_Value']['Keyframe_' + str(i)][j])
                file.write(str(self.config_current['back_getup']['Keyframe_Value']['Keyframe_' + str(i)][j] + ', '))

            file.write('/*Time*/  ' + str(self.config_current['back_getup']['Keyframe_Time'][i]) + '*0.1')
            if(i == int(self.config_current['back_getup']['Keyframe_Amount']) -1): file.write('}\n};\n')
            else: file.write('},\n')

    

        file.write('/////*** MOTION SPECIAL 1 ***/////\n')
        file.write('const int i_Motion_Special_1_State_Amount = ' + str(self.config_current['p1']['Keyframe_Amount']) + ';\n')
        file.write('float f_Motion_Special_1_State_Parameter[i_Motion_Special_1_State_Amount][i_Motion_Parameter_Amount] = {\n')
        for i in range(int(self.config_current['p1']['Keyframe_Amount'])):
            file.write('{')
            for j in motor_valur_index:
                #print(self.config_current['back_getup']['Keyframe_Value']['Keyframe_' + str(i)][j])
                file.write(str(self.config_current['p1']['Keyframe_Value']['Keyframe_' + str(i)][j] + ', '))

            file.write('/*Time*/  ' + str(self.config_current['p1']['Keyframe_Time'][i]) + '*0.1')
            if(i == int(self.config_current['p1']['Keyframe_Amount']) -1): file.write('}\n};\n')
            else: file.write('},\n')

        file.write('/////*** MOTION SPECIAL 2 ***/////\n')
        file.write('const int i_Motion_Special_2_State_Amount = ' + str(self.config_current['p2']['Keyframe_Amount']) + ';\n')
        file.write('float f_Motion_Special_2_State_Parameter[i_Motion_Special_2_State_Amount][i_Motion_Parameter_Amount] = {\n')
        for i in range(int(self.config_current['p2']['Keyframe_Amount'])):
            file.write('{')
            for j in motor_valur_index:
                #print(self.config_current['back_getup']['Keyframe_Value']['Keyframe_' + str(i)][j])
                file.write(str(self.config_current['p2']['Keyframe_Value']['Keyframe_' + str(i)][j] + ', '))

            file.write('/*Time*/  ' + str(self.config_current['p2']['Keyframe_Time'][i]) + '*0.1')
            if(i == int(self.config_current['p2']['Keyframe_Amount']) -1): file.write('}\n};\n')
            else: file.write('},\n')

        file.write('/////*** MOTION SPECIAL 3 ***/////\n')
        file.write('const int i_Motion_Special_3_State_Amount = ' + str(self.config_current['p3']['Keyframe_Amount']) + ';\n')
        file.write('float f_Motion_Special_3_State_Parameter[i_Motion_Special_3_State_Amount][i_Motion_Parameter_Amount] = {\n')
        for i in range(int(self.config_current['p3']['Keyframe_Amount'])):
            file.write('{')
            for j in motor_valur_index:
                #print(self.config_current['back_getup']['Keyframe_Value']['Keyframe_' + str(i)][j])
                file.write(str(self.config_current['p3']['Keyframe_Value']['Keyframe_' + str(i)][j] + ', '))

            file.write('/*Time*/  ' + str(self.config_current['p3']['Keyframe_Time'][i]) + '*0.1')
            if(i == int(self.config_current['p3']['Keyframe_Amount']) -1): file.write('}\n};\n')
            else: file.write('},\n')


        file.close()
        print("Finished generate getup file " + str(fileName))

    def OnButton_saveFile(self):
        fname = QFileDialog.getSaveFileName(self, 'Save file', './Postures/', "OBJ (*.ini)")

        print(fname)
        print("save file")
        if fname[0]:
            config = ConfigObj()
            config = self.config_current
            config.filename = fname[0]
            config.write()

            self.config_current = config

            self.ui.fileName_label.setText((fname[0].split("/")[len(fname[0].split("/")) - 1]))
            self.str_fileName = str(fname[0].split("/")[len(fname[0].split("/")) - 1])
            self.ui.fileName_label.setText(self.str_fileName)

            self.config_setup['fileName'] = self.str_fileName
            self.config_setup.write()

            self.OnButton_Load()

    def OnButton_loadFile(self):

        #self.str_fileName = 'mx_default.ini'

        fname = QFileDialog.getOpenFileName(self, 'Open file', './Postures', "OBJ (*.ini)")

        if fname[0]:
            f = open(fname[0], 'r')

            with f:
                print("file name", fname[0])
                config = ConfigObj(fname[0])

                self.config_current = config
                self.str_fileName = str(fname[0].split("/")[len(fname[0].split("/")) - 1])
                self.ui.fileName_label.setText(self.str_fileName)

                self.OnButton_Load()



                self.str_motorType = self.config_current['motors type']['left leg'] + self.config_current['motors type'][
                    'right leg'] + \
                                     self.config_current['motors type']['left arm'] + self.config_current['motors type'][
                                         'right arm'] + \
                                     self.config_current['motors type']['head']

                ### set text motor type ###
                for id in self.int_id_All:
                    eval("self.ui.motorType{}_label".format(id)).setText(
                        self.str_motorType[self.dic_motorIndexID['id' + str(id)]])


                self.config_setup['fileName'] = self.str_fileName
                self.config_setup.write()



    def Search_Comport(self):
        ports = list(serial.tools.list_ports.comports())
        for p in ports:
            self.ui.comport_comboBox.addItem(p[0])

    def OnIndexChange_ComboboxComport(self,text):
        self.str_comport = str(text)
        print(self.str_postureName)

    def OnButton_Delete(self):
        #self.ui.keyFrame_comboBox.
        #self.int_backup_motorValue
        #self.int_keyframeSelected
        pass

    def OnButton_DisableTorqueAll(self):
        for i in self.int_id_All:
            self.setDisableMotorTorque(i)
            time.sleep(0.015)

    def OnButton_DisableTorqueLAll(self):
        for i in self.int_id_L:
            self.setDisableMotorTorque(i)
            time.sleep(0.015)

    def OnButton_DisableTorqueRAll(self):
        for i in self.int_id_R:
            self.setDisableMotorTorque(i)
            time.sleep(0.015)

    def OnButton_DisableTorqueLArmAll(self):
        for i in self.int_id_LArm:
            self.setDisableMotorTorque(i)
            time.sleep(0.015)

    def OnButton_DisableTorqueRArmAll(self):
        for i in self.int_id_RArm:
            self.setDisableMotorTorque(i)
            time.sleep(0.015)

    def OnButton_DisableTorqueHAll(self):
        for i in self.int_id_H:
            self.setDisableMotorTorque(i)
        time.sleep(0.015)

    def OnButton_DisableTorque(self, id):
        print("DisableTorque ID " + str(id))
        self.setDisableMotorTorque(id)

    def OnButton_Get(self, id):
        print("get ID = " + str(id))
        value = self.getMotorPosition(id)
        if value == "error" :
            eval("self.ui.motor{}Set_pushButton.setDisabled(True)".format(id))
            eval("self.ui.motor{}Value_spinBox.setValue(9999)".format(id))
        else :
            eval("self.ui.motor{}Set_pushButton.setEnabled(True)".format(id))

            eval("self.ui.motor{}Value_spinBox.setValue(value)".format(id))

    def OnButton_getAll(self):
        print("getAll")
        for id in self.int_id_All:
            eval("self.ui.motor{}Value_spinBox.setValue(self.getMotorPosition(id))".format(id))
            time.sleep(0.015)

    def OnButton_getLAll(self):
        print("get_L_All")
        for id in self.int_id_L:
            eval("self.ui.motor{}Value_spinBox.setValue(self.getMotorPosition(id))".format(id))
            time.sleep(0.015)

    def OnButton_getRAll(self):
        print("get_R_All")
        for id in self.int_id_R:
            eval("self.ui.motor{}Value_spinBox.setValue(self.getMotorPosition(id))".format(id))
            time.sleep(0.015)

    def OnButton_getLArmAll(self):
        print("get_L_Arm_All")
        for id in self.int_id_LArm:
            eval("self.ui.motor{}Value_spinBox.setValue(self.getMotorPosition(id))".format(id))
            time.sleep(0.015)

    def OnButton_getRArmAll(self):
        print("get_R_Arm_All")
        for id in self.int_id_RArm:
            eval("self.ui.motor{}Value_spinBox.setValue(self.getMotorPosition(id))".format(id))
            time.sleep(0.015)

    def OnButton_getHAll(self):
        print("get_H_All")
        for id in self.int_id_H:
            eval("self.ui.motor{}Value_spinBox.setValue(self.getMotorPosition(id))".format(id))
            time.sleep(0.015)

    def OnButton_Set(self, id):
        print("set id=",id)
        self.int_motorValue[self.GetOrderKeyframe() - 1][self.dic_motorIndexID['id' + str(id)]] = eval(
            "self.ui.motor{}Value_spinBox.value()".format(id))

        torque_status = [1]
        self.setWritePackage(id ,0x40,1,torque_status)

        self.setDeviceMoving(self.str_comport, self.str_baudrate, id, "Ex",
                             self.int_motorValue[self.GetOrderKeyframe() - 1][self.dic_motorIndexID['id' + str(id)]],
                             1023, 1023)
        self.int_old_motorValue[self.dic_motorIndexID['id' + str(id)]] = \
        self.int_motorValue[self.GetOrderKeyframe() - 1][self.dic_motorIndexID['id' + str(id)]]

    def OnButton_play(self):
        print("play...")

        self.SetButtonAndSpinCtrlDisable()


        for id in self.int_id_All:
            self.int_motorValue[self.GetOrderKeyframe() - 1][eval("self.dic_motorIndexID['id{}']".format(id))] = eval(
                "self.ui.motor{}Value_spinBox.value()".format(id))

        time_start = time.time()
        time_finish = time_start + float(self.int_time[self.GetOrderKeyframe() - 1])/10
        in_time = True

        print(time_start)
        print(time_finish)
        print('Wait....')
        while in_time:
            time_current = time.time()
            if time_current >= time_finish:

                for i in self.int_id_All:
                    self.setDeviceMoving( self.str_comport, self.str_baudrate, i, "Ex", self.int_motorValue[self.GetOrderKeyframe() - 1][self.dic_motorIndexID['id'+str(i)]], 1023, 1023)
                    #self.setDeviceMoving( self.str_comport, self.str_baudrate, 1, "Ex", self.int_motorValue[self.GetOrderKeyframe() - 1][self.dic_motorIndexID['id1']], 1023, 1023)

                for id in self.int_id_All:
                    self.int_old_motorValue[eval("self.dic_motorIndexID['id{}']".format(id))] = \
                    self.int_motorValue[self.GetOrderKeyframe() - 1][eval("self.dic_motorIndexID['id{}']".format(id))]

                in_time = False

            else:
                for i in self.int_id_All:
                    self.setDeviceMoving( self.str_comport, self.str_baudrate, i, "Ex", self.InterpolateMotorValue(self.int_motorValue[self.GetOrderKeyframe() - 1][self.dic_motorIndexID['id'+str(i)]],self.int_old_motorValue[self.dic_motorIndexID['id'+str(i)]],time_finish,time_start,time_current), 1023, 1023)
                    #self.setDeviceMoving( self.str_comport, self.str_baudrate, 1, "Ex", self.InterpolateMotorValue(self.int_motorValue[self.GetOrderKeyframe() - 1][self.dic_motorIndexID['id1']],self.int_old_motorValue[self.dic_motorIndexID['id1']],time_finish,time_start,time_current), 1023, 1023)

            time.sleep(self.int_stepTime)

        print('Finished')
        self.SetButtonAndSpinCtrlEnable()

    def OnButton_setLAll(self):
        print("set L all")
        for id in self.int_id_L:
            self.int_motorValue[self.GetOrderKeyframe() - 1][eval("self.dic_motorIndexID['id{}']".format(id))] = eval(
                "self.ui.motor{}Value_spinBox.value()".format(id))

            torque_status = [1]
            self.setWritePackage(id ,0x40,1,torque_status)

            self.setDeviceMoving(self.str_comport, self.str_baudrate, id, "Ex",
                                 self.int_motorValue[self.GetOrderKeyframe() - 1][
                                     eval("self.dic_motorIndexID['id{}']".format(id))], 1023, 1023)
            self.int_old_motorValue[eval("self.dic_motorIndexID['id{}']".format(id))] = \
            self.int_motorValue[self.GetOrderKeyframe() - 1][eval("self.dic_motorIndexID['id{}']".format(id))]
            time.sleep(0.015)
    def OnButton_setRAll(self):
        print("set R all")
        for id in self.int_id_R:
            self.int_motorValue[self.GetOrderKeyframe() - 1][eval("self.dic_motorIndexID['id{}']".format(id))] = eval(
                "self.ui.motor{}Value_spinBox.value()".format(id))

            torque_status = [1]
            self.setWritePackage(id ,0x40,1,torque_status)

            self.setDeviceMoving(self.str_comport, self.str_baudrate, id, "Ex",
                                 self.int_motorValue[self.GetOrderKeyframe() - 1][
                                     eval("self.dic_motorIndexID['id{}']".format(id))], 1023, 1023)
            self.int_old_motorValue[eval("self.dic_motorIndexID['id{}']".format(id))] = \
            self.int_motorValue[self.GetOrderKeyframe() - 1][eval("self.dic_motorIndexID['id{}']".format(id))]
            time.sleep(0.015)
    def OnButton_setLArmAll(self):
        print("set L arm all")
        for id in self.int_id_LArm:
            self.int_motorValue[self.GetOrderKeyframe() - 1][eval("self.dic_motorIndexID['id{}']".format(id))] = eval(
                "self.ui.motor{}Value_spinBox.value()".format(id))

            torque_status = [1]
            self.setWritePackage(id ,0x40,1,torque_status)

            self.setDeviceMoving(self.str_comport, self.str_baudrate, id, "Ex",
                                 self.int_motorValue[self.GetOrderKeyframe() - 1][
                                     eval("self.dic_motorIndexID['id{}']".format(id))], 1023, 1023)
            self.int_old_motorValue[eval("self.dic_motorIndexID['id{}']".format(id))] = \
            self.int_motorValue[self.GetOrderKeyframe() - 1][eval("self.dic_motorIndexID['id{}']".format(id))]
            time.sleep(0.015)
    def OnButton_setRArmAll(self):
        print("set R arm all")
        for id in self.int_id_RArm:
            self.int_motorValue[self.GetOrderKeyframe() - 1][eval("self.dic_motorIndexID['id{}']".format(id))] = eval(
                "self.ui.motor{}Value_spinBox.value()".format(id))

            torque_status = [1]
            self.setWritePackage(id ,0x40,1,torque_status)

            self.setDeviceMoving(self.str_comport, self.str_baudrate, id, "Ex",
                                 self.int_motorValue[self.GetOrderKeyframe() - 1][
                                     eval("self.dic_motorIndexID['id{}']".format(id))], 1023, 1023)
            self.int_old_motorValue[eval("self.dic_motorIndexID['id{}']".format(id))] = \
            self.int_motorValue[self.GetOrderKeyframe() - 1][eval("self.dic_motorIndexID['id{}']".format(id))]
            time.sleep(0.015)
    def OnButton_setHAll(self):
        print("set H all")
        for id in self.int_id_H:
            self.int_motorValue[self.GetOrderKeyframe() - 1][eval("self.dic_motorIndexID['id{}']".format(id))] = eval(
                "self.ui.motor{}Value_spinBox.value()".format(id))
            
            torque_status = [1]
            self.setWritePackage(id ,0x40,1,torque_status)

            self.setDeviceMoving(self.str_comport, self.str_baudrate, id, "Ex",
                                 self.int_motorValue[self.GetOrderKeyframe() - 1][
                                     eval("self.dic_motorIndexID['id{}']".format(id))], 1023, 1023)
            self.int_old_motorValue[eval("self.dic_motorIndexID['id{}']".format(id))] = \
            self.int_motorValue[self.GetOrderKeyframe() - 1][eval("self.dic_motorIndexID['id{}']".format(id))]
            time.sleep(0.015)
    def OnButton_setAll(self):
        print("set all")
        #self.int_time[self.GetOrderKeyframe() - 1] = self.spinctrl_time.GetValue()
        for id in self.int_id_All:
            self.int_motorValue[self.GetOrderKeyframe() - 1][eval("self.dic_motorIndexID['id{}']".format(id))] = eval(
                "self.ui.motor{}Value_spinBox.value()".format(id))

            torque_status = [1]
            self.setWritePackage(id ,0x40,1,torque_status)

            self.setDeviceMoving(self.str_comport, self.str_baudrate, id, "Ex",
                                 self.int_motorValue[self.GetOrderKeyframe() - 1][
                                     eval("self.dic_motorIndexID['id{}']".format(id))], 1023, 1023)
            self.int_old_motorValue[eval("self.dic_motorIndexID['id{}']".format(id))] = \
            self.int_motorValue[self.GetOrderKeyframe() - 1][eval("self.dic_motorIndexID['id{}']".format(id))]
            time.sleep(0.015)
    def OnButton_time(self):
        self.int_time[self.GetOrderKeyframe() - 1] = self.ui.keyframeTime_spinBox.value()
        print(self.int_time[self.GetOrderKeyframe() - 1])

    def OnButton_ready(self):
        print("ready...")

        self.SetButtonAndSpinCtrlDisable()

        if self.int_numberOfKeyframe == 0:
            print('Error!! Number of keyframe = 0 ')
        else:
            time_start = time.time()
            time_finish = time_start + float(self.int_time[0])/10
            in_time = True

            print(time_start)
            print(time_finish)
            print('Wait....')
            while in_time:
                time_current = time.time()
                if time_current >= time_finish:
                    for i in self.int_id_All:
                        self.setDeviceMoving( self.str_comport, self.str_baudrate, i, "Ex", self.int_motorValue[0][self.dic_motorIndexID['id'+str(i)]], 200, 200)
                        self.int_old_motorValue[eval("self.dic_motorIndexID['id{}']".format(i))] = \
                        self.int_motorValue[0][eval("self.dic_motorIndexID['id{}']".format(i))]

                    in_time = False

                else:
                    for i in self.int_id_All:
                        self.setDeviceMoving( self.str_comport, self.str_baudrate, i, "Ex", self.InterpolateMotorValue(self.int_motorValue[0][self.dic_motorIndexID['id'+str(i)]],self.int_old_motorValue[self.dic_motorIndexID['id'+str(i)]],time_finish,time_start,time_current), 200, 200)
                        #self.setDeviceMoving( self.str_comport, self.str_baudrate, 1, "Ex", self.InterpolateMotorValue(self.int_motorValue[0][self.dic_motorIndexID['id1']],self.int_old_motorValue[self.dic_motorIndexID['id1']],time_finish,time_start,time_current), 200, 200)

                time.sleep(0.015)
            print('Finished')
        self.SetButtonAndSpinCtrlEnable()

    def OnButton_playAll(self):
        print("play all")
        self.SetButtonAndSpinCtrlDisable()

        if self.int_numberOfKeyframe == 0:
            print('Error!! Number of keyframe = 0 ')
        else:
            self.SetButtonAndSpinCtrlDisable()
            for x in range(self.int_numberOfKeyframe):
                time_start = time.time()
                time_finish = time_start + float(self.int_time[x])/10
                in_time = True

                print(time_start)
                print(time_finish)
                print('keyframe = ' + str(x + 1))
                print('Time = ' + str(self.int_time[x]))
                print('Wait....')
                while in_time:
                    time_current = time.time()
                    if time_current >= time_finish:
                        for i in self.int_id_All:
                            self.setDeviceMoving( self.str_comport, self.str_baudrate, i, "Ex", self.int_motorValue[x][self.dic_motorIndexID['id'+str(i)]], 1023, 1023)
                            self.int_old_motorValue[eval("self.dic_motorIndexID['id{}']".format(i))] = \
                            self.int_motorValue[x][eval("self.dic_motorIndexID['id{}']".format(i))]

                        in_time = False

                    else:
                        for i in self.int_id_All:
                            self.setDeviceMoving( self.str_comport, self.str_baudrate, i, "Ex", self.InterpolateMotorValue(self.int_motorValue[x][self.dic_motorIndexID['id'+str(i)]],self.int_old_motorValue[self.dic_motorIndexID['id'+str(i)]],time_finish,time_start,time_current), 1023, 1023)
                            #self.setDeviceMoving( self.str_comport, self.str_baudrate, 1, "Ex", self.InterpolateMotorValue(self.int_motorValue[x][self.dic_motorIndexID['id1']],self.int_old_motorValue[self.dic_motorIndexID['id1']],time_finish,time_start,time_current), 1023, 1023)

                    time.sleep(self.int_stepTime)

                print('Finished')
            self.SetButtonAndSpinCtrlEnable()

    def OnButton_Load(self):
        print("Load Posture :: "+str(self.str_postureName))

        self.ui.postureName_label.setText(self.str_postureName)

        self.int_numberOfKeyframe = int(self.config_current[self.str_postureName]['Keyframe_Amount'])
        self.ui.numOfKeyframeStatus_label.setText(str(self.int_numberOfKeyframe))

        for x in range(self.int_numberOfKeyframe):
            self.bool_activeKeyframe[x] = True
            for y in range(self.int_motor_Amount):
                print(self.str_postureName)
                self.int_motorValue[x][y] = int(self.config_current[self.str_postureName]['Keyframe_Value']['Keyframe_' +str(x)][y])
            print(self.int_motorValue[x])

        for z in range(self.int_numberOfKeyframe, self.int_keyframe_Amount):
            self.bool_activeKeyframe[z] = False

        for x in range(self.int_numberOfKeyframe):
            self.int_time[x] = int(self.config_current[self.str_postureName]['Keyframe_Time'][x])

        self.SetValueKeyframeToShow()

    def OnButton_Save(self):
        print("Save Posture :: " + str(self.str_postureName))

        self.ui.postureName_label.setText(self.str_postureName)

        config = self.config_current

        config[self.str_postureName] = {}
        config[self.str_postureName]['Keyframe_Amount'] = self.int_numberOfKeyframe
        config[self.str_postureName]['Keyframe_Time'] = self.int_time[:self.int_numberOfKeyframe]
        config[self.str_postureName]['Keyframe_Value'] = {}
        for i in range(self.int_numberOfKeyframe):
            config[self.str_postureName]['Keyframe_Value']['Keyframe_' + str(i)] = self.int_motorValue[i]

        config.write()

        self.config_current = ConfigObj(self.str_fileName)


    def SetMotorCenterLabel(self):
        for i in self.int_id_All:
            eval(
                "self.ui.motor{}center_label.setText(str(self.int_motorCenterValue[self.dic_motorIndexID['id'+str(i)]]))".format(
                    i))

    def OnButton_SaveCenter(self):
        config = self.config_current

        for id in self.int_id_All:
            self.int_motorCenterValue[eval("self.dic_motorIndexID['id{}']".format(id))] = eval(
                "self.ui.motor{}Value_spinBox.value()".format(id))

        config['motors center']['left leg'] = self.int_motorCenterValue[0:6]
        config['motors center']['right leg'] = self.int_motorCenterValue[6:12]
        config['motors center']['left arm'] = self.int_motorCenterValue[12:16]
        config['motors center']['right arm'] = self.int_motorCenterValue[16:20]
        config['motors center']['head'] = self.int_motorCenterValue[20:23]

        config.write()

        self.SetMotorCenterLabel()

    def OnSelect_ComboboxPosture(self,text):
        self.str_postureName = text
        print('Posture Selected')
        print(self.str_postureName)

    def OnButton_connect(self):
        print("connect clicked")
        if self.bool_comportConnected == False:
            try:

                self.serialDevice = serial.Serial(self.str_comport, self.str_baudrate,8,'N',1,0,0,0,0)
            
                self.bool_comportConnected = True
                self.ui.connectionStatus_label.setText("Status : Connected")
                self.ui.connect_Button.setText("Disconnect")
                self.config_setup['baudrate'] = self.str_baudrate
                self.config_setup.write()
                print('comport connected')
                time.sleep(0.5)
                self.setStatusReturnLevel(1)
                self.setEnableMotorTorqueAll()
            except:
                print("Cannot Connect Comport!!!")
        else:
            self.bool_comportConnected = False
            self.serialDevice.close()
            self.ui.connectionStatus_label.setText("Status : Disconnected")
            self.ui.connect_Button.setText("Connect")
            print('comport disconnected')

    def OnSelect_ComboboxComport(self,text):
        self.str_comport = str(text)
        print("comport = " + str(self.str_comport))

    def OnSelect_ComboboxBaudrate(self,text):
        self.str_baudrate = str(text)
        print("baurate = " + str(self.str_baudrate))

    def OnSelect_ComboboxKeyframe(self,text):
        self.str_keyframeSelected = text
        self.int_keyframeSelected = int(text)
        print("keyframe selected = " + str(self.int_keyframeSelected))
        self.SetValueKeyframeToShow()

    def SetValueKeyframeToShow(self):

        keyframe = self.int_keyframeSelected

        self.int_keyframeSelected = keyframe

        print("keyframe selected = " + str(self.int_keyframeSelected))


        if self.bool_activeKeyframe[keyframe-1] == True:
            self.ui.activeKeyframe_checkBox.setChecked(2)
            self.SetButtonAndSpinCtrlEnable()
            for id in self.int_id_All:
                eval("self.ui.motor{}Value_spinBox".format(id)).setValue(
                    int(self.int_motorValue[keyframe - 1][eval("self.dic_motorIndexID['id{}']".format(id))]))
            self.ui.keyframeTime_spinBox.setValue(self.int_time[keyframe-1])
        else:
            self.ui.activeKeyframe_checkBox.setChecked(0)
            self.SetButtonAndSpinCtrlDisable()

    def CheckPreviousKeyframe(self,currentKeyframe):


        if currentKeyframe == 1:
            self.bool_activeKeyframe[currentKeyframe-1] = True
            self.SetValueKeyframeToShow()
        else:
            self.bool_activeKeyframe[0] = True
            bool_getActiveKeyframe = False
            int_searchKeyframe = currentKeyframe - 1
            while(bool_getActiveKeyframe == False):
                if self.bool_activeKeyframe[int_searchKeyframe - 1] == True:
                    bool_getActiveKeyframe = True
                else:
                    int_searchKeyframe = int_searchKeyframe - 1
            for i in range (int_searchKeyframe+1,currentKeyframe+1):
                self.bool_activeKeyframe[i-1] = True
                for j in range (self.int_motor_Amount):
                    self.int_motorValue[i-1][j] = self.int_motorValue[int_searchKeyframe-1][j]
            #self.SetValueKeyframeToShow(currentKeyframe)
            self.SetValueKeyframeToShow()

    def CheckNextKeyframe(self,currentKeyframe):
        if currentKeyframe == self.int_keyframe_Amount:
            self.bool_activeKeyframe[currentKeyframe-1] = False
            self.SetValueKeyframeToShow()
        else:
            self.bool_activeKeyframe[self.int_keyframe_Amount-1] = False
            bool_getNotActiveKeyframe = False
            int_searchKeyframe = currentKeyframe + 1
            while(bool_getNotActiveKeyframe == False):
                if self.bool_activeKeyframe[int_searchKeyframe - 1] == False:
                    bool_getNotActiveKeyframe = True
                else:
                    int_searchKeyframe = int_searchKeyframe + 1
            for i in range (currentKeyframe,int_searchKeyframe+1):
                self.bool_activeKeyframe[i-1] = False
                for j in range (self.int_motor_Amount):
                    self.int_motorValue[i-1][j] = self.int_motorCenterValue[j]
            #self.SetValueKeyframeToShow(currentKeyframe)
            self.SetValueKeyframeToShow()

    def ActiveKeyframe_CheckBox(self):
        print(self.ui.activeKeyframe_checkBox.checkState())

        if self.ui.activeKeyframe_checkBox.checkState() == 2:
            print("Checked")

            self.CheckPreviousKeyframe(self.int_keyframeSelected)

            self.int_numberOfKeyframe = self.int_keyframeSelected


            self.ui.numOfKeyframeStatus_label.setText(str(self.int_numberOfKeyframe))


        else:
            print("Unchecked")
            self.CheckNextKeyframe(self.int_keyframeSelected)
            self.int_numberOfKeyframe = (self.int_keyframeSelected - 1)

            self.ui.numOfKeyframeStatus_label.setText(str(self.int_numberOfKeyframe))

    def SetButtonAndSpinCtrlEnable(self):

        self.ui.setAll_pushButton.setEnabled(True)
        self.ui.setLAll_pushButton.setEnabled(True)
        self.ui.setRAll_pushButton.setEnabled(True)
        self.ui.setLArmAll_pushButton.setEnabled(True)
        self.ui.setRArmAll_pushButton.setEnabled(True)
        self.ui.setHAll_pushButton.setEnabled(True)

        self.ui.getAll_pushButton.setEnabled(True)
        self.ui.getLAll_pushButton.setEnabled(True)
        self.ui.getRAll_pushButton.setEnabled(True)
        self.ui.getLArmAll_pushButton.setEnabled(True)
        self.ui.getRArmAll_pushButton.setEnabled(True)
        self.ui.getHAll_pushButton.setEnabled(True)

        self.ui.disTAll_pushButton.setEnabled(True)
        self.ui.disTLAll_pushButton.setEnabled(True)
        self.ui.disTRAll_pushButton.setEnabled(True)
        self.ui.disTLArmAll_pushButton.setEnabled(True)
        self.ui.disTRArmAll_pushButton.setEnabled(True)
        self.ui.disTHAll_pushButton.setEnabled(True)

        self.ui.deleteKeyframe_pushButton.setEnabled(True)
        self.ui.duplicateKeyframe_pushButton.setEnabled(True)
        self.ui.previousSwitchKeyframe_pushButton.setEnabled(True)
        self.ui.nextSwitchKeyframe_pushButton.setEnabled(True)
        self.ui.play_pushButton.setEnabled(True)
        self.ui.playAll_Button.setEnabled(True)
        self.ui.setReady_Button.setEnabled(True)
        self.ui.setTime_pushButton.setEnabled(True)
        self.ui.setAll_pushButton.setEnabled(True)
        self.ui.keyframeTime_spinBox.setEnabled(True)

        for id in self.int_id_All:
            eval("self.ui.motor{}Value_spinBox.setEnabled(True)".format(id))
            eval("self.ui.motor{}value_dial.setEnabled(True)".format(id))
            eval("self.ui.motor{}Set_pushButton.setEnabled(True)".format(id))
            eval("self.ui.motor{}Get_pushButton.setEnabled(True)".format(id))
            eval("self.ui.motor{}DisT_pushButton.setEnabled(True)".format(id))

    def SetButtonAndSpinCtrlDisable(self):

        self.ui.setAll_pushButton.setDisabled(True)
        self.ui.setLAll_pushButton.setDisabled(True)
        self.ui.setRAll_pushButton.setDisabled(True)
        self.ui.setLArmAll_pushButton.setDisabled(True)
        self.ui.setRArmAll_pushButton.setDisabled(True)
        self.ui.setHAll_pushButton.setDisabled(True)

        self.ui.getAll_pushButton.setDisabled(True)
        self.ui.getLAll_pushButton.setDisabled(True)
        self.ui.getRAll_pushButton.setDisabled(True)
        self.ui.getLArmAll_pushButton.setDisabled(True)
        self.ui.getRArmAll_pushButton.setDisabled(True)
        self.ui.getHAll_pushButton.setDisabled(True)

        self.ui.disTAll_pushButton.setDisabled(True)
        self.ui.disTLAll_pushButton.setDisabled(True)
        self.ui.disTRAll_pushButton.setDisabled(True)
        self.ui.disTLArmAll_pushButton.setDisabled(True)
        self.ui.disTRArmAll_pushButton.setDisabled(True)
        self.ui.disTHAll_pushButton.setDisabled(True)

        self.ui.deleteKeyframe_pushButton.setDisabled(True)
        self.ui.duplicateKeyframe_pushButton.setDisabled(True)
        self.ui.previousSwitchKeyframe_pushButton.setDisabled(True)
        self.ui.nextSwitchKeyframe_pushButton.setDisabled(True)
        self.ui.play_pushButton.setDisabled(True)
        self.ui.playAll_Button.setDisabled(True)
        self.ui.setReady_Button.setDisabled(True)
        self.ui.setTime_pushButton.setDisabled(True)
        self.ui.setAll_pushButton.setDisabled(True)
        self.ui.keyframeTime_spinBox.setDisabled(True)

        for id in self.int_id_All:
            eval("self.ui.motor{}Value_spinBox.setDisabled(True)".format(id))
            eval("self.ui.motor{}value_dial.setDisabled(True)".format(id))
            eval("self.ui.motor{}Set_pushButton.setDisabled(True)".format(id))
            eval("self.ui.motor{}Get_pushButton.setDisabled(True)".format(id))
            eval("self.ui.motor{}DisT_pushButton.setDisabled(True)".format(id))

    def GetOrderKeyframe(self):

        for index, kf in enumerate(self.keyframeList):
            if self.int_keyframeSelected == int(kf):
                orderKeyframe = index + 1
        return orderKeyframe
    
    def setWritePackage(self,ID,address,bytes,data):
        length = bytes + 2 + 3
        TxBuf = [0xff, 0xff, 0xfd, 0x00, ID, length & 0xff, (length >> 8) & 0xff, 0x03, address & 0xff, (address >>8) & 0xff]
        print("byte =",bytes, type(bytes))
        for i in range(0,bytes):
            
            TxBuf.append(data[i])
        
        CRC = self.updateCRC(0, TxBuf, len(TxBuf))
        TxBuf.append(CRC & 0x00FF)
        TxBuf.append((CRC >> 8) & 0x00FF)

        try:
            self.serialDevice.write(TxBuf)
        except:
            print("Serial Error!! [setWriteMotorPacket]")
        print(TxBuf)

        

    def setReadMotorPacket(self,deviceID,Address,Length):
        #package = H1 H2 H3 RSRV ID LEN1 LEN2 INST PARAM1 PARAM2 PARAM3 PARAM4 CRC1 CRC2
        readPackage = [0xFF, 0xFF, 0xFD, 0x00, deviceID, 0x07, 0x00, 0x02, Address & 0xff, (Address >> 8) &0xff, Length & 0xff, (Length >> 8) &0xff]
        CRC = self.updateCRC(0, readPackage, len(readPackage))
        readPackage.append(CRC & 0x00FF)
        readPackage.append((CRC >> 8) & 0x00FF)

        print("ReadPackage = ", [hex(x) for x in readPackage])

       
        try:
            self.serialDevice.write(readPackage)
        except:
            print("Serial Error!! [setReadMotorPacket]")
        print(readPackage)

    def getMotorQueryResponse( self, deviceID, Length ):

            queryData = 0
            responsePacketSize = 15
            #responsePacket = readAllData(serialDevice)
            responsePacket = self.serialDevice.read(self.serialDevice.inWaiting())
            print("responsepkg =",responsePacket)
            print("len responsePacket = ", len(responsePacket))

            if len(responsePacket) == responsePacketSize:

                print("responsePacket=", responsePacket)

                responseID = responsePacket[4]
                errorByte = responsePacket[8]

                ### python 3
                if responseID == deviceID and errorByte == 0:
                    queryData = responsePacket[9] + 256 * responsePacket[10]

                else:
                    print("Error response:", responseID, errorByte)

                responsePacketStatue = True

            else:
                responsePacketStatue = False

            print("queryData=", queryData)
            return queryData,responsePacketStatue

    def get(self,deviceID, address, Length):

            for i in range(0,5):
                self.setReadMotorPacket(deviceID, address, Length)
                time.sleep(0.02)
                data, status = self.getMotorQueryResponse(deviceID, Length)

                if status == True:
                    break
                else:
                    print("motor ID " + str(deviceID) + "  no response " + str(i))
                    data = "error"

            return data

    def getMotorPosition(self,id):
            data = self.get(id,0x84,4)
            return data

    def rxPacketConversion( self,value ):
            if value < 1024 and value >= 0:
                    hiByte = int(value/256)
                    loByte = value%256
            else:
                    print("rxPacketConversion: value out of range", value)
            return loByte, hiByte

    def exPacketConversion( self,value ):
            if value < 4096 and value >= 0:
                    hiByte = int(value/256)
                    loByte = value%256
            else:
                    print("exPacketConversion: value out of range", value)
            return loByte, hiByte

    def setStatusReturnLevel(self,status):
        return_status = [status]
        for i in range(0,50):
            self.setWritePackage(i ,0x44,1,return_status)
            time.sleep(0.01)
        #time.sleep(0.01)

    def setEnableMotorTorqueAll(self):
        for i in range(0,50):
            self.setEnableMotorTorque(i)
            time.sleep(0.01)

    def setEnableMotorTorque(self,deviceID):
        torque_status = [1]
        self.setWritePackage(deviceID ,0x40,1,torque_status)

    def setDisableMotorTorque(self,deviceID):
        torque_status = [0]
        self.setWritePackage(deviceID ,0x40,1,torque_status)
        #time.sleep(0.01)

    def setDeviceMoving( self,Port, Baud, deviceID, deviceType, goalPos, goalSpeed, maxTorque):

        position = [goalPos & 0xff, (goalPos >> 8) & 0xff, 0x00, 0x00]
        self.setWritePackage(deviceID ,0x74,4,position)



    def InterpolateMotorValue(self,finish_value,start_value,finish_time,start_time,current_time):
        motor_value = int((finish_value - start_value)*(current_time-start_time)/(finish_time - start_time)+start_value)
        return motor_value

    def updateCRC(self, crc_accum, data_blk_ptr, data_blk_size):
        crc_table = [0x0000,
                     0x8005, 0x800F, 0x000A, 0x801B, 0x001E, 0x0014, 0x8011,
                     0x8033, 0x0036, 0x003C, 0x8039, 0x0028, 0x802D, 0x8027,
                     0x0022, 0x8063, 0x0066, 0x006C, 0x8069, 0x0078, 0x807D,
                     0x8077, 0x0072, 0x0050, 0x8055, 0x805F, 0x005A, 0x804B,
                     0x004E, 0x0044, 0x8041, 0x80C3, 0x00C6, 0x00CC, 0x80C9,
                     0x00D8, 0x80DD, 0x80D7, 0x00D2, 0x00F0, 0x80F5, 0x80FF,
                     0x00FA, 0x80EB, 0x00EE, 0x00E4, 0x80E1, 0x00A0, 0x80A5,
                     0x80AF, 0x00AA, 0x80BB, 0x00BE, 0x00B4, 0x80B1, 0x8093,
                     0x0096, 0x009C, 0x8099, 0x0088, 0x808D, 0x8087, 0x0082,
                     0x8183, 0x0186, 0x018C, 0x8189, 0x0198, 0x819D, 0x8197,
                     0x0192, 0x01B0, 0x81B5, 0x81BF, 0x01BA, 0x81AB, 0x01AE,
                     0x01A4, 0x81A1, 0x01E0, 0x81E5, 0x81EF, 0x01EA, 0x81FB,
                     0x01FE, 0x01F4, 0x81F1, 0x81D3, 0x01D6, 0x01DC, 0x81D9,
                     0x01C8, 0x81CD, 0x81C7, 0x01C2, 0x0140, 0x8145, 0x814F,
                     0x014A, 0x815B, 0x015E, 0x0154, 0x8151, 0x8173, 0x0176,
                     0x017C, 0x8179, 0x0168, 0x816D, 0x8167, 0x0162, 0x8123,
                     0x0126, 0x012C, 0x8129, 0x0138, 0x813D, 0x8137, 0x0132,
                     0x0110, 0x8115, 0x811F, 0x011A, 0x810B, 0x010E, 0x0104,
                     0x8101, 0x8303, 0x0306, 0x030C, 0x8309, 0x0318, 0x831D,
                     0x8317, 0x0312, 0x0330, 0x8335, 0x833F, 0x033A, 0x832B,
                     0x032E, 0x0324, 0x8321, 0x0360, 0x8365, 0x836F, 0x036A,
                     0x837B, 0x037E, 0x0374, 0x8371, 0x8353, 0x0356, 0x035C,
                     0x8359, 0x0348, 0x834D, 0x8347, 0x0342, 0x03C0, 0x83C5,
                     0x83CF, 0x03CA, 0x83DB, 0x03DE, 0x03D4, 0x83D1, 0x83F3,
                     0x03F6, 0x03FC, 0x83F9, 0x03E8, 0x83ED, 0x83E7, 0x03E2,
                     0x83A3, 0x03A6, 0x03AC, 0x83A9, 0x03B8, 0x83BD, 0x83B7,
                     0x03B2, 0x0390, 0x8395, 0x839F, 0x039A, 0x838B, 0x038E,
                     0x0384, 0x8381, 0x0280, 0x8285, 0x828F, 0x028A, 0x829B,
                     0x029E, 0x0294, 0x8291, 0x82B3, 0x02B6, 0x02BC, 0x82B9,
                     0x02A8, 0x82AD, 0x82A7, 0x02A2, 0x82E3, 0x02E6, 0x02EC,
                     0x82E9, 0x02F8, 0x82FD, 0x82F7, 0x02F2, 0x02D0, 0x82D5,
                     0x82DF, 0x02DA, 0x82CB, 0x02CE, 0x02C4, 0x82C1, 0x8243,
                     0x0246, 0x024C, 0x8249, 0x0258, 0x825D, 0x8257, 0x0252,
                     0x0270, 0x8275, 0x827F, 0x027A, 0x826B, 0x026E, 0x0264,
                     0x8261, 0x0220, 0x8225, 0x822F, 0x022A, 0x823B, 0x023E,
                     0x0234, 0x8231, 0x8213, 0x0216, 0x021C, 0x8219, 0x0208,
                     0x820D, 0x8207, 0x0202]

        for j in range(0, data_blk_size):
            i = ((crc_accum >> 8) ^ data_blk_ptr[j]) & 0xFF
            crc_accum = ((crc_accum << 8) ^ crc_table[i]) & 0xFFFF

        return crc_accum

if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    MainWindow = HumanoidMainWindow()


    MainWindow.show()
    sys.exit(app.exec_())