"""
Created by: Christopher Kotschwar

Description: This script will select verts of a skinned mesh inside an arbitrary mesh volume. It should work correctly if the
volume is slightly concave. If two volumes are intersecting
it will interpolate the weighting between the two, otherwise it will set all weighting of the joint to 1. 
The volumes are named in relation to which joint they affect.

The required naming of volumes is "BindVolume_For_Joint_" + any_joint_name + anyNumber
it is important that the volumes be named in this way, as they are considered through their naming.

Run the volumeBindWindow gui and bind to joint by volume.


"""
import math

import maya.OpenMaya as OpenMaya
import maya.cmds as cmds
import maya.mel as mel


class IncorrectSceneSetup(Exception):
    def __init__(self, value):
        self.value = value

    def __str__(self):
        return repr(self.value)


class Vector(list):
    def __init__(self, data):
        super(Vector, self).__init__(data)
        self.data = data

    def __repr__(self):
        return repr(self.data)

    def __add__(self, other):

        data = []  # start with an empty list

        for j in range(len(self.data)):
            data.append(self.data[j] + other.data[j])

        return Vector(data)

    def __sub__(self, other):

        data = []  # start with an empty list

        for j in range(len(self.data)):
            data.append(self.data[j] - other.data[j])

        return Vector(data)

    def __mul__(self, other):

        data = []  # start with an empty list

        for j in range(len(self.data)):
            data.append(self.data[j] * other.data[j])

        return Vector(data)

    def __div__(self, other):

        data = []  # start with an empty list

        for j in range(len(self.data)):
            data.append(self.data[j] / other.data[j])

        return Vector(data)

    def __getitem__(self, index):
        return self.data[index]

    def __len__(self):
        return len(self.data)


def dot_product(v, w):
    """
    v and w are points of [x,y,z] that can be multiplied together, It returns an integer.
    """
    # (P1x * P2x) + (P1y * P2y) + (p1z * p2z)
    return v[0] * w[0] + v[1] * w[1] + v[2] * w[2]


def cross_product(v, w):
    """
    v and w are points of [x,y,z] that can be multiplied together, it returns a tupple.
    """
    # x = (p1y * p2z) - (p1z * p2y)
    # y = (p1z * p2x) - (p1x * p2z)
    # z = (p1x * p2y) - (p1y * p2x)
    # return x, y, z
    x = v[1] * w[2] - v[2] * w[1]
    y = v[2] * w[0] - v[0] * w[2]
    z = v[0] * w[1] - v[1] * w[0]

    return (x, y, z)


def normalizeNormal(v):
    """
    v is a normal, which is a vector of [x, y, z] we will take the squareroot of each of these to get the normalisation
    factor, then divide each of these by the normalisation factor.
    """
    addedSquares = ((v[0] ** 2) + (v[1] ** 2) + (v[2] ** 2))
    normalizeFactor = math.sqrt(addedSquares)
    normalizedNormal = [v[0] / normalizeFactor, v[1] / normalizeFactor, v[2] / normalizeFactor]
    return normalizedNormal


