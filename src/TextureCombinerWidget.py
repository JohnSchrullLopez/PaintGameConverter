from PySide2 import QtCore
from PySide2.QtGui import QIntValidator, QRegExpValidator
from PySide2.QtWidgets import QCheckBox, QFileDialog, QHBoxLayout, QLabel, QLineEdit, QMainWindow, QMessageBox, QPushButton, QSlider, QVBoxLayout, QWidget #import classes from the QtWidgets module
from PySide2.QtCore import Qt #Import Qt class from QtCore
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
        return "ejdowi309wrjsfmd" #Returns unique identifier for this widget

class TextureCombiner:
    def __init__(self, resolution, destination, filename):
        self.target = ""
        self.source = ""
        self.textureResolution = resolution
        self.outputDestination = destination
        self.filename = filename
        
    def CreateNewUVs(self):
        mc.polyLayoutUV(self.target, layout=2, percentageSpace=2)
        mc.polyAutoProjection(f'{self.target}.f[*]', ps=0.5)
        #Auto Layout UVs with padding
        mc.polyLayoutUV(self.target, layout=2, percentageSpace=2)

    def ReadySelectionForSampling(self):
        #Get selected mesh and duplicate
        self.target = mc.duplicate(self.source, n=(self.source + "_dup"))[0]
        #self.MakeOutputMaterial(self.target)

        #Delete history (c)hannel (h)istory
        mc.delete(self.target, ch=True)
        #Freeze transform
        mc.makeIdentity(self.target)

    def MakeOutputMaterial(self, object):
        outputMat = mc.shadingNode('aiStandardSurface', asShader=True, name="M_Output")
        outputMatSG = mc.sets(name="%s" % outputMat, empty=True, renderable=True, noSurfaceShader=True)
        mc.connectAttr("%s.outColor" % outputMat, "%s.surfaceShader" % outputMatSG, f=True)
        mc.sets(object, forceElement=outputMatSG)

    def RunSurfaceSampler(self):
        mc.select(cl=True)
        mc.select(self.source)
        mc.select(self.target, add=True)
        print(f"{self.source} {self.target}")
        print(f"{self.outputDestination}/{self.filename}")

        commandString = f'surfaceSampler -target {self.target} -uvSet UVSet0 -searchOffset 0 -maxSearchDistance 0 -searchCage "" '
        commandString += f'-source {self.source} -mapOutput normal -mapWidth {self.textureResolution} -mapHeight {self.textureResolution} -max 1 -mapSpace tangent -mapMaterials 1 -shadows 1 '
        commandString += f'-filename "{self.outputDestination}/{self.filename}_normal" -fileFormat "png" -mapOutput diffuseRGB '
        commandString += f'-mapWidth {self.textureResolution} -mapHeight {self.textureResolution} -max 1 -mapSpace tangent -mapMaterials 1 -shadows 1 -filename "{self.outputDestination}/{self.filename}_color" -fileFormat "png" '
        commandString += f'-ignoreTransforms true -superSampling 3 -filterType 0 -filterSize 3 -overscan 1 -searchMethod 0 -useGeometryNormals 1 -ignoreMirroredFaces 0 -flipU 0 -flipV 0 '

        print(commandString)
        mel.eval(commandString)

class TextureCombinerWidget(MayaWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Texture Combiner")
        self.resolution = ""
        self.saveLocation = ""
        self.fileName = ""
        self.shouldCreateUVs = False

        self.masterLayout = QVBoxLayout()
        self.setLayout(self.masterLayout)

        #Resolution
        resolutionLayout = QHBoxLayout()
        self.resolutionLabel = QLabel("Output Resolution [Square Textures Only]: ")
        resolutionLayout.addWidget(self.resolutionLabel)

        self.resolutionLineEdit = QLineEdit()
        self.resolutionLineEdit.setValidator(QIntValidator())
        self.resolutionLineEdit.textChanged.connect(self.SetResolution)
        resolutionLayout.addWidget(self.resolutionLineEdit)
        self.masterLayout.addLayout(resolutionLayout)

        #File Location
        self.saveFileLayout = QHBoxLayout()
        self.masterLayout.addLayout(self.saveFileLayout)

        #
        # Filename Label
        #
        self.saveFileLayout.addWidget(QLabel("Filename: "))
        self.fileNameLineEdit = QLineEdit()
        self.fileNameLineEdit.setFixedWidth(100)
        self.fileNameLineEdit.setValidator(QRegExpValidator("\w+"))
        self.fileNameLineEdit.textChanged.connect(self.FileNameLineEditChanged)
        self.saveFileLayout.addWidget(self.fileNameLineEdit)

        #
        # Save Directory Label
        #
        self.saveFileLayout.addWidget(QLabel("Save Directory: "))
        self.saveDirectoryLineEdit = QLineEdit()
        self.saveDirectoryLineEdit.setEnabled(False)
        self.saveFileLayout.addWidget(self.saveDirectoryLineEdit)

        #
        # Save Directory Button
        #
        self.pickDirectoryButton = QPushButton("...")
        self.pickDirectoryButton.clicked.connect(self.PickDirectoryButtonClicked)
        self.saveFileLayout.addWidget(self.pickDirectoryButton)

        #
        # Create UV Checkbox
        #
        self.createNewUVCheckbox = QCheckBox("Create New UVs?")
        self.createNewUVCheckbox.toggled.connect(self.CreateNewUVCheckboxClicked)
        self.saveFileLayout.addWidget(self.createNewUVCheckbox)

        #
        # Combine Texture Button
        #
        combineTextureButton = QPushButton("Combine Textures")
        combineTextureButton.clicked.connect(self.RunTextureCombiner)
        self.masterLayout.addWidget(combineTextureButton)

    def CreateNewUVCheckboxClicked(self):
        self.shouldCreateUVs = not self.shouldCreateUVs
        print(self.shouldCreateUVs)

    def FileNameLineEditChanged(self, newVal):
        self.fileName = newVal

    def PickDirectoryButtonClicked(self):
        pickedLocation = QFileDialog().getExistingDirectory()
        self.saveDirectoryLineEdit.setText(pickedLocation)
        self.saveLocation = pickedLocation

    def RunTextureCombiner(self):
        try: #Check for errors
            selectedMesh = mc.ls(sl=True)[0]
        except Exception as e: #Handle errors
            QMessageBox().critical(None, "Error", "Please Select a Mesh!")
            return
        if self.resolution == "":
            QMessageBox().critical(None, "Error", "Please set a resolution!")
            return
        elif self.fileName == "":
            QMessageBox().critical(None, "Error", "Please set a filename!")
            return
        elif self.saveLocation == "":
            QMessageBox().critical(None, "Error", "Please pick a save location!")
            return
        
        textureCombiner = TextureCombiner(self.resolution, self.saveLocation, self.fileName)
        textureCombiner.source = selectedMesh
        
        textureCombiner.ReadySelectionForSampling()
        if (self.shouldCreateUVs):
            textureCombiner.CreateNewUVs()
        textureCombiner.RunSurfaceSampler()

    def SetResolution(self, newVal):
        self.resolution = newVal
        
textureWidget = TextureCombinerWidget()
textureWidget.show()