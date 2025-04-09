from PySide2.QtWidgets import QHBoxLayout, QLabel, QLineEdit, QMainWindow, QMessageBox, QPushButton, QSlider, QVBoxLayout, QWidget #import classes from the QtWidgets module
from PySide2.QtCore import Qt #Import Qt class from QtCore
from maya.OpenMaya import MVector
import maya.OpenMayaUI as OpenMayaUI #Import Maya UI module
import shiboken2 #Import shoken2
import maya.cmds as mc #Import maya commands
import maya.mel as mel

def GetMayaMainWindow()->QMainWindow: #Defines the GetMayaMainWindow() function that returns QMainWindow
    mainWindow = OpenMayaUI.MQtUtil.mainWindow() #Instantiate a mainWindow() class and assign to mainWindow
    return shiboken2.wrapInstance(int(mainWindow), QMainWindow) #Create python wrapper for a QMainWindow object

def DeleteWidgetWithName(name)->QMainWindow: #Defines the DeleteWidgetWithName() function that returns QMainWindow
    for widget in GetMayaMainWindow().findChildren(QWidget, name): #Loop through children of type QWidget with name in main maya window
        widget.deleteLater() #Delete widget when event loop has control

class MayaWindow(QWidget): #Define class MayaWindow 
    def __init__(self): #Constructor
        super().__init__(parent = GetMayaMainWindow()) #Parent this window to main maya window
        DeleteWidgetWithName(self.GetWidgetUniqueName()) #Delete old widget if it exists
        self.setWindowFlags(Qt.WindowType.Window) #Make widget a window
        self.setObjectName(self.GetWidgetUniqueName()) #Set object name as unique identifier

    def GetWidgetUniqueName(self): #Defines GetWidgetUniqueName() function
        return "djsiofsklfhawp98ahw389dfnseiof" #Returns unique identifier for this widget