class MeshVolume(object):
    def __init__(self, skinClust):
        self.volumesInScene = None
        self.jointsInScene = None
        self.skinClust = skinClust

        self.get_joints_in_scene()
        self.getVolumesInScene()
        self.getJointsToWeight()
        self.getSkinsToWeight()
        self.getRelatedVolumes()

        # Test to make sure the scene is set up correctly and we have all of the information we need,
        # If not, raise an exception and exit the script.
        try:
            if not self.jointsInScene:
                raise IncorrectSceneSetup(
                    "No joints in scene. Please bind a mesh to joints before running this script.")
            if not self.relatedVolumes:
                raise IncorrectSceneSetup(
                    "No volumes to bind with, please create binding volumes before running this script.")
            if not self.jointsToWeight:
                raise IncorrectSceneSetup(
                    "No joints match volume names. Please make sure joints and volumes are named correctly.")
            if not self.skinsToWeight:
                raise IncorrectSceneSetup(
                    "No mesh has been bound to an affected joint. Please bind meshes to joints with an affecting volume.")
        except IncorrectSceneSetup as e:
            print("Problem with scene: ", e.value)
            raise
        self.bindByVolume()

    def get_joints_in_scene(self):
        # Gather a list of joints we will be testing.
        self.jointsInScene = cmds.ls(type="joint")

    def getVolumesInScene(self):
        """
        I am gathering all transform nodes in the scene and checking to see if they have "BindVolume" in their name.
        if they do, they are considered for binding.
        """
        transforms = cmds.ls(type="transform")
        listOfVolumes = []
        for node in transforms:
            transformName = node.split("_")

            if "BindVolume" in transformName:
                listOfVolumes.append(node)

        try:
            if len(listOfVolumes) == 0:
                raise IncorrectSceneSetup("No Volumes in scene, please create volumes.")
        except IncorrectSceneSetup as e:
            print("Problem with scene: ", e.value)
            raise

        print("Triangulating volumes\n")
        print("Deleting volumes History")
        for volume in listOfVolumes:
            cmds.polyTriangulate(volume, ch=True)
            cmds.delete(volume, ch=True)

        self.volumesInScene = listOfVolumes

    def getJointsToWeight(self):
        # Compare the Volumes with the Joints, only those joints that have a volume will be returned as a list.
        jointsToReturn = []
        for jointNode in self.jointsInScene:
            for volume in self.volumesInScene:
                splitName = volume.split("_")
                jointName = "_".join(splitName[3:-1])

                if jointNode == jointName:
                    jointsToReturn.append(jointNode)

        self.jointsToWeight = jointsToReturn

    def getSkinsToWeight(self):
        # Gather a list of skins that we will be testing. Make sure they have a skin cluster with the affected joints.

        numberOfSkinsAffected = len([self.skinClust])

        if numberOfSkinsAffected > 1:
            print("Please choose only 1 skin cluster to weight.")
            return

        skinClustersInScene = cmds.ls(type="skinCluster")

        # Test to see if it exists
        if self.skinClust in skinClustersInScene:
            # Get a list of joints affected, we will compare this to the joints that have binding volumes
            # and make sure the joints with volumes affect this skin cluster.
            jointInfluences = cmds.skinCluster(self.skinClust, q=True, inf=True)

            # Returns Shape Node, this will be the shape node that we will be getting our verts to test from.
            geoInfluenced = cmds.skinCluster(self.skinClust, q=True, g=True)

            for volumeJoint in self.jointsToWeight:
                if volumeJoint not in jointInfluences:
                    print(str(volumeJoint) + " does not influence " + str(geoInfluenced) + "\n")
                    print("Please make sure all joints with volumes influence " + str(geoInfluenced))
                else:
                    self.skinsToWeight = geoInfluenced


        else:
            print("Skin cluster does not exist. Please enter correct skin cluster name.")

    def getRelatedVolumes(self):
        # Compare the Volumes with the Joints, only those joints that have a volume will be returned as a list.
        volumesToReturn = []

        for volume in self.volumesInScene:
            splitName = volume.split("_")
            jointName = "_".join(splitName[3:-1])

            if jointName not in self.jointsToWeight:
                print("Volume " + str(volume) + " has no affected joints. Skipped.")
            else:
                volumesToReturn.append(volume)

        self.relatedVolumes = volumesToReturn

    def getAllVerts(self):
        # Gather all verts in the scene to compare against the volume triangles.
        vertsToReturn = []

        meshTransform = str(cmds.listRelatives(self.skinnedMesh, ap=True)[0])

        vertCount = cmds.polyEvaluate(self.skinnedMesh, v=True)

        while (vertCount >= 0):
            vertsToReturn.append(meshTransform + ".vtx[" + str(vertCount) + "]")
            vertCount = vertCount - 1

        self.vertsOfSkinnedMesh = vertsToReturn

    def checkBoundingBox(self):
        # If there are verts outside of the bounding box then they cannot
        # be inside of the volume.

        vertsToReturn = []

        # returns [xmin, ymin, zmin, xmax, ymax, zmax]
        boundingBox = cmds.exactWorldBoundingBox(self.currentVolume)

        for vert in self.vertsOfSkinnedMesh:
            vertPos = cmds.pointPosition(vert, w=True)
            if vertPos[0] > boundingBox[0] and vertPos[1] > boundingBox[1] and vertPos[2] > boundingBox[2] and vertPos[
                0] < boundingBox[3] and vertPos[1] < boundingBox[4] and vertPos[2] < boundingBox[5]:
                vertsToReturn.append(vert)

        self.vertsInBoundingBox = vertsToReturn

    def createVertDictionary(self):
        # Create a dictionary of all verts in scene, the key is the vert #, the value is blank for now.
        # We will fill it up later on whether it intersects or not.
        self.allVerts = {}
        for vert in self.vertsOfSkinnedMesh:
            self.allVerts[vert] = []

    def createDictOfIntersectCount(self):
        self.intersectCount = {}

        for vert in self.vertsInBoundingBox:
            self.intersectCount[vert] = 0

    def getTrianglesInVolume(self):
        # Gather triangles of the current volume.
        self.trianglesInVolume = []

        # I use OpenMaya to get the list of triangles quickly.

        # Create an empty list, MSelectionList is not actually what is selected,
        # It is just a list of MObjects, probably DAG nodes.
        selectionList = OpenMaya.MSelectionList()

        # MGlobal.getSelectionListByName("string", MSelectionList) grabs a dag object named "string"
        # and adds it to the MSelectionList.
        OpenMaya.MGlobal.getSelectionListByName(self.currentVolume, selectionList)

        # MItSelectionList takes a MSelectionList object, and makes it iterable,
        # Maya claims it iterates through that selection list, but really it requires
        # more input from you to iterate.
        # MFn.kGeometric is asking it to only iter through the shape node geometry.
        # We have to use MItSelectionList so we can only get the shape node
        # And so we can use the method getDependnode in MItSelectionList as well.
        iterList = OpenMaya.MItSelectionList(selectionList, OpenMaya.MFn.kGeometric)

        while not iterList.isDone():

            # create an empty MObject to fill up.
            mObj = OpenMaya.MObject()

            # MItSelectionList().getDependnode(MObject) will get the dependency node
            # Of the current object of the iterate.
            iterList.getDependNode(mObj)

            # The dependency node itself is a list of objects, we want to gather all of the
            # polygon data in this node, and make an iterable list.
            # MItMeshPolygon(MObject) does this.

            itMeshPolygon = OpenMaya.MItMeshPolygon(mObj)

            # We now need to iterate through all of the polygon data.
            while not itMeshPolygon.isDone():
                # Make some empty arrays and objects in maya, things that the API needs to fill.
                pointArray = OpenMaya.MPointArray()
                # Create an Int array, these are the vert numbers of the triangle in maya. This is what
                # We are going to use later.
                vertexList = OpenMaya.MIntArray()
                # We are in object space, so we set MSpace.kObject
                space = OpenMaya.MSpace.kObject

                # Get the triangles in the polygon mesh, we want to save the vertexList.
                itMeshPolygon.getTriangles(pointArray, vertexList, space)

                # Add the vert list to the variable.
                self.trianglesInVolume = self.trianglesInVolume + [vertexList]

                itMeshPolygon.next()
            iterList.next()

    def getVolumeCenter(self):
        # Start point of line, and end of line. Creates a matrix.
        vertsToTest = []
        volumeCenter = Vector([0, 0, 0])

        vertCount = cmds.polyEvaluate(self.currentVolume, v=True)

        while (vertCount > 0):
            vertsToTest.append("%s.vtx[%i]" % (self.currentVolume, vertCount))
            vertCount = vertCount - 1

        for i in vertsToTest:
            volumeCenter = volumeCenter + Vector(cmds.pointPosition(i))

        volumeCenter = volumeCenter / Vector([len(vertsToTest), len(vertsToTest), len(vertsToTest)])

        self.volumeCenter = volumeCenter

    def startProgressBar(self):
        totalCyclesForVolume = len(self.vertsInBoundingBox) + len(self.trianglesInVolume)

        self.gMainProgressBar = mel.eval("$tmp = $gMainProgressBar")
        cmds.progressBar(self.gMainProgressBar, edit=True, beginProgress=True, isInterruptable=False,
                         status="Calculating verts in Volume " + self.currentVolume, maxValue=totalCyclesForVolume)

    def getPlaneNormals(self):
        # Calculate the normal of the plane we are going to test, returns matrix
        # I can't get the normals from Maya correctly, so I have to do it the hard way
        # Formula for getting Normals:
        # Get the 2 vectors: Vector1 = vertB - vertA	Vector2 = vertC - vertA
        # Cross product of Vector1 and Vector2 gets us [NormalX, NormalY, NormalZ]
        vertA = Vector(cmds.pointPosition(self.triangleVerts[0]))
        vertB = Vector(cmds.pointPosition(self.triangleVerts[1]))
        vertC = Vector(cmds.pointPosition(self.triangleVerts[2]))

        Vector1 = vertB - vertA
        Vector2 = vertC - vertA

        Normal = cross_product(Vector1, Vector2)
        Normal = normalizeNormal(Normal)

        self.triangleNormal = Normal

    def earlyOuts(self):
        # Test for early outs.
        # Are we on the backfacing side? If so, we'll never collide, return 0
        self.meshVert = Vector(cmds.pointPosition(self.currentVert))
        self.triVertA = Vector(cmds.pointPosition(self.triangleVerts[0]))
        self.triVertB = Vector(cmds.pointPosition(self.triangleVerts[1]))
        self.triVertC = Vector(cmds.pointPosition(self.triangleVerts[2]))
        self.triNormalVector = Vector(self.triangleNormal)
        self.volCenterVector = Vector(self.volumeCenter)

        if (dot_product(self.meshVert, self.triNormalVector) - dot_product(self.triVertA,
                                                                           self.triNormalVector)) < 0 and (
                dot_product(self.volCenterVector, self.triNormalVector) - dot_product(self.triVertA,
                                                                                      self.triNormalVector)) < 0:
            return False
        if (dot_product(self.meshVert, self.triNormalVector) - dot_product(self.triVertA,
                                                                           self.triNormalVector)) > 0 and (
                dot_product(self.volCenterVector, self.triNormalVector) - dot_product(self.triVertA,
                                                                                      self.triNormalVector)) > 0:
            return False

        return True

    def lineSegmentPlaneIntersection(self):
        # Test to see if the line intersects with the plane and at what point.
        meshVertToOrigin = dot_product(self.triNormalVector, self.meshVert)
        triVertAToOrigin = dot_product(self.triNormalVector, self.triVertA)

        distToMesh = (meshVertToOrigin - triVertAToOrigin)

        lineSegment = (self.volCenterVector - self.meshVert)

        rayToCenter = dot_product(self.triNormalVector, lineSegment)

        distMid = -(distToMesh / rayToCenter)

        distMid = Vector([distMid, distMid, distMid])

        self.intersectPoint = self.meshVert + distMid + lineSegment

    def halfSpaceTest(self, normal, planePoint):
        vectorToPoint = self.intersectPoint - planePoint
        distanceToPlane = dot_product(normal, vectorToPoint)
        if distanceToPlane > 0:
            return "Positive"
        if distanceToPlane < 0:
            return "Negative"
        if distanceToPlane == 0:
            return "OnPlane"

    def lineSegmentTriangleIntersection(self):
        # Check to see if intersectPoint is inside the triangle.
        Edge0 = self.triVertB - self.triVertA
        Normal0 = cross_product(Edge0, self.triNormalVector)

        if self.halfSpaceTest(Normal0, self.triVertA) == "Positive":
            return False

        Edge1 = self.triVertC - self.triVertB
        Normal1 = cross_product(Edge1, self.triNormalVector)
        if self.halfSpaceTest(Normal1, self.triVertB) == "Positive":
            return False

        Edge2 = self.triVertA - self.triVertC
        Normal2 = cross_product(Edge2, self.triNormalVector)
        if self.halfSpaceTest(Normal2, self.triVertC) == "Positive":
            return False

        return True

    def testCollision(self):
        for singleSkinnedVert in self.vertsInBoundingBox:
            self.currentVert = singleSkinnedVert

            # Test for early outs.
            if not self.earlyOuts():
                continue

            # Find the intersection point of the plane, return self.intersectPoint
            self.lineSegmentPlaneIntersection()

            if self.lineSegmentTriangleIntersection():
                self.intersectCount[self.currentVert] = self.intersectCount[self.currentVert] + 1

    def setupCollision(self):
        for triangle in self.trianglesInVolume:
            self.currentTriangle = triangle

            # Convert our vert list for our current triangle vert indices into maya's vertex names. "MeshName.vtx[1]" etc.
            self.triangleVerts = ["%s.vtx[%i]" % (self.currentVolume, self.currentTriangle[0]),
                                  "%s.vtx[%i]" % (self.currentVolume, self.currentTriangle[1]),
                                  "%s.vtx[%i]" % (self.currentVolume, self.currentTriangle[2])]

            self.getPlaneNormals()
            self.testCollision()

            # Step progress Bar Forward
            cmds.progressBar(self.gMainProgressBar, e=True, step=1)

    def checkCollisionCount(self):
        # Check to see if the vert intersected an even number, or 0 times.
        for vert in self.intersectCount.items():
            vertName = vert[0]
            count = vert[1]
            if not count % 2 or count == 0:
                # This checks to make sure the jointname is not already in
                # allverts, then creates a list of the joint name, and the volume
                if self.jointName not in self.allVerts[vertName]:
                    self.allVerts[vertName] = self.allVerts[vertName] + [(self.jointName, self.currentVolume)]

    def checkAllVolumes(self):
        # Check to see if there are any verts in all volumes, based on the skinned mesh that we are working
        # with.
        for volume in self.relatedVolumes:
            # Load volume in memory, we'll come back to it a lot.
            self.currentVolume = volume

            # Create an empty list that will be filled with all of the verts that are within a volume later.
            self.vertsInCurrentVolume = []

            # Seperate the name of the volume by its underscore, that way we can extract the name
            # of the joint that it affects. It is important that the user created correctly named
            # joints or this will cause problems at this stage.
            splitName = volume.split("_")
            self.jointName = "_".join(splitName[3:-1])

            # See if the verts are within the bounding box of the volume,
            # Not in the bounding box? We can rule it out cheaply.
            self.checkBoundingBox()

            # If there is nothing in the bounding box, go to the next volume.
            if len(self.vertsInBoundingBox) == 0:
                continue

            # Create dictionary self.intersectCount and fill it up with the verts in the bounding box,
            # default the values to 0, we will add 1 to each key when the vert intersects a triangle of the current
            # volume.
            self.createDictOfIntersectCount()

            # Get a list of all triangles in the volume.
            # Creates variable self.trianglesInVolume
            self.getTrianglesInVolume()

            # returns self.VolumeCenter
            self.getVolumeCenter()

            # Start the progress bar.
            self.startProgressBar()

            # Check for collisions
            self.setupCollision()

            # End the progress Bar
            cmds.progressBar(self.gMainProgressBar, e=True, endProgress=True)

            # Test to see if the times a vert has intersected is divisible by 2 or if it's 0
            # then it's inside of the volume. Add it to the list of verts that are inside the volume.
            self.checkCollisionCount()

    def checkOverlap(self):
        # This test sees if the list of volumes that the vert is associated with is > 0
        # a vert is associated with a volume if it is inside of that volume.
        # I am creating a new dictionary vertsInAllVolumes and associating the vert name
        # with the list of joints and verts from allVerts dictionary.
        # allVerts was a placeholder to capture all of the verts, and it is easier to
        # create a new dictionary with verts inside of volumes than delete the entry
        # of a vert with no volumes associated with it.
        for vert in self.allVerts.items():
            vertName = vert[0]
            volumeList = vert[1]

            if len(volumeList) > 0:
                self.vertsInAllVolumes[vertName] = volumeList

    def getDistanceToCenter(self):
        # Calculate the distance to the center of the volume.
        testVert = Vector(cmds.pointPosition(self.vertName))
        self.distanceToCenter = math.sqrt(
            ((testVert[0] - self.volumeCenter[0]) ** 2) + ((testVert[0] - self.volumeCenter[0]) ** 2) + (
                        (testVert[0] - self.volumeCenter[0]) ** 2))

    def getDistanceAndBlend(self):
        # take out the name of the joint, and the volume,
        # put it in an empty dictionary to be used later
        for jointVolTupple in self.listOfJointsVolumes:
            jointName = str(jointVolTupple[0])

            self.volumeCenters[jointName] = []

            self.currentVolume = jointVolTupple[1]

            # Find the volume's center point
            self.getVolumeCenter()

            # Calculate the distance of the vert to the center.
            self.getDistanceToCenter()

            # Append to the dictionary
            self.volumeCenters[jointName] = self.volumeCenters[jointName] + [self.distanceToCenter]

        totalDistances = 0.0
        for val in self.volumeCenters.items():

            jointName = str(val[0])

            # This is a list of all of the volumes for this joint.
            distances = val[1]
            totalDistances = 0.0
            for distance in distances:
                totalDistances += distance

        for val in self.volumeCenters.items():
            jointName = str(val[0])

            distances = val[1]

            self.volumeCenters[jointName] = []

            for distance in distances:
                self.volumeCenters[jointName] = self.volumeCenters[jointName] + [distance / totalDistances]

            self.jointsToNormalize = {jointName: 0.0}

        self.allDistances = 0.0

        for val in self.volumeCenters.items():

            jointName = str(val[0])

            # This is a list of all of the volumes for this joint.
            distances = val[1]

            totalVal = 0.0
            for i in distances:
                # Gaussian falloff
                currentVal = math.exp(-(i / 2.0 * .1 ** 2.0))
                # if volumes overlap, they will add to eachother
                totalVal = totalVal + currentVal

                self.jointsToNormalize[jointName] = totalVal

                self.allDistances = self.allDistances + totalVal

        # Normalize weights
        for val in self.jointsToNormalize.items():
            jointName = str(val[0])

            # This is the weight of the current joint
            weight = val[1]

            self.jointsVal[jointName] = weight / self.allDistances

    def calculateBlend(self):
        self.vertInMultVolumes = []
        for vert in self.vertsInAllVolumes.items():
            self.listOfJointsVolumes = vert[1]
            self.vertName = vert[0]

            # Vert is inside only one volume.
            if len(self.listOfJointsVolumes) == 1:
                cmds.skinPercent(self.skinClust, self.vertName,
                                 transformValue=[(str(self.listOfJointsVolumes[0][0]), 1.0)])

            # Vert is inside multiple volumes
            else:
                self.vertInMultVolumes.append(self.vertName)
                self.jointsVal = {}
                self.volumeCenters = {}
                self.getDistanceAndBlend()
                cmds.skinPercent(self.skinClust, self.vertName, transformValue=self.jointsVal.items())

        cmds.select(self.vertInMultVolumes)

    # mel.eval('doSmoothSkinWeightsArgList 2 { "0", "5", "0" };')
    # cmds.select(cl=True)

    # cmds.skinPercent( self.skinClust, self.vertName, transformValue = [(str(self.listOfJointsVolumes[0][0]), 1.0)])
    def bindByVolume(self):
        # For each skinned mesh, we have to check each vert, then compare it against each triangle in the
        # volumes.
        for skinnedMesh in self.skinsToWeight:
            # Let's start storing some of this information in memory.
            # We need to do this here because these items will be called by other functions
            # down the line.
            self.skinnedMesh = skinnedMesh

            # Get all of the verts of the skinned mesh, create variable self.vertsOfSkinnedMesh
            self.getAllVerts()

            # create a dictionary with all of the verts as keys, and an empty list definition
            # that we will use later, creates self.allVerts
            self.createVertDictionary()

            # create an empty dictionary for all volumes of verts, we will fill this later.
            self.vertsInAllVolumes = {}

            # Check to see if there are any verts in all volumes.
            self.checkAllVolumes()

            self.checkOverlap()

            self.calculateBlend()
