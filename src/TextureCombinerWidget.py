from PySide2.QtWidgets import QHBoxLayout, QLabel, QLineEdit, QMainWindow, QMessageBox, QPushButton, QSlider, QVBoxLayout, QWidget #import classes from the QtWidgets module
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

    #TODO: Combine meshes
    #TODO: Delete history


    def ReadySelectionForSampling(self):
        #Get selected mesh and duplicate
        self.target = mc.duplicate(self.source, n=(self.source + "_dup"))[0]

        #Auto unwrap UVs with padding
        mc.polyAutoProjection(f'{self.target}.f[*]', ps=0.5)
        self.MakeOutputMaterial(self.target)
        #Delete history (c)hannel (h)istory
        mc.delete(self.target, ch=True)
        #Freeze transform
        mc.makeIdentity(self.target)

    def MakeOutputMaterial(self, object):
        outputMat = mc.shadingNode('aiStandardSurface', asShader=True, name="M_Output")
        outputMatSG = mc.sets(name="%sSG" % outputMat, empty=True, renderable=True, noSurfaceShader=True)
        mc.connectAttr("%s.outColor" % outputMat, "%s.surfaceShader" % outputMatSG)
        #mc.sets(object, forceElement=outputMat)

    def RunSurfaceSampler(self):
        commandString = f'surfaceSampler -target {self.target} -searchOffset 0 -maxSearchDistance 0 -searchCage "" '
        commandString += f'-source {self.source} -mapOutput normal -mapWidth {self.textureResolution} -mapHeight {self.textureResolution} -max 1 -mapSpace tangent -mapMaterials 1 -shadows 1 '
        commandString += f'-filename "{self.outputDestination}/{self.filename}_normal" -fileFormat "png" -mapOutput diffuseRGB '
        commandString += f'-mapWidth {self.textureResolution} -mapHeight {self.textureResolution} -max 1 -mapSpace tangent -mapMaterials 1 -shadows 1 -filename "{self.outputDestination}/{self.filename}_color" -fileFormat "png" '
        commandString += f'-superSampling 3 -filterType 0 -filterSize 3 -overscan 1 -searchMethod 0 -useGeometryNormals 1 -ignoreMirroredFaces 0 -flipU 0 -flipV 0'

        print(commandString)
        mel.eval(commandString)

        #mc.delete(self.source)
        #self.target.replace("_dup", "")

class TextureCombinerWidget(MayaWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Texture Combiner")
        self.textureCombiner = TextureCombiner(1024, "D:/Unity/Assets/CombinedItems", "ShelfItems")

        self.masterLayout = QVBoxLayout()
        self.setLayout(self.masterLayout)

        combineTextureButton = QPushButton("Combine Textures")
        combineTextureButton.clicked.connect(self.RunTextureCombiner)
        self.masterLayout.addWidget(combineTextureButton)

    def RunTextureCombiner(self):
        try: #Check for errors
            selectedMesh = mc.ls(sl=True)[0]
        except Exception as e: #Handle errors
            raise Exception("Please select a mesh") #Display error
        
        self.textureCombiner.source = selectedMesh
        self.textureCombiner.ReadySelectionForSampling()
        self.textureCombiner.RunSurfaceSampler()
        
textureWidget = TextureCombinerWidget()
textureWidget.show()