class LimbRigger: #Define LimbRigger class
    def __init__(self): #Initializer
        self.root = "" #Clear root joint
        self.mid = "" #Clear mid joint
        self.end = "" #Clear end joint
        self.controllerSize = 2 #Set size of controller to 2

    def FindJointsBasedOnSelection(self): #Define the FindJointsBasedOnSelection function
        try: #Check for errors
            self.root = mc.ls(sl=True, type="joint")[0] #Gets currently selected joint and assigns it to root

            self.mid = mc.listRelatives(self.root, c=True, type="joint")[0] #gets first child of root and assigns it to mid
            self.end = mc.listRelatives(self.mid, c=True, type="joint")[0] #gets first child of mid and assigns it to end
        except Exception as e: #Handle errors
            raise Exception("Invalid Selection, please select the first joint of the limb") #Display error 

    def CreateFKControllerForJoint(self, jntName): #Define CreateFKControllerForJoint Function
        ctrlName = "ac_L_fk_" + jntName #Set control name to prefix + jntName
        ctrlGrpName = ctrlName + "_grp" #Set group name to ctrlName + suffix
        mc.circle(name = ctrlName, radius = self.controllerSize, normal = (1,0,0)) #Create a nurb circle and set name, size, and orientation
        mc.group(ctrlName, n=ctrlGrpName) #Group ctrl to ctrlGrp
        mc.matchTransform(ctrlGrpName, jntName) #Match ctrlGrp to joint transform
        mc.orientConstraint(ctrlName, jntName) #Match orientation of control to joint
        return ctrlName, ctrlGrpName #Return control and control group
    
    def CreateBoxController(self, name):
        mel.eval(f"curve -n {name} -d 1 -p -0.5 0.5 0.5 -p 0.5 0.5 0.5 -p 0.5 0.5 -0.5 -p -0.5 0.5 -0.5 -p -0.5 0.5 0.5 -p -0.5 -0.5 0.5 -p 0.5 -0.5 0.5 -p 0.5 0.5 0.5 -p 0.5 -0.5 0.5 -p 0.5 -0.5 -0.5 -p 0.5 0.5 -0.5 -p 0.5 -0.5 -0.5 -p -0.5 -0.5 -0.5 -p -0.5 0.5 -0.5 -p -0.5 -0.5 -0.5 -p -0.5 -0.5 0.5 -k 0 -k 1 -k 2 -k 3 -k 4 -k 5 -k 6 -k 7 -k 8 -k 9 -k 10 -k 11 -k 12 -k 13 -k 14 -k 15")
        mc.scale(self.controllerSize, self.controllerSize, self.controllerSize, name)
        mc.makeIdentity(name, apply = True) # Freeze transform
        grpName = name + "_grp"
        mc.group(name, n = grpName)
        return name, grpName

    def CreatePlusController(self, name):
        mel.eval(f"curve -n {name} -d 1 -p -1 1 0 -p -1 3 0 -p 1 3 0 -p 1 1 0 -p 3 1 0 -p 3 -1 0 -p 1 -1 0 -p 1 -3 0 -p -1 -3 0 -p -1 -1 0 -p -3 -1 0 -p -3 1 0 -p -1 1 0 -k 0 -k 1 -k 2 -k 3 -k 4 -k 5 -k 6 -k 7 -k 8 -k 9 -k 10 -k 11 -k 12 ;")
        grpName = name + "_grp"
        mc.group(name, n = grpName)
        return name, grpName

    def GetObjectLocation(self, objectName):
        x, y, z = mc.xform(objectName, q=True, ws=True, t=True) #any transform, world space, translate attr
        return MVector(x, y, z)
    
    def PrintMVector(self, vector):
        print(f"<{vector.x}, {vector.y}, {vector.z}>")

    def RigLimb(self): #Defines RigLimb function
        rootCtrl, rootCtrlGrp = self.CreateFKControllerForJoint(self.root) #Creates FK controller for root joint
        midCtrl, midCtrlGrp = self.CreateFKControllerForJoint(self.mid) #Creates FK controller for mid joint 
        endCtrl, endCtrlGrp = self.CreateFKControllerForJoint(self.end) #Creates FK controller for end joint

        mc.parent(midCtrlGrp, rootCtrl) #Parent mid control group to root controller
        mc.parent(endCtrlGrp, midCtrl) #Parent end control group to mid controller

        ikEndCtrl = "ac_ik_" + self.end
        ikEndCtrl, ikEndCtrlGrp = self.CreateBoxController(ikEndCtrl)
        mc.matchTransform(ikEndCtrlGrp, self.end)
        endOrientConstraint = mc.orientConstraint(ikEndCtrl, self.end)[0]

        rootJntLoc = self.GetObjectLocation(self.root)
        self.PrintMVector(rootJntLoc)

        ikHandleName = "ikHandle_" + self.end
        mc.ikHandle(n=ikHandleName, sol="ikRPsolver", sj=self.root, ee=self.end) 

        poleVectorLocationVals = mc.getAttr(ikHandleName + ".poleVector")[0]
        poleVector = MVector(poleVectorLocationVals[0], poleVectorLocationVals[1], poleVectorLocationVals[2])
        poleVector.normalize()

        endJntLoc = self.GetObjectLocation(self.end)
        rootToEndVector = endJntLoc - rootJntLoc

        poleVectorCtrlLoc = (rootJntLoc + rootToEndVector / 2) + (poleVector * rootToEndVector.length())
        poleVectorCtrl = "ac_ik_" + self.mid
        mc.spaceLocator(n=poleVectorCtrl)
        poleVectorCtrlGrp = poleVectorCtrl + "_grp"
        mc.group(poleVectorCtrl, n=poleVectorCtrlGrp)
        mc.setAttr(poleVectorCtrlGrp + ".t", poleVectorCtrlLoc.x, poleVectorCtrlLoc.y, poleVectorCtrlLoc.z, typ="double3")

        mc.poleVectorConstraint(poleVectorCtrl, ikHandleName)

        ikfkBlendCtrl = "ac_ikfk_blend_" + self.root
        ikfkBlendCtrl, ikfkBlendCtrlGrp = self.CreatePlusController(ikfkBlendCtrl)
        mc.setAttr(ikfkBlendCtrlGrp+".t", rootJntLoc.x * 2, rootJntLoc.y, rootJntLoc.z * 2, typ="double3")
        
        ikfkBlendAttrName = "ikfkBlend"
        mc.addAttr(ikfkBlendCtrl, ln=ikfkBlendAttrName, min=0, max=1, k=True)
        ikfkBlendAttr = ikfkBlendCtrl + "." + ikfkBlendAttrName

        mc.expression(s=f"{ikHandleName}.ikBlend={ikfkBlendAttr}")
        #TODO: Finish Lecture from this point
        

class LimbRiggerWidget(MayaWindow): #Define LimbRiggerWidget
    def __init__(self): #Initializer
        super().__init__() #Call base class initializer
        self.rigger = LimbRigger() #Make new LimbRigger object
        self.setWindowTitle("Limb Rigger")

        self.masterLayout = QVBoxLayout() #Create QVBoxLayout object and assign to masterLayout
        self.setLayout(self.masterLayout) #set layout to masterLayout

        toolTipLabel = QLabel("Select the first joint of the limb and press the auto find button") #Create tooltip
        self.masterLayout.addWidget(toolTipLabel) #Add tooltip widget to window

        self.jointsListLineEdit = QLineEdit() #Create QLineEdit object, a one line text editor
        self.masterLayout.addWidget(self.jointsListLineEdit) #Add line edit widget to master Layout
        self.jointsListLineEdit.setEnabled(False) #Disable editing of line edit

        autoFindJointButton = QPushButton("Auto Find Joint") #Create QPushButton object with text
        autoFindJointButton.clicked.connect(self.AutoFindJointButtonClicked) #Register AutoFindJointButtonClicked function to the clicked event
        self.masterLayout.addWidget(autoFindJointButton) #Add joint button widget to master layout

        #Create controller size slider
        ctrlSizeSlider = QSlider()
        ctrlSizeSlider.setOrientation(Qt.Horizontal)
        ctrlSizeSlider.setRange(1, 30)
        ctrlSizeSlider.setValue(self.rigger.controllerSize)
        #Display value of controller size
        self.ctrlSizeLabel = QLabel(f"{self.rigger.controllerSize}")
        ctrlSizeSlider.valueChanged.connect(self.CtrlSizeSliderChanged)

        ctrlSizeLayout = QHBoxLayout()
        ctrlSizeLayout.addWidget(ctrlSizeSlider)
        ctrlSizeLayout.addWidget(self.ctrlSizeLabel)
        self.masterLayout.addLayout(ctrlSizeLayout)
        
        rigLimbButton = QPushButton("Rig Limb") #Create Limb Rig button
        rigLimbButton.clicked.connect(lambda : self.rigger.RigLimb()) #Register RigLimb function to button clicked event
        self.masterLayout.addWidget(rigLimbButton) #Add widget to master layout

    def CtrlSizeSliderChanged(self, newValue):
        self.ctrlSizeLabel.setText(f"{newValue}")
        self.rigger.controllerSize = newValue

    def AutoFindJointButtonClicked(self): #Define AutoFindJointButtonClicked
        try: #Check for exception
            self.rigger.FindJointsBasedOnSelection() #Get joints based on currently selected joint. Calls the function from our rigger class
            self.jointsListLineEdit.setText(f"{self.rigger.root},{self.rigger.mid},{self.rigger.end}") #Set text line to found joints
        except Exception as e: #Handle exceptions 
            QMessageBox.critical(self, "Error", f"{e}") #raise a critical error

limbRiggerWidget = LimbRiggerWidget() #Create LimbRiggerWidget object
limbRiggerWidget.show() #Show LimbRiggerWidget