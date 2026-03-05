#
# Revision History
#
# Date          Name                Description of Change
# 20-Nov-2012   Volker Grabowski    Initial version
# 13-Jan-2014   Volker Grabowski    Add NCTypeSystem class
# 20-Jan-2015   Volker Grabowski    Add ASYNC_RAPID motion type
# 08-Oct-2015   Volker Grabowski    Add documentation and fix command/method argument instantiation
# 20-Oct-2015   Volker Grabowski    PR7539807: Control partial indexing in NCArrayType, remove IsComposed flag from NCStructType
# 06-May-2016   Volker Grabowski    Fix merge error caused by rebase to new NX11 baseline
# 11-May-2016   Thomas Schulz       Fix a typo of GetCallStackDepth
# 02-Sep-2016   Volker Grabowski    Catch type errors to avoid passing invalid references to CSE
# 04-Oct-2016   Volker Grabowski    PR7847201: Return None from ParseNCExpression in error case
# 31-Jan-2017   Volker Grabowski    PR7254570: Add PeekLine to CallFactory
# 08-Feb-2017   Volker Grabowski    cam17015.1: Add ExecuteMetacode to Controller
# 11-Jul-2017   Volker Grabowski    cam17015.1: Add missing API functions required for metacodes
# 08-Sep-2017   Volker Grabowski    Fix API typos and bugs
# 17-Oct-2017   Volker Grabowski    PR9021170: Add missing AnyController commands and CSE query methods
# 03-Jan-2018   Volker Grabowski    Add abstract expression factory methods

import CSE
import math



################################################################################
# Exceptions
################################################################################

class CseParseError(Exception):
    pass

class CseTypeError(Exception):
    pass


################################################################################
# Tolerances
################################################################################

g_dEps = 0.001
g_dAngleEps = 0.001 * math.pi / 180.0
g_dSinEps = math.sin(g_dAngleEps)
g_dCosEps = math.cos(g_dAngleEps)


################################################################################
# Math
################################################################################

# 3D vector class.
class Vector3:
    def __init__(self, x = 0, y = 0, z = 0):
        self.vec = [float(x), float(y), float(z)]

    def __add__(self, vec):
        return Vector3(self.vec[0] + vec.vec[0], self.vec[1] + vec.vec[1], self.vec[2] + vec.vec[2])

    def __sub__(self, vec):
        return Vector3(self.vec[0] - vec.vec[0], self.vec[1] - vec.vec[1], self.vec[2] - vec.vec[2])

    def __iadd__(self, vec):
        self.vec[0] = vec.vec[0] + self.vec[0]
        self.vec[1] = vec.vec[1] + self.vec[1]
        self.vec[2] = vec.vec[2] + self.vec[2]
        return self

    def __isub__(self, vec):
        self.vec[0] = self.vec[0] - vec.vec[0]
        self.vec[1] = self.vec[1] - vec.vec[1]
        self.vec[2] = self.vec[2] - vec.vec[2]
        return self

    def __div__(self, val : float):
        return Vector3(self.vec[0] / val, self.vec[1] / val, self.vec[2] / val)

    def __mul__(self, val : float):
        return Vector3(self.vec[0] * val, self.vec[1] * val, self.vec[2] * val)

    def __idiv__(self, val : float):
        self.vec[0] = self.vec[0] / val
        self.vec[1] = self.vec[1] / val
        self.vec[2] = self.vec[2] / val
        return self

    def __imul__(self, val : float):
        self.vec[0] = self.vec[0] * val
        self.vec[1] = self.vec[1] * val
        self.vec[2] = self.vec[2] * val
        return self

    def __getitem__(self, idx : int) -> float:
        if idx >= 0 and idx <= 2:
            return self.vec[idx]
        else:
            raise Exception("CSE: Invalid vector access")

    def __setitem__(self, idx : int, val : float):
        if idx >= 0 and idx <= 2:
            self.vec[idx] = val
        else:
            raise Exception("CSE: Invalid vector access")

    def __str__(self):
        return "(" + str(self.vec[0]) + "," + str(self.vec[1]) + "," + str(self.vec[2]) + ")"

    @staticmethod
    def CreateVectorFromList(elements : list):
        vector = Vector3()
        vector.vec = [elements[0], elements[1], elements[2]]
        return vector

# Computes the dot product of two vectors.
def Dot(vec1 : Vector3, vec2 : Vector3) -> float:
    return vec1[0] * vec2[0] + vec1[1] * vec2[1] + vec1[2] * vec2[2]

# Computes the cross product of two vectors.
def Cross(vec1 : Vector3, vec2 : Vector3) -> Vector3:
    return Vector3(vec1[1] * vec2[2] - vec1[2] * vec2[1],
                   vec1[2] * vec2[0] - vec1[0] * vec2[2],
                   vec1[0] * vec2[1] - vec1[1] * vec2[0])

# Computes the determinant of three vectors.
def Determinant(vec1 : Vector3, vec2 : Vector3, vec3 : Vector3) -> float:
    return vec1[0] * ((vec2[1] * vec3[2]) - (vec3[1] * vec2[2])) \
         - vec1[1] * ((vec2[0] * vec3[2]) - (vec3[0] * vec2[2])) \
         + vec1[2] * ((vec2[0] * vec3[1]) - (vec3[0] * vec2[1]))

# Returns the length of a vector.
def Length(vec : Vector3) -> float:
    return math.sqrt(Dot(vec, vec))

# Returns the distance between two points.
def Distance(pt1 : Vector3, pt2 : Vector3) -> float:
    return Length(pt2 - pt1)

# Returns a new vector that has the same direction as vec, but has a length of one.
def Normalize(vec : Vector3) -> Vector3:
    if (vec[0] == 0.0 and vec[1] == 0.0 and vec[2] == 0.0):
        return Vector3()
    return vec / Length(vec)

# Returns an arbitrary perpendicular vector with respect to the input vector
def GetPerpVec(vec : Vector3) -> Vector3:
    xAbs = math.fabs(vec[0])
    yAbs = math.fabs(vec[1])
    zAbs = math.fabs(vec[2])

    if zAbs < xAbs:
        if zAbs < yAbs:
            return Vector3(-vec[1], vec[0], 0.0)
        else:
            return Vector3(vec[2], 0.0, -vec[0])
    else:
        if xAbs < yAbs:
            return Vector3(0.0, -vec[2], vec[1])
        else:
            return Vector3(vec[2], 0.0, -vec[0])



# 4x4 matrix class.
class Matrix4:
    def __init__(self):
        self.mat = [[1.0, 0.0, 0.0, 0.0],
                    [0.0, 1.0, 0.0, 0.0],
                    [0.0, 0.0, 1.0, 0.0],
                    [0.0, 0.0, 0.0, 1.0]]

    def SetRowVec(self, index : int, vec : Vector3):
        self.mat[index][0] = vec[0]
        self.mat[index][1] = vec[1]
        self.mat[index][2] = vec[2]

    def GetRowVec(self, index : int) -> Vector3:
        return Vector3(self.mat[index][0], self.mat[index][1], self.mat[index][2])

    def GetColVec(self, index : int) -> Vector3:
        return Vector3(self.mat[0][index], self.mat[1][index], self.mat[2][index])

    def MultiplyVec(self, vec : Vector3) -> Vector3:
        return Vector3(Dot(self.GetColVec(0), vec),
                       Dot(self.GetColVec(1), vec),
                       Dot(self.GetColVec(2), vec))

    def MultiplyPt(self, pt : Vector3) -> Vector3:
        return self.MultiplyVec(pt) + GetRowVec(3)

    def __mul__(self, mat):
        matProd = Matrix4()
        for row in range(4):
            for col in range(4):
                for i in range(4):
                    matProd.mat[row][col] += self.mat[row][i] * mat[i][col]
        return matProd

    def __imul__(self, mat):
        matProd = self * mat
        self.mat = matprod.mat
        return self

    def Transpose(self):
        for i in range(1, 4):
            for j in range(i):
                dTmp = self.mat[i][j]
                self.mat[i][j] = self.mat[j][i]
                self.mat[j][i] = dTmp

    def Translate(self, vec : Vector3):
        self.mat[3][0] += vec[0]
        self.mat[3][1] += vec[1]
        self.mat[3][2] += vec[2]

    def GetTranslation(self) -> Vector3:
        return mat.GetRowVec(3)

    def Scale(self, vec : Vector3):
        for i in range(4):
            self.mat[i][0] *= vec[0]
            self.mat[i][1] *= vec[1]
            self.mat[i][2] *= vec[2]

    def GetScale(self, nAxis : int) -> float:
        if nAxis == 0:
            return Length(Vector3(self.mat[0][0], self.mat[0][1], self.mat[0][2]))
        elif nAxis == 1:
            return Length(Vector3(self.mat[1][0], self.mat[1][1], self.mat[1][2]))
        elif nAxis == 2:
            return Length(Vector3(self.mat[2][0], self.mat[2][1], self.mat[2][2]))
        else:
            return 0

    def RotateX(self, val : float):
        dCos = math.cos(val)
        dSin = math.sin(val)

        for i in range(4):
            dTmp = self.mat[i][1] * dCos - self.mat[i][2] * dSin
            self.mat[i][2] = self.mat[i][1] * dSin + self.mat[i][2] * dCos
            self.mat[i][1] = dTmp

    def RotateY(self, val : float):
        dCos = math.cos(val)
        dSin = math.sin(val)

        for i in range(4):
            dTmp = self.mat[i][0] * dCos + self.mat[i][2] * dSin
            self.mat[i][2] = -self.mat[i][0] * dSin + self.mat[i][2] * dCos
            self.mat[i][0] =  dTmp

    def RotateZ(self, val : float):
        dCos = math.cos(val)
        dSin = math.sin(val)

        for i in range(4):
            dTmp = self.mat[i][0] * dCos - self.mat[i][1] * dSin
            self.mat[i][1] = self.mat[i][0] * dSin + self.mat[i][1] * dCos
            self.mat[i][0] = dTmp

    def RotateByVec(self, vecAxis : Vector3, angle : float):
        vecZ = Normalize(vecAxis)
        vecX = Normalize(GetPerpVec(vecAxis))
        vecY = Cross(vecZ, vecX)

        matBack = Matrix4.CreateMatrixFromVectors(vecX, vecY, vecZ, Vector3(0.0, 0.0, 0.0))
        matForward = Matrix4.CreateMatrixFromVectors(vecX, vecY, vecZ, Vector3(0.0, 0.0, 0.0))
        matForward.Transpose()

        self *= matForward
        self.RotateZ(angle)
        self *= matBack

    def RotateByAngles(self, dXAngle : float, dYAngle : float, dZAngle : float, strRotType : str):
        if strRotType == "RPY":
            self.RotateX(dXAngle)
            self.RotateY(dYAngle)
            self.RotateZ(dZAngle)
        elif strRotType == "Euler":
            self.RotateZ(dXAngle)
            self.RotateX(dYAngle)
            self.RotateZ(dZAngle)

    def GetRotationZYX(self, nAxis : int) -> float:
        # Take only the non-rotational matrix parts into account
        matTmp = Matrix4.CreateMatrixFromList(self.mat)
        matTmp.mat[0][3] = 0.0
        matTmp.mat[1][3] = 0.0
        matTmp.mat[2][3] = 0.0
        matTmp.mat[3][0] = 0.0
        matTmp.mat[3][1] = 0.0
        matTmp.mat[3][2] = 0.0
        matTmp.mat[3][3] = 1.0

        # Rotate the first row (i.e. the rotated x-axis) into the z-x-plane
        vecRow = Vector3(matTmp.mat[0][0], matTmp.mat[0][1], matTmp.mat[0][2])
        dRowLength = Length(vecRow)

        dAngleZ = 0.0
        if dRowLength >= g_dEps and vecRow[2] < g_dCosEps * dRowLength:
            dAngleZ = math.atan2(matTmp.mat[0][1], matTmp.mat[0][0])

        if nAxis == 2:
            return dAngleZ

        matTmp.RotateZ(-dAngleZ)

        # Rotate the first row (i.e. the rotated x-axis) onto the x-axis
        vecRow = Vector3(matTmp.mat[0][0], matTmp.mat[0][1], matTmp.mat[0][2])
        dRowLength = Length(vecRow)

        dAngleY = 0.0
        if dRowLength >= g_dEps and vecRow[1] < g_dCosEps * dRowLength:
            dAngleY = math.atan2(matTmp.mat[0][2], matTmp.mat[0][0])

        if nAxis == 1:
            return -dAngleY

        matTmp.RotateY(dAngleY)

        # Rotate the second row (i.e. the rotated y-axis) into the z-x-plane
        vecRow = Vector3(matTmp.mat[1][0], matTmp.mat[1][1], matTmp.mat[1][2])
        dRowLength = Length(vecRow)

        dAngleX = 0.0
        if dRowLength >= g_dEps and vecRow[0] < g_dCosEps * dRowLength:
            dAngleX = math.atan2(matTmp.mat[1][2], matTmp.mat[1][1])

        if nAxis == 0:
            return dAngleX;

        return 0

    def Invert():
        # Initialization
        reduced = [False, False, False, False]

        row_max = 0
        col_max = 0

        row_save = [0, 0, 0, 0]
        col_save = [0, 0, 0, 0]

        # Reduction loop
        for i in range(4):
            # Look for greatest element
            abs_max = 0.0;

            for row in range(4):
                if not reduced[row]:
                    for col in range(4):
                        if not reduced[col]:
                            abs_val = abs(self.mat[row][col])

                            if abs_max < abs_val:
                                abs_max = abs_val
                                col_max = col
                                row_max = row

            reduced[col_max] = True

            # If necessary: Swap rows so that the greatest element is in the diagonal
            if col_max != row_max:
                for col in range(4):
                    save_elem = self.mat[row_max][col]
                    self.mat[row_max][col] = self.mat[col_max][col]
                    self.mat[col_max][col] = save_elem

            # Store changed order
            row_save[i] = row_max;
            col_save[i] = col_max;

            # Divide pivot row by diagonal element
            pivot_elem = self.mat[col_max][col_max]
            self.mat[col_max][col_max] = 1.0

            for col in range(4):
                self.mat[col_max][col] = self.mat[col_max][col] / pivot_elem

            # Reduce the other rows
            for row in range(4):
                if row != col_max:
                    save_elem = self.mat[row][col_max]
                    self.mat[row][col_max] = 0.0

                    for col in range(4):
                       self.mat[row][col] -= self.mat[col_max][col] * save_elem

        # Swap back
        for index in range(4, 0, -1):
            i = index - 1

            if row_save[i] != col_save[i]:
                row_max = row_save[i]
                col_max = col_save[i]

                for row in range(4):
                    save_elem = self.mat[row][row_max]
                    self.mat[row][row_max] = self.mat[row][col_max]
                    self.mat[row][col_max] = save_elem

    @staticmethod
    def CreateMatrixFromVectors(row0 : Vector3, row1 : Vector3, row2 : Vector3, row3 : Vector3):
        mat = Matrix4()
        mat.SetRowVec(0, row0)
        mat.SetRowVec(1, row1)
        mat.SetRowVec(2, row2)
        mat.SetRowVec(3, row3)
        return mat

    @staticmethod
    def CreateMatrixFromList(elements : list):
        mat = Matrix4()
        mat.SetRowVec(0, Vector3(elements[0][0], elements[0][1], elements[0][2]))
        mat.SetRowVec(1, Vector3(elements[1][0], elements[1][1], elements[1][2]))
        mat.SetRowVec(2, Vector3(elements[2][0], elements[2][1], elements[2][2]))
        mat.SetRowVec(3, Vector3(elements[3][0], elements[3][1], elements[3][2]))
        return mat



# NC coordinate class.
class NCCoordinate:
    def __init__(self, nccoord):
        self.m_nccoord = nccoord

    def SetJointValue(self, strJointName : str, dJointValue : float):
        CSE.Coordinate_SetJointValue(self.m_nccoord, strJointName, dJointValue)

    def GetJointValue(self, strJointName : str) -> float:
        return CSE.Coordinate_GetJointValue(self.m_nccoord, strJointName)



# NC motion class.
class NCMotion:
    def __init__(self, ncmotion):
        self.m_ncmotion = ncmotion

    def GetTargetCoordinate(self) -> NCCoordinate:
        return NCCoordinate(CSE.Motion_GetTargetCoordinate(self.m_ncmotion))

    def GetCenterCoordinate(self) -> NCCoordinate:
        return NCCoordinate(CSE.Motion_GetCenterCoordinate(self.m_ncmotion))

    def GetType(self) -> str:
        return CSE.Motion_GetType(self.m_ncmotion)



################################################################################
# Types
################################################################################

# Base class for all NC types
class NCType:
    # Type kind enum definition. Don't modify!
    KIND_UNDEFINED, KIND_BASIC, KIND_ARRAY, KIND_STRUCT = range(4)

    # Used by factory code. Don't call directly.
    def __init__(self, nctype):
        self.m_nctype = nctype

    # Checks whether this type is equal to another type.
    # @param nctype An NCType object.
    # @return True iff the types are identical.
    def IsEqual(self, nctype):
        return CSE.Type_IsEqual(self.m_nctype, nctype.m_nctype)

    # Creates a derived class instance of this object if available.
    # @return An NCType derived class instance.
    def GetDerivedInstance(self):
        kind = CSE.Type_GetKind(self.m_nctype)
        if kind == NCType.KIND_BASIC:
            return NCBasicType(self.m_nctype)
        elif kind == NCType.KIND_ARRAY:
            return NCArrayType(self.m_nctype)
        elif kind == NCType.KIND_STRUCT:
            return NCStructType(self.m_nctype)
        else:
            return None



# Type class for all scalar data types
class NCBasicType(NCType):
    # Value type enum definition. Don't modify!
    BOOL, CHAR, INTEGER, REAL, DOUBLE, STRING, OBJECT = range(7)

    # This method returns the data type represented by this object.
    # @return The appropriate enum from the above definition.
    def GetValueType(self) -> int:
        return CSE.BasicType_GetValueType(self.m_nctype)



# Type class for array data types of arbitrary dimension
class NCArrayType(NCType):
    # This method returns the type of the values stored in the array.
    # @return The elements' NCType object.
    def GetElementType(self) -> NCType:
        return NCType(CSE.ArrayType_GetElementType(self.m_nctype)).GetDerivedInstance()

    # This method returns the array's number of dimensions.
    # @return The dimension count.
    def GetDimCount(self) -> int:
        return CSE.ArrayType_GetDimCount(self.m_nctype)

    # This method returns the number of elements stored in a given dimension.
    # @param nIndex A dimension index.
    # @return The dimension's element count.
    def GetDimSize(self, nIndex : int) -> int:
        return CSE.ArrayType_GetDimCount(self.m_nctype, nIndex)

    # This method creates an array for this type. It instantiates all elements
    # with default values.
    # @return An NCArray object.
    def CreateArray(self):
        return NCArray(CSE.ArrayType_CreateArray(self.m_nctype))



# Type class for struct data types
class NCStructType(NCType):
    # This method returns the type of the value stored in a given struct field.
    # @param strFieldName The name of a struct field.
    # @return The field's NCType object.
    def GetFieldType(self, strFieldName : str) -> NCType:
        return NCType(CSE.StructType_GetFieldType(self.m_nctype, strFieldName)).GetDerivedInstance()

    # This method defines the default values for this struct type. If a new struct
    # is created (via CreateStruct, see below) it will be initialized with this
    # default element.
    # @param struct An NCStruct object.
    def SetDefaultElement(self, struct):
        return CSE.StructType_SetDefaultElement(self.m_nctype, struct.m_obj)

    # This method creates a struct for this type. It instantiates all fields
    # with default values according to the default struct defined per SetDefaultElement.
    # @return An NCStruct object.
    def CreateStruct(self):
        return NCStruct(CSE.StructType_CreateStruct(self.m_nctype))



################################################################################
# Objects
################################################################################

# Class for NC objects. An NC object can be a scalar value, an array or a struct.
# Each NC object has an NC type.
class NCObject:
    # Object kind enum definition. Don't modify!
    KIND_UNDEFINED, KIND_VALUE, KIND_ARRAY, KIND_STRUCT = range(4)

    # Used by factory code. Don't call directly.
    def __init__(self, obj):
        self.m_obj = obj

    # This method returns the NC type of this object.
    # @return The NCType object.
    def GetType(self) -> NCType:
        return NCType(CSE.Object_GetType(self.m_obj)).GetDerivedInstance()

    # Checks whether this object is equal to another object.
    # @param obj An NCObject object.
    # @return True iff the objects are identical.
    def IsEqual(self, obj):
        return CSE.Object_IsEqual(self.m_obj, obj.m_obj)

    # Creates a clone of this object.
    # @return The copied NCObject instance.
    def Clone(self):
        return NCObject(CSE.Object_Clone(self.m_obj)).GetDerivedInstance()

    # Creates a derived class instance of this object if available.
    # @return An NCObject derived class instance.
    def GetDerivedInstance(self):
        kind = CSE.Object_GetKind(self.m_obj)
        if kind == NCObject.KIND_VALUE:
            return NCValue(self.m_obj)
        elif kind == NCObject.KIND_ARRAY:
            return NCArray(self.m_obj)
        elif kind == NCObject.KIND_STRUCT:
            return NCStruct(self.m_obj)
        else:
            return None

    # Creates a native Python representation of this object if available.
    # @return A native Python representation.
    def GetNativeValue(self):
        return self

    @staticmethod
    def GetNativeObject(obj):
        kind = CSE.Object_GetKind(obj)
        if kind == NCObject.KIND_VALUE:
            return NCValue(obj).GetNativeValue()
        elif kind == NCObject.KIND_ARRAY:
            return NCArray(obj)
        elif kind == NCObject.KIND_STRUCT:
            return NCStruct(obj)
        else:
            return None



# Class to represent scalar values as NC objects. The type of an NC value is an NCType object.
class NCValue(NCObject):
    # Object value type enum definition
    OBJ_UNDEFINED, OBJ_VECTOR, OBJ_MATRIX, OBJ_LIST, OBJ_COORDINATE, OBJ_MOTION = range(6)

    # This method returns the NC basic type of this object.
    # @return The NCBasicType object.
    def GetType(self) -> NCBasicType:
        return NCBasicType(CSE.Object_GetType(self.m_obj))

    # Creates a clone of this object.
    # @return The copied NCValue instance.
    def Clone(self):
        return NCValue(CSE.Object_Clone(self.m_obj))

    # This method returns the scalar value type of this object.
    # @return The type's enum from the NCBasicType enum definition.
    def GetValueType(self):
        return CSE.Value_GetValueType(self.m_obj)

    # Interprets this object's content as a boolean value.
    # @return A boolean value.
    def GetBool(self) -> bool:
        return CSE.Value_GetBool(self.m_obj)

    # Interprets this object's content as an integer value.
    # @return An integer value.
    def GetInteger(self) -> int:
        return CSE.Value_GetInteger(self.m_obj)

    # Interprets this object's content as a double value.
    # @return A double value.
    def GetDouble(self) -> float:
        return CSE.Value_GetDouble(self.m_obj)

    # Interprets this object's content as a string.
    # @return A string.
    def GetString(self) -> str:
        return CSE.Value_GetString(self.m_obj)

    # Interprets this object's content as a vector.
    # @return A vector.
    def GetVector(self) -> Vector3:
        vec = CSE.Value_GetVector(self.m_obj)
        return Vector3(vec[0], vec[1], vec[2])

    # Interprets this object's content as a matrix.
    # @return A matrix.
    def GetMatrix(self) -> Matrix4:
        return Matrix4.CreateMatrixFromList(CSE.Value_GetMatrix(self.m_obj))

    # Interprets this object's content as a list
    # @return A coordinate.
    def GetList(self) -> list:
        return CSE.Value_GetList(self.m_obj)

    def GetNativeValue(self):
        type = self.GetValueType()
        if type == NCBasicType.BOOL:
            return self.GetBool()
        elif type == NCBasicType.CHAR:
            return self.GetInteger()
        elif type == NCBasicType.INTEGER:
            return self.GetInteger()
        elif type == NCBasicType.REAL:
            return self.GetDouble()
        elif type == NCBasicType.DOUBLE:
            return self.GetDouble()
        elif type == NCBasicType.STRING:
            return self.GetString()
        elif type == NCBasicType.OBJECT:
            objVal = CSE.Value_GetObject(self.m_obj)
            valType = CSE.ObjectValue_GetType(objVal)
            if valType == NCValue.OBJ_VECTOR:
                return Vector3.CreateVectorFromList(CSE.Value_GetVector(self.m_obj))
            elif valType == NCValue.OBJ_MATRIX:
                return Matrix4.CreateMatrixFromList(CSE.Value_GetMatrix(self.m_obj))
            elif valType == NCValue.OBJ_LIST:
                return CSE.Value_GetList(self.m_obj)
            elif valType == NCValue.OBJ_COORDINATE:
                return NCCoordinate(objVal)
            elif valType == NCValue.OBJ_MOTION:
                return NCMotion(objVal)
            else:
                return None
        else:
            return None



# Class to represent arrays of arbitrary dimension as NC objects. The type of an NC array is an NCType object.
class NCArray(NCObject):
    # This method returns the NC array type of this object.
    # @return The NCArrayType object.
    def GetType(self) -> NCArrayType:
        return NCArrayType(CSE.Object_GetType(self.m_obj))

    # Creates a clone of this object.
    # @return The copied NCArray instance.
    def Clone(self):
        return NCArray(CSE.Object_Clone(self.m_obj))

    # This method sets the array element at a given index.
    # @param list A list of indices for each of the array's dimensions, e.g. [2, 5] for a two-dimensional array.
    # @param objElement The NC object that is supposed to be assigned to the specified array index.
    def SetElement(self, list : list, objElement : NCObject):
        if not isinstance(objElement, NCObject):
            raise CseTypeError
        return CSE.Array_SetElement(self.m_obj, list, objElement.m_obj)

    # This method retrieves the array element at a given index.
    # @param list A list of indices for each of the array's dimensions, e.g. [2, 5] for a two-dimensional array.
    # @return The NC object at the specified array index.
    def GetElement(self, list : list) -> NCObject:
        return NCObject(CSE.Array_GetElement(self.m_obj, list)).GetDerivedInstance()

    # This method assigns the elements of the given array to this array object.
    # @param ncArray An NC array object.
    def Assign(self, ncArray):
        return CSE.Array_Assign(self.m_obj, ncArray.m_obj)



# Class to represent structs as NC objects. The type of an NC struct is an NCType object.
class NCStruct(NCObject):
    # This method returns the NC struct type of this object.
    # @return The NCStructType object.
    def GetType(self) -> NCStructType:
        return NCStructType(CSE.Object_GetType(self.m_obj))

    # Creates a clone of this object.
    # @return The copied NCStruct instance.
    def Clone(self):
        return NCStruct(CSE.Object_Clone(self.m_obj))

    # This method sets the element of a given struct field.
    # @param strFieldName The name of a struct field.
    # @param objElement The NC object that is supposed to be assigned to the specified struct field.
    def SetField(self, strFieldName : str, objField : NCObject):
        if not isinstance(objField, NCObject):
            raise CseTypeError
        return CSE.Struct_SetField(self.m_obj, strFieldName, objField.m_obj)

    # This method retrieves a struct field element.
    # @param strFieldName The name of a struct field.
    # @param objElement The NC object at the specified struct field.
    def GetField(self, strFieldName : str) -> NCObject:
        return NCObject(CSE.Struct_GetField(self.m_obj, strFieldName)).GetDerivedInstance()

    # This method assigns the fields of the given struct to this struct object.
    # @param ncStruct An NC struct object.
    def Assign(self, ncStruct):
        return CSE.Struct_Assign(self.m_obj, ncStruct.m_obj)

    # This method (de-)activates the variable listener of this struct object.
    # @param bActive A boolean flag.
    def ActivateListener(self, bActive : bool):
        return CSE.Struct_ActivateListener(self.m_obj, bActive)



################################################################################
# Expressions
################################################################################

# Class for NC object expressions. An NC object expression can be evaluated which results in an NC object.
class NCObjectExpression:
    # Used by factory code. Don't call directly.
    def __init__(self, expr):
        self.m_expr = expr

    # Evaluates the expression and returns the result as an NC object.
    # @return An NC object.
    def GetObject(self) -> NCObject:
        return NCObject(CSE.ObjExpr_GetObject(self.m_expr)).GetDerivedInstance()



# This class represents scalar NC object expressions, i.e. their evaluation results in an instance of NCValue.
class NCExpression(NCObjectExpression):
    # Returns the scalar value type of this expression.
    # @return The type's enum from the NCBasicType enum definition.
    def GetValueType(self) -> int:
        return CSE.Expr_GetValueType(self.m_expr)

    # Evaluates the expression and returns the result as an NCValue object.
    # @return An NCValue object.
    def GetValue(self) -> NCValue:
        return NCValue(CSE.Expr_GetValue(self.m_expr))



# This class represents an l-value, i.e. a modifiable scalar NC object expressions. Instances of this class correspond to an NC variable
# (see class VariableManager).
class NCLValue(NCExpression):
    # Modifies the NC variable that is associated with this expression.
    # @param value An NCValue object.
    def SetValue(self, value : NCValue):
        if not isinstance(value, NCValue):
            raise CseTypeError
        return CSE.LValue_SetValue(self.m_expr, value.m_obj)



# This class represents array NC array expressions, i.e. their evaluation results in an instance of NCArray.
class NCArrayExpression(NCObjectExpression):
    # This method returns the NC type of this object.
    # @return The NCArrayType object.
    def GetType(self) -> NCArrayType:
        return NCArrayType(CSE.ArrayExpr_GetType(self.m_expr))

    # Evaluates the expression and returns the result as an NCArray object.
    # @return An NCArray object.
    def GetArray(self) -> NCArray:
        return NCArray(CSE.ArrayExpr_GetArray(self.m_expr))



# This class represents NC struct expressions, i.e. their evaluation results in an instance of NCStruct.
class NCStructExpression(NCObjectExpression):
    # This method returns the NC type of this object.
    # @return The NCStructType object.
    def GetType(self) -> NCStructType:
        return NCStructType(CSE.StructExpr_GetType(self.m_expr))

    # Evaluates the expression and returns the result as an NCStruct object.
    # @return An NCStruct object.
    def GetStruct(self) -> NCStruct:
        return NCStruct(CSE.StructExpr_GetStruct(self.m_expr))



################################################################################
# Factories
################################################################################

# Factory class to create instances of the NCValue class.
class NCValueFactory:
    # Used by wrapper code. Don't call directly.
    def __init__(self, factory):
        self.m_factory = factory

    # This method creates an NCValue instance representing a boolean value.
    # @param value A boolean value (False, False).
    # @return An NCValue object.
    def CreateBoolValue(self, value : bool) -> NCValue:
        return NCValue(CSE.ValueFactory_CreateBoolValue(self.m_factory, value))

    # This method creates an NCValue instance representing a character value.
    # @param value A single-byte character value (0-255).
    # @return An NCValue object.
    def CreateCharacterValue(self, value : int) -> NCValue:
        return NCValue(CSE.ValueFactory_CreateCharacterValue(self.m_factory, value))

    # This method creates an NCValue instance representing a signed integer value.
    # @param value A signed integer value.
    # @return An NCValue object.
    def CreateIntegerValue(self, value : int) -> NCValue:
        return NCValue(CSE.ValueFactory_CreateIntegerValue(self.m_factory, value))

    # This method creates an NCValue instance representing a single-precision floating point value.
    # @param value A double value that is representable as a 32-bit IEEE floating point number.
    # @return An NCValue object.
    def CreateRealValue(self, value : float) -> NCValue:
        return NCValue(CSE.ValueFactory_CreateRealValue(self.m_factory, value))

    # This method creates an NCValue instance representing a double-precision floating point value.
    # @param value A double value that is representable as a 64-bit IEEE floating point number.
    # @return An NCValue object.
    def CreateDoubleValue(self, value : float) -> NCValue:
        return NCValue(CSE.ValueFactory_CreateDoubleValue(self.m_factory, value))

    # This method creates an NCValue instance representing a string value.
    # @param value A string value.
    # @return An NCValue object.
    def CreateStringValue(self, value : str) -> NCValue:
        return NCValue(CSE.ValueFactory_CreateStringValue(self.m_factory, value))

    # This method creates an NCValue instance representing an object value.
    # @param value An object value.
    # @return An NCValue object.
    def CreateObjectValue(self, value) -> NCValue:
        return NCValue(CSE.ValueFactory_CreateObjectValue(self.m_factory, value))

    # This method creates an NCValue instance representing a vector value.
    # @param value A vector value.
    # @return An NCValue object.
    def CreateVectorValue(self, value : Vector3) -> NCValue:
        return NCValue(CSE.ValueFactory_CreateVectorValue(self.m_factory, value.vec))

    # This method creates an NCValue instance representing a matrix value.
    # @param value A matrix value.
    # @return An NCValue object.
    def CreateMatrixValue(self, value : Matrix4) -> NCValue:
        return NCValue(CSE.ValueFactory_CreateMatrixValue(self.m_factory, value.mat))

    # This method creates an NCValue instance representing a list.
    # @return An NCValue object.
    def CreateListValue(self, value : list) -> NCValue:
        return NCValue(CSE.ValueFactory_CreateListValue(self.m_factory, value))

    # This method creates an NCValue instance representing the given Python value
    # of arbitrary type.
    # @param value A Python value.
    # @return An NCObject instance.
    def CreateValue(self, value):
        if isinstance(value, bool):
            return NCValue(CSE.ValueFactory_CreateBoolValue(self.m_factory, value))
        elif isinstance(value, int):
            return NCValue(CSE.ValueFactory_CreateIntegerValue(self.m_factory, value))
        elif isinstance(value, float):
            return NCValue(CSE.ValueFactory_CreateDoubleValue(self.m_factory, value))
        elif isinstance(value, str):
            return NCValue(CSE.ValueFactory_CreateStringValue(self.m_factory, value))
        elif isinstance(value, Vector3):
            return NCValue(CSE.ValueFactory_CreateVectorValue(self.m_factory, value.vec))
        elif isinstance(value, Matrix4):
            return NCValue(CSE.ValueFactory_CreateMatrixValue(self.m_factory, value.mat))
        elif isinstance(value, list):
            return NCValue(CSE.ValueFactory_CreateListValue(self.m_factory, value))
        elif isinstance(value, NCCoordinate):
            return NCValue(CSE.ValueFactory_CreateObjectValue(self.m_factory, value.m_nccoord))
        elif isinstance(value, NCMotion):
            return NCValue(CSE.ValueFactory_CreateObjectValue(self.m_factory, value.m_ncmotion))

        # If it is none of the above values, it has to be an instance of an
        # NCObject derived class (NCValue/NCStruct/NCArray), so return as-is
        return value



# Factory class to create instances of the NCExpression class.
class NCExpressionFactory:
    # Unary operator enum definition to be used with CreateUnaryArithmeticExpr method. Don't modify!
    NEG_OP, SIN_OP, COS_OP, TAN_OP, ASIN_OP, ACOS_OP, ATAN_OP, EXP_OP, LN_OP, LOG_OP, ROUND_UP_OP, ROUND_DOWN_OP, ROUND_OP, ABS_OP, SGN_OP, SQRT_OP, NOT_OP, DEFINED_OP = range(18)

    # Binary operator enum definition to be used with CreateBinaryArithmeticExpr. Don't modify!
    ADD_OP, SUB_OP, MULT_OP, DIV_OP, MOD_OP, POW_OP, ATAN2_OP, AND_OP, OR_OP, XOR_OP, EQ_OP, NE_OP, GT_OP, GE_OP, LT_OP, LE_OP = range(16)

    # Used by wrapper code. Don't call directly.
    def __init__(self, factory):
        self.m_factory = factory

    # Creates a literal expression. A literal embodies a constant value, in this case an NCValue object.
    # @param value An NCValue object.
    # @return An NCExpression object.
    def CreateLiteral(self, value : NCValue) -> NCExpression:
        if not isinstance(value, NCValue):
            raise CseTypeError
        return NCExpression(CSE.ExprFactory_CreateLiteral(self.m_factory, value.m_obj))

    # Casts a given expression to a specified scalar type.
    # @param expr An NCExpression object.
    # @param enumValueType A scalar type specified as an enum value from the NCBasicType enum definition.
    # @return An NCExpression object.
    def CreateCastExpr(self, expr : NCExpression, enumValueType : int) -> NCExpression:
        if not isinstance(expr, NCExpression):
            raise CseTypeError
        return NCExpression(CSE.ExprFactory_CreateCastExpr(self.m_factory, expr.m_expr, enumValueType))

    # Creates a variable expression. It is associated with a scalar NC variable which is accessed when the
    # expression is evaluated.
    # @param strVarName A string that specifies the variable's name.
    # @return An NCLValue object.
    def CreateVariableExpr(self, strVarName : str) -> NCLValue:
        return NCLValue(CSE.ExprFactory_CreateVariableExpr(self.m_factory, strVarName))

    # Creates a variable expression in a given channel. It is associated with a scalar NC variable which is
    # accessed when the expression is evaluated.
    # @param strVarName A string that specifies the variable's name.
    # @param strChannelName A string that specifies a channel name.
    # @return An NCExpression object.
    def CreateRemoteVariableExpr(self, strVarName : str, strChannelName : str) -> NCExpression:
        return NCLValue(CSE.ExprFactory_CreateRemoteVariableExpr(self.m_factory, strVarName, strChannelName))

    # Creates a variable expression. It is associated with a scalar NC variable which is accessed when the
    # expression is evaluated. The variable name is specified as an expression itself, i.e. it is only
    # determined when the expression is evaluated.
    # @param exprVarName An NCExpression object that specifies the variable's name.
    # @return An NCExpression object.
    def CreateDynamicVariableExpr(self, exprVarName : NCExpression) -> NCExpression:
        if not isinstance(exprVarName, NCExpression):
            raise CseTypeError
        return NCLValue(CSE.ExprFactory_CreateDynamicVariableExpr(self.m_factory, exprVarName.m_expr))

    # Creates a variable expression in a given channel. It is associated with a scalar NC variable which is
    # accessed when the expression is evaluated. The variable name and the channel are specified as expressions
    # themselves, i.e. they are only determined when the expression is evaluated.
    # @param exprVarName An NCExpression object that specifies the variable's name.
    # @param exprChannelName An NCExpression object that specifies a channel name.
    # @return An NCExpression object.
    def CreateDynamicRemoteVariableExpr(self, exprVarName : NCExpression, strChannelName : str) -> NCExpression:
        if not isinstance(exprVarName, NCExpression):
            raise CseTypeError
        return NCLValue(CSE.ExprFactory_CreateDynamicRemoteVariableExpr(self.m_factory, exprVarName.m_expr, strChannelName))

    # Creates a string variable access expression. This evaluates a string variable at a given index.
    # @param exprStringVar An NCLValue object.
    # @param exprIndex An NCExpression object.
    # @return An NCLValue object.
    def CreateStringVarAccessExpr(self, exprStringVar : NCLValue, exprIndex : NCExpression) -> NCLValue:
        if not isinstance(exprStringVar, NCLValue) or not isinstance(exprIndex, NCExpression):
            raise CseTypeError
        return NCLValue(CSE.ExprFactory_CreateStringVarAccessExpr(self.m_factory, exprStringVar.m_expr, exprIndex.m_expr))

    # Creates an array access expression. This evaluates an array variable at a given index.
    # @param exprArray An NCArrayExpression object.
    # @param listIdx A list of NCExpression objects which specify the array indices.
    # @return An NCLValue object.
    def CreateArrayAccessExpr(self, exprArray : NCArrayExpression, listIdx : list) -> NCLValue:
        if not isinstance(exprArray, NCArrayExpression):
            raise CseTypeError
        listIdxNC = []
        for idx in listIdx:
            listIdxNC.append(idx.m_expr)
        return NCLValue(CSE.ExprFactory_CreateArrayAccessExpr(self.m_factory, exprArray.m_expr, listIdxNC))

    # Creates a struct access expression. This evaluates a struct variable at a given field.
    # @param exprStruct An NCStructExpression object.
    # @param strFieldName A string that specifies the struct field name.
    # @return An NCLValue object.
    def CreateStructAccessExpr(self, exprStruct : NCStructExpression, strFieldName : str) -> NCLValue:
        if not isinstance(exprStruct, NCStructExpression):
            raise CseTypeError
        return NCLValue(CSE.ExprFactory_CreateStructAccessExpr(self.m_factory, exprStruct.m_expr, strFieldName))

    # Creates a unary arithmetic expression. It applies an arithmetic operation to a given expression.
    # @param expr An NCExpression object.
    # @param enumOp An enum from the definitions at the beginning of this class that specifies the arithmetic operation.
    # @return An NCExpression object.
    def CreateUnaryArithmeticExpr(self, expr : NCExpression, enumOp : int) -> NCExpression:
        if not isinstance(expr, NCExpression):
            raise CseTypeError
        return NCExpression(CSE.ExprFactory_CreateUnaryArithmeticExpr(self.m_factory, expr.m_expr, enumOp))

    # Creates a binary arithmetic expression. It applies an arithmetic operation to two given expressions.
    # @param expr1 An NCExpression object.
    # @param expr2 An NCExpression object.
    # @param enumOp An enum from the definitions at the beginning of this class that specifies the arithmetic operation.
    # @return An NCExpression object.
    def CreateBinaryArithmeticExpr(self, expr1 : NCExpression, expr2 : NCExpression, enumOp : int) -> NCExpression:
        if not isinstance(expr1, NCExpression) or not isinstance(expr2, NCExpression):
            raise CseTypeError
        return NCExpression(CSE.ExprFactory_CreateBinaryArithmeticExpr(self.m_factory, expr1.m_expr, expr2.m_expr, enumOp))

    # Creates a conditional expression. It accepts three expressions. During evaluation, the result of the first
    # expression determines whether the second or the third expression is evaluated and its result is returned.
    # @param exprCondition An NCExpression object.
    # @param expr1 An NCExpression object.
    # @param expr2 An NCExpression object.
    # @return An NCExpression object.
    def CreateConditionalExpr(self, exprCondition : NCExpression, expr1 : NCExpression, expr2 : NCExpression) -> NCExpression:
        if not isinstance(exprCondition, NCExpression) or not isinstance(expr1, NCExpression) or not isinstance(expr2, NCExpression):
            raise CseTypeError
        return NCExpression(CSE.ExprFactory_CreateConditionalExpr(self.m_factory, exprCondition.m_expr, expr1.m_expr, expr2.m_expr))

    # Creates a method expression. During evaluation, a method is executed which receives a list of parameters.
    # The parameters are specified as expressions themselves and evaluated before the method is called. The method
    # can be implemented in the MCF/CCF, in CSE kernel or in Python where it is invoked through the
    # Controller.ExecuteMethod interface method. This offers a flexible mechanism to implement new operators.
    # @param strMethodName A string that specifies the method name.
    # @param listArgs A list of NCObjectExpression objects which specify the method parameters.
    # @return An NCExpression object.
    def CreateMethodExpr(self, strMethodName : str, listArgs : list = []) -> NCExpression:
        listArgsNC = []
        for arg in listArgs:
            listArgsNC.append(arg.m_expr)
        return NCExpression(CSE.ExprFactory_CreateMethodExpr(self.m_factory, strMethodName, listArgsNC))

    # Creates a dynamic cast expression. Used to convert from (abstract) object expressions to NCExpression instances.
    # @param exprObject An NCObjectExpression object.
    # @return An NCExpression object.
    def CreateDynamicCastExpr(self, exprObject : NCObjectExpression) -> NCExpression:
        return NCExpression(CSE.ExprFactory_CreateDynamicCastExpr(self.m_factory, exprObject.m_expr))

    # Creates an abstract variable expression. As opposed to the previous expression, it is associated with
    # an arbitrary object which is accessed when the expression is evaluated.
    # @param strVarName A string that specifies the variable's name.
    # @return An NCObjectExpression object.
    def CreateAbstractVariableExpr(self, strVarName : str) -> NCObjectExpression:
        return NCObjectExpression(CSE.ExprFactory_CreateAbstractVariableExpr(self.m_factory, strVarName))

    # Creates an abstract array access expression. This evaluates an array variable at a given index.
    # @param exprArray An NCArrayExpression object.
    # @param listIdx A list of NCExpression objects which specify the array indices.
    # @return An NCObjectExpression object.
    def CreateAbstractArrayAccessExpr(self, exprArray : NCArrayExpression, listIdx : list) -> NCObjectExpression:
        if not isinstance(exprArray, NCArrayExpression):
            raise CseTypeError
        listIdxNC = []
        for idx in listIdx:
            listIdxNC.append(idx.m_expr)
        return NCObjectExpression(CSE.ExprFactory_CreateAbstractArrayAccessExpr(self.m_factory, exprArray.m_expr, listIdxNC))

    # Creates an abstract struct access expression. This evaluates a struct variable at a given field.
    # @param exprStruct An NCStructExpression object.
    # @param strFieldName A string that specifies the struct field name.
    # @return An NCObjectExpression object.
    def CreateAbstractStructAccessExpr(self, exprStruct : NCStructExpression, strFieldName : str) -> NCObjectExpression:
        if not isinstance(exprStruct, NCStructExpression):
            raise CseTypeError
        return NCObjectExpression(CSE.ExprFactory_CreateAbstractStructAccessExpr(self.m_factory, exprStruct.m_expr, strFieldName))

    # Creates an abstract conditional expression. It accepts three expressions. During evaluation, the result of the first
    # expression determines whether the second or the third expression is evaluated and its result is returned.
    # @param exprCondition An NCExpression object.
    # @param expr1 An NCObjectExpression object.
    # @param expr2 An NCObjectExpression object.
    # @return An NCObjectExpression object.
    def CreateAbstractConditionalExpr(self, exprCondition : NCExpression, expr1 : NCObjectExpression, expr2 : NCObjectExpression) -> NCObjectExpression:
        if not isinstance(exprCondition, NCExpression) or not isinstance(expr1, NCObjectExpression) or not isinstance(expr2, NCObjectExpression):
            raise CseTypeError
        return NCObjectExpression(CSE.ExprFactory_CreateAbstractConditionalExpr(self.m_factory, exprCondition.m_expr, expr1.m_expr, expr2.m_expr))

    # Creates an abstract method expression. During evaluation, a method is executed which receives a list of parameters.
    # The parameters are specified as expressions themselves and evaluated before the method is called. The method
    # can be implemented in the MCF/CCF, in CSE kernel or in Python where it is invoked through the
    # Controller.ExecuteMethod interface method. This offers a flexible mechanism to implement new operators.
    # @param strMethodName A string that specifies the method name.
    # @param listArgs A list of NCObjectExpression objects which specify the method parameters.
    # @return An NCObjectExpression object.
    def CreateAbstractMethodExpr(self, strMethodName : str, listArgs : list = []) -> NCObjectExpression:
        listArgsNC = []
        for arg in listArgs:
            listArgsNC.append(arg.m_expr)
        return NCObjectExpression(CSE.ExprFactory_CreateAbstractMethodExpr(self.m_factory, strMethodName, listArgsNC))



# Factory class to create instances of the NCArrayExpression class.
class NCArrayExpressionFactory:
    # Used by wrapper code. Don't call directly.
    def __init__(self, factory):
        self.m_factory = factory

    # Creates a literal array expression. A literal embodies a constant value, in this case an NCArray object.
    # @param value An NCArray object.
    # @return An NCArrayExpression object.
    def CreateLiteral(self, value : NCArray) -> NCArrayExpression:
        if not isinstance(value, NCArray):
            raise CseTypeError
        return NCArrayExpression(CSE.ArrayExprFactory_CreateLiteral(self.m_factory, value.m_obj))

    # Creates a variable expression. It is associated with an NC array variable which is accessed when the
    # expression is evaluated.
    # @param strVarName A string that specifies the array variable's name.
    # @return An NCArrayExpression object.
    def CreateVariableExpr(self, strVarName : str) -> NCArrayExpression:
        return NCArrayExpression(CSE.ArrayExprFactory_CreateVariableExpr(self.m_factory, strVarName))

    # Creates an array access expression. This evaluates an array variable at a given index.
    # The evaluation results in an array itself.
    # @param exprArray An NCArrayExpression object.
    # @param listIdx A list of NCExpression objects which specify the array indices.
    # @return An NCArrayExpression object.
    def CreateArrayAccessExpr(self, exprArray : NCArrayExpression, listIdx : list) -> NCArrayExpression:
        if not isinstance(exprArray, NCArrayExpression):
            raise CseTypeError
        listIdxNC = []
        for idx in listIdx:
            listIdxNC.append(idx.m_expr)
        return NCArrayExpression(CSE.ArrayExprFactory_CreateArrayAccessExpr(self.m_factory, exprArray.m_expr, listIdxNC))

    # Creates a struct access expression. This evaluates a struct variable at a given field.
    # The evaluation results in a struct.
    # @param exprStruct An NCStructExpression object.
    # @param strFieldName A string that specifies the struct field name.
    # @return An NCArrayExpression object.
    def CreateStructAccessExpr(self, exprStruct : NCStructExpression, strFieldName : str) -> NCArrayExpression:
        if not isinstance(exprStruct, NCStructExpression):
            raise CseTypeError
        return NCArrayExpression(CSE.ArrayExprFactory_CreateStructAccessExpr(self.m_factory, exprStruct.m_expr, strFieldName))

    # Creates a method expression. During evaluation, a method is executed which receives a list of parameters.
    # The parameters are specified as expressions themselves and evaluated before the method is called. The method
    # can be implemented in the MCF/CCF, in CSE kernel or in Python where it is invoked through the
    # Controller.ExecuteMethod interface method. This offers a flexible mechanism to implement new operators.
    # @param strMethodName A string that specifies the method name.
    # @param listArgs A list of NCObjectExpression objects which specify the method parameters.
    # @return An NCArrayExpression object.
    def CreateMethodExpr(self, strMethodName : str, listArgs : list = []) -> NCArrayExpression:
        listArgsNC = []
        for arg in listArgs:
            listArgsNC.append(arg.m_expr)
        return NCArrayExpression(CSE.ArrayExprFactory_CreateMethodExpr(self.m_factory, strMethodName, listArgsNC))

    # Creates a dynamic cast expression. Used to convert from (abstract) object expressions to NCArrayExpression instances.
    # @param exprObject An NCObjectExpression object.
    # @return An NCArrayExpression object.
    def CreateDynamicCastExpr(self, exprObject : NCObjectExpression) -> NCArrayExpression:
        return NCArrayExpression(CSE.ArrayExprFactory_CreateDynamicCastExpr(self.m_factory, exprObject.m_expr))



# Factory class to create instances of the NCStructExpression class.
class NCStructExpressionFactory:
    # Used by wrapper code. Don't call directly.
    def __init__(self, factory):
        self.m_factory = factory

    # Creates a literal struct expression. A literal embodies a constant value, in this case an NCStruct object.
    # @param value An NCStruct object.
    # @return An NCStructExpression object.
    def CreateLiteral(self, value : NCStruct) -> NCStructExpression:
        if not isinstance(value, NCStruct):
            raise CseTypeError
        return NCStructExpression(CSE.StructExprFactory_CreateLiteral(self.m_factory, value.m_obj))

    # Creates a variable expression. It is associated with an NC struct variable which is accessed when the
    # expression is evaluated.
    # @param strVarName A string that specifies the struct variable's name.
    # @return An NCStructExpression object.
    def CreateVariableExpr(self, strVarName : str) -> NCStructExpression:
        return NCStructExpression(CSE.StructExprFactory_CreateVariableExpr(self.m_factory, strVarName))

    # Creates an array access expression. This evaluates an array variable at a given index.
    # The evaluation results in an array.
    # @param exprArray An NCArrayExpression object.
    # @param listIdx A list of NCExpression objects which specify the array indices.
    # @return An NCStructExpression object.
    def CreateArrayAccessExpr(self, exprArray : NCArrayExpression, listIdx : list) -> NCStructExpression:
        if not isinstance(exprArray, NCArrayExpression):
            raise CseTypeError
        listIdxNC = []
        for idx in listIdx:
            listIdxNC.append(idx.m_expr)
        return NCStructExpression(CSE.StructExprFactory_CreateArrayAccessExpr(self.m_factory, exprArray.m_expr, listIdxNC))

    # Creates a struct access expression. This evaluates a struct variable at a given field.
    # The evaluation results in a struct itself.
    # @param exprStruct An NCStructExpression object.
    # @param strFieldName A string that specifies the struct field name.
    # @return An NCStructExpression object.
    def CreateStructAccessExpr(self, exprStruct : NCStructExpression, strFieldName : str) -> NCStructExpression:
        if not isinstance(exprStruct, NCStructExpression):
            raise CseTypeError
        return NCStructExpression(CSE.StructExprFactory_CreateStructAccessExpr(self.m_factory, exprStruct.m_expr, strFieldName))

    # Creates a method expression. During evaluation, a method is executed which receives a list of parameters.
    # The parameters are specified as expressions themselves and evaluated before the method is called. The method
    # can be implemented in the MCF/CCF, in CSE kernel or in Python where it is invoked through the
    # Controller.ExecuteMethod interface method. This offers a flexible mechanism to implement new operators.
    # @param strMethodName A string that specifies the method name.
    # @param listArgs A list of NCObjectExpression objects which specify the method parameters.
    # @return An NCStructExpression object.
    def CreateMethodExpr(self, strMethodName : str, listArgs : list = []) -> NCStructExpression:
        listArgsNC = []
        for arg in listArgs:
            listArgsNC.append(arg.m_expr)
        return NCStructExpression(CSE.StructExprFactory_CreateMethodExpr(self.m_factory, strMethodName, listArgsNC))

    # Creates a dynamic cast expression. Used to convert from (abstract) object expressions to NCStructExpression instances.
    # @param exprObject An NCObjectExpression object.
    # @return An NCStructExpression object.
    def CreateDynamicCastExpr(self, exprObject : NCObjectExpression) -> NCStructExpression:
        return NCStructExpression(CSE.StructExprFactory_CreateDynamicCastExpr(self.m_factory, exprObject.m_expr))



# Class that stores and manages access to all variables that are associated with a channel of an NC machine.
class VariableManager:
    # Variable access mode enum definition. Don't modify!
    LOCAL_FIRST, GLOBAL_ONLY, MACHINE_GLOBAL_ONLY, DEFAULT_MODE = range(4)

    # Used by wrapper code. Don't call directly.
    def __init__(self, varmanager):
        self.m_varmanager = varmanager

    # Sets the variable access mode which defines the scope of every variable.
    # @param enumVarAccessMode An enum value from the definition at the beginning of this class which specifies
    # the desired variable access mode.
    def SetVarAccessMode(self, enumVarAccessMode : int):
        CSE.VarManager_SetVarAccessMode(self.m_varmanager, enumVarAccessMode)

    # AutoDeclare mode automatically creates a variable upon first access (bot read or write). This is a convenient
    # feature for NC controllers which don't explicitly declare variables (as e.g. Fanuc).
    # @param bActive A boolean flag that specifies the new state (True=On, False=Off).
    def ActivateAutoDeclare(self, bActive : bool):
        CSE.VarManager_ActivateAutoDeclare(self.m_varmanager, bActive)

    # MultiDeclare mode allows multiple declarations of the same variable. If it is active, any declaration
    # after the first one is ignored. If it is inactive, an error will be thrown if multiple declarations are
    # encountered.
    # @param bActive A boolean flag that specifies the new state (True=On, False=Off).
    def AllowMultiDeclare(self, bAllow : bool):
        CSE.VarManager_AllowMultiDeclare(self.m_varmanager, bAllow)

    # Creates a new variable in the given scope.
    # @param strVarName The variable's name.
    # @param enumVarAccessMode An enum value from the definition at the beginning of this class which specifies
    # the scope of this variable.
    # @param enumValueType The variable's scalar type specified as an enum value from the NCBasicType enum definition.
    # @param value An NCValue object that specifies the initial value of this variable.
    def RegisterVariable(self, strVarName : str, enumVarAccessMode : int, enumValueType : int, value : NCValue):
        if value == None:
            return CSE.VarManager_RegisterVariable(self.m_varmanager, strVarName, enumVarAccessMode, enumValueType, None)
        if not isinstance(value, NCValue):
            raise CseTypeError
        return CSE.VarManager_RegisterVariable(self.m_varmanager, strVarName, enumVarAccessMode, enumValueType, value.m_obj)

    # Returns a reference to the requested variable.
    # @param strVarName The variable's name.
    # @return An NCLValue object referencing the variable's value.
    def GetVariable(self, strVarName : str) -> NCLValue:
        return NCLValue(CSE.VarManager_GetVariable(self.m_varmanager, strVarName))

    # Check whether a variable is defined.
    # @param strVarName The variable's name.
    # @return True iff the variable exists.
    def DoesVariableExist(self, strVarName : str) -> bool:
        return CSE.VarManager_DoesVariableExist(self.m_varmanager, strVarName)

    # Queries the current value of an array variable.
    # @param strVarName The variable's name.
    # @return An NCArray object containing the variable's value.
    def GetArrayVariable(self, strVarName : str) -> NCArray:
        return NCArray(CSE.VarManager_GetArrayVariable(self.m_varmanager, strVarName))

    # Check whether an array variable is defined.
    # @param strVarName The variable's name.
    # @return True iff the variable exists.
    def DoesArrayVariableExist(self, strVarName : str) -> bool:
        return CSE.VarManager_DoesArrayVariableExist(self.m_varmanager, strVarName)

    # Queries the current value of a struct variable.
    # @param strVarName The variable's name.
    # @return An NCStruct object containing the variable's value.
    def GetStructVariable(self, strVarName : str) -> NCStruct:
        return NCStruct(CSE.VarManager_GetStructVariable(self.m_varmanager, strVarName))

    # Check whether a struct variable is defined.
    # @param strVarName The variable's name.
    # @return True iff the variable exists.
    def DoesStructVariableExist(self, strVarName : str) -> bool:
        return CSE.VarManager_DoesStructVariableExist(self.m_varmanager, strVarName)



# A type system stores type definitions and allows to create type and value objects.
class NCTypeSystem:
    # Used by wrapper code. Don't call directly.
    def __init__(self, sys):
        self.m_sys = sys

    # Convert the given value to a new value with the specified target type.
    # @param pValue An NCValue instance.
    # @param nTargetType The desired result type specified as an NCBasicType value type
    #                    (e.g. NCBasicType.INTEGER).
    # @return The converted NCValue object.
    # @throws CSE.KernelError
    def ForceConvert(self, pValue : NCValue, nTargetType : int) -> NCValue:
        return NCValue(CSE.TypeSystem_ForceConvert(self.m_sys, pValue.m_obj, nTargetType))

    # Create a scalar type object.
    # @param valType The scalar type specified as an enum value from the NCBasicType enum definition.
    # @return An NCBasicType object.
    def CreateBasicType(self, valType : int) -> NCBasicType:
        return NCBasicType(CSE.TypeSystem_CreateBasicType(self.m_sys, valType))

    # Define indexing logic for array objects.
    # @param bAllow True iff indices may be omitted when accessing array elements.
    def AllowPartialArrayIndexing(self, bAllow : bool):
        CSE.TypeSystem_AllowPartialArrayIndexing(self.m_sys, bAllow)

    # Create an array type object.
    # @param elType The scalar element type specified as an enum value from the NCBasicType enum definition.
    # @param listDims A list of integer values which define the size of each array dimension.
    # @param isSmart A boolean flag which specifies whether this is a smart array, i.e. whether it is
    # implemented as an associative array to save memory.
    # @param isComposed A boolean flag which specifies whether this is considered a composed type.
    # @return An NCArrayType object.
    def CreateArrayType(self, elType : NCType, listDims : list, isSmart : bool) -> NCArrayType:
        return NCArrayType(CSE.TypeSystem_CreateArrayType(self.m_sys, elType.m_nctype, listDims, isSmart))

    # Create a struct type object.
    # @param dictFiels A map containing the struct's field names and types.
    # @param isComposed A boolean flag which specifies whether this is considered a composed type.
    # @return An NCStructType object.
    def CreateStructType(self, dictFields : dict) -> NCStructType:
        dictFieldsNC = {}
        for strName, type in dictFields.items():
            dictFieldsNC[strName] = type.m_nctype
        return NCStructType(CSE.TypeSystem_CreateStructType(self.m_sys, dictFieldsNC))

    # Register a type under a given name for later retrieval.
    # @param strTypeName The type's name.
    # @param type An NCType object.
    def RegisterTypeDefinition(self, strTypeName : str, type : NCType):
        if not isinstance(type, NCType):
            raise CseTypeError
        CSE.TypeSystem_RegisterTypeDefinition(self.m_sys, strTypeName, type.m_nctype)

    # Access the that is registered under the given name.
    # @param strTypeName The type's name.
    # @return An NCType object.
    def GetTypeDefinition(self, strTypeName : str) -> NCType:
        return NCType(CSE.TypeSystem_GetTypeDefinition(self.m_sys, strTypeName)).GetDerivedInstance()

    # Get an instance of the type system's value factory.
    # @return An NCValueFactory object.
    def GetValueFactory(self) -> NCValueFactory:
        return NCValueFactory(CSE.TypeSystem_GetValueFactory(self.m_sys))



# An expression system provides access to expression factories and represents the environment of a
# machine channel, in particular it is associated with a channel's state and variable manager.
class NCExpressionSystem(NCTypeSystem):
    # Get an instance of the expression system's expression factory.
    # @return An NCExpressionFactory object.
    def GetExprFactory(self) -> NCExpressionFactory:
        return NCExpressionFactory(CSE.ExprSystem_GetExprFactory(self.m_sys))

    # Get an instance of the expression system's array expression factory.
    # @return An NCArrayExpressionFactory object.
    def GetArrayExprFactory(self) -> NCArrayExpressionFactory:
        return NCArrayExpressionFactory(CSE.ExprSystem_GetArrayExprFactory(self.m_sys))

    # Get an instance of the expression system's struct expression factory.
    # @return An NCStructExpressionFactory object.
    def GetStructExprFactory(self) -> NCStructExpressionFactory:
        return NCStructExpressionFactory(CSE.ExprSystem_GetStructExprFactory(self.m_sys))

    # Checks whether a method exists.
    # @param strMethodName The method's name.
    # @return True iff the given method exists.
    def HasMethod(self, strMethodName : str) -> bool:
        return CSE.ExprSystem_HasMethod(self.m_sys, strMethodName)

    # Get an instance of the expression system's variable manager.
    # @return A VariableManager object.
    def GetVarManager(self) -> VariableManager:
        return VariableManager(CSE.ExprSystem_GetVarManager(self.m_sys))

    # Get an instance of the expression system's channel state.
    # @return A ChannelState object.
    def GetChannelState(self):
        return ChannelState(CSE.ExprSystem_GetChannelState(self.m_sys))



# Class to represent an NC program. It has a unique ID and stores a list of lines.
class Program:
    # Used by wrapper code. Don't call directly.
    def __init__(self, prg):
        self.m_prg = prg

    # Get the program's ID.
    # @return The ID string.
    def GetPrgID(self) -> str:
        return CSE.Program_GetPrgID(self.m_prg)

    # Access a program line.
    # @param nLine The line index.
    # @return The line string.
    def GetLine(self, nLine : int) -> str:
        return CSE.Program_GetLine(self.m_prg, nLine)

    # Determine the number of lines in this program.
    # @return The line count.
    def GetLineCount(self) -> int:
        return CSE.Program_GetLineCount(self.m_prg)



# The program manager contains all programs required for simulation. There is only one instance per machine.
class ProgramManager:
    # Used by wrapper code. Don't call directly.
    def __init__(self, prgmgr):
        self.m_prgmgr = prgmgr

    # Get the program object for a given ID.
    # @param strPrgID A string specifying the program ID.
    # @return A Program object.
    def GetProgram(self, strPrgID : str) -> Program:
        return Program(CSE.ProgManager_GetProgram(self.m_prgmgr, strPrgID))

    # Get the program object that is current loaded in a specific call stack level of the given channel.
    # @param strChannel The channel name.
    # @param nCallStackLevel An integer value specifying the call stack level.
    # @return A Program object.
    def GetChannelProgram(self, strChannel : str, nCallStackLevel : int) -> Program:
        return Program(CSE.ProgManager_GetChannelProgram(self.m_prgmgr, strChannel, nCallStackLevel))

    # Get the current line index for the given channel and call stack level.
    # @param strChannel The channel name.
    # @param nCallStackLevel An integer value specifying the call stack level.
    # @return The line index (0-based).
    def GetCurrentLineIndex(self, strChannel : str, nCallStackLevel : int) -> int:
        return CSE.ProgManager_GetCurrentLineIndex(self.m_prgmgr, strChannel, nCallStackLevel)

    # Determines the size of the call stack for a given channel.
    # @param strChannel The channel name.
    # @return The current number of call stack levels.
    def GetCallStackDepth(self, strChannel : str) -> int:
        return CSE.ProgManager_GetCallStackDepth(self.m_prgmgr, strChannel)



# The state of an NC machine's channel. A channel can be compared to an operating system process.
# It is controlled by an NC program.
class ChannelState:
    # Used by wrapper code. Don't call directly.
    def __init__(self, state):
        self.m_state = state
        self.m_exprsys = CSE.ChannelState_GetExprSystem(state)
        self.m_factory = CSE.TypeSystem_GetValueFactory(self.m_exprsys)

    def CreateJoint(self,
                    strChannelJointName : str,
                    strJointName : str,
                    strType : str,
                    strGeoAxis : str,
                    nNumber : int,
                    dMinHard : float = None,
                    dMaxHard : float = None,
                    dMinSoft : float = None,
                    dMaxSoft : float = None,
                    dMaxVelocity : float = None,
                    dRefValue : float = None,
                    dJump : float = None,
                    dMaxAcc : float = None,
                    dMaxDec : float = None,
                    dJerkLimit : float = None,
                    dCoarsePrecision : float = None,
                    dFinePrecision : float = None,
                    dKv : float = None):
        listArgsNC = []
        listArgsNC.append(CSE.ValueFactory_CreateStringValue(self.m_factory, strChannelJointName))
        listArgsNC.append(CSE.ValueFactory_CreateStringValue(self.m_factory, strJointName))
        listArgsNC.append(CSE.ValueFactory_CreateStringValue(self.m_factory, strType))
        listArgsNC.append(CSE.ValueFactory_CreateStringValue(self.m_factory, strGeoAxis))
        listArgsNC.append(CSE.ValueFactory_CreateIntegerValue(self.m_factory, nNumber))
        if dMinHard != None:
            listArgsNC.append(CSE.ValueFactory_CreateDoubleValue(self.m_factory, dMinHard))
        if dMaxHard != None:
            listArgsNC.append(CSE.ValueFactory_CreateDoubleValue(self.m_factory, dMaxHard))
        if dMinSoft != None:
            listArgsNC.append(CSE.ValueFactory_CreateDoubleValue(self.m_factory, dMinSoft))
        if dMaxSoft != None:
            listArgsNC.append(CSE.ValueFactory_CreateDoubleValue(self.m_factory, dMaxSoft))
        if dMaxVelocity != None:
            listArgsNC.append(CSE.ValueFactory_CreateDoubleValue(self.m_factory, dMaxVelocity))
        if dRefValue != None:
            listArgsNC.append(CSE.ValueFactory_CreateDoubleValue(self.m_factory, dRefValue))
        if dJump != None:
            listArgsNC.append(CSE.ValueFactory_CreateDoubleValue(self.m_factory, dJump))
        if dMaxAcc != None:
            listArgsNC.append(CSE.ValueFactory_CreateDoubleValue(self.m_factory, dMaxAcc))
        if dMaxDec != None:
            listArgsNC.append(CSE.ValueFactory_CreateDoubleValue(self.m_factory, dMaxDec))
        if dJerkLimit != None:
            listArgsNC.append(CSE.ValueFactory_CreateDoubleValue(self.m_factory, dJerkLimit))
        if dCoarsePrecision != None:
            listArgsNC.append(CSE.ValueFactory_CreateDoubleValue(self.m_factory, dCoarsePrecision))
        if dFinePrecision != None:
            listArgsNC.append(CSE.ValueFactory_CreateDoubleValue(self.m_factory, dFinePrecision))
        if dKv != None:
            listArgsNC.append(CSE.ValueFactory_CreateDoubleValue(self.m_factory, dKv))
        CSE.ChannelState_ExecuteCommand(self.m_state, "CreateJoint", listArgsNC)

    def GetChannelName(self) -> str:
        return CSE.ChannelState_GetChannelName(self.m_state)

    def GetRefChannelName(self) -> str:
        retobj = CSE.ExprSystem_CallMethod(self.m_exprsys, "getRefChannelName", [])
        return CSE.Value_GetString(retobj)

    def GetControllerState(self):
        return CSE.ChannelState_GetControllerState(self.m_state)

    def Assert(self, bCondition : bool, strSeverity : str, strErrorMessage : str):
        listArgsNC = []
        listArgsNC.append(CSE.ValueFactory_CreateBoolValue(self.m_factory, bCondition))
        listArgsNC.append(CSE.ValueFactory_CreateStringValue(self.m_factory, strSeverity))
        listArgsNC.append(CSE.ValueFactory_CreateStringValue(self.m_factory, strErrorMessage))
        CSE.ChannelState_ExecuteCommand(self.m_state, "Assert", listArgsNC)

    def CheckCredentials(self, strClass : str, strValue : str) -> bool:
        listArgsNC = []
        listArgsNC.append(CSE.ValueFactory_CreateStringValue(self.m_factory, strClass))
        listArgsNC.append(CSE.ValueFactory_CreateStringValue(self.m_factory, strValue))
        retobj = CSE.ExprSystem_CallMethod(self.m_exprsys, "checkCredentials", listArgsNC)
        return CSE.Value_GetBool(retobj)

    def GetCurrentTime(self) -> float:
        retobj = CSE.ExprSystem_CallMethod(self.m_exprsys, "getCurrentTime", [])
        return CSE.Value_GetDouble(retobj)

    def GetProgramManager(self) -> ProgramManager:
        return ProgramManager(CSE.ChannelState_GetProgramManager(self.m_state))

    def GetExprSystem(self) -> NCExpressionSystem:
        return NCExpressionSystem(CSE.ChannelState_GetExprSystem(self.m_state))

    def SetVariable(self, strVarName : str, obj):
        valueFactory = NCValueFactory(self.m_factory)
        listArgsNC = []
        listArgsNC.append(CSE.ValueFactory_CreateStringValue(self.m_factory, strVarName))
        listArgsNC.append(valueFactory.CreateValue(obj).m_obj)
        CSE.ChannelState_ExecuteCommand(self.m_state, "SetVariable", listArgsNC)

    def GetVariable(self, strVarName : str, strChannelName : str = None):
        listArgsNC = []
        listArgsNC.append(CSE.ValueFactory_CreateStringValue(self.m_factory, strVarName))
        if strChannelName != None:
            listArgsNC.append(CSE.ValueFactory_CreateStringValue(self.m_factory, strChannelName))
        retobj = CSE.ExprSystem_CallMethod(self.m_exprsys, "getVariable", listArgsNC)
        return NCObject.GetNativeObject(retobj)

    def SetArrayElement(self, array, indices : list, obj):
        valueFactory = NCValueFactory(self.m_factory)
        listArgsNC = []
        listArgsNC.append(valueFactory.CreateValue(array).m_obj)
        for index in indices:
            listArgsNC.append(CSE.ValueFactory_CreateIntegerValue(self.m_factory, index))
        listArgsNC.append(valueFactory.CreateValue(obj).m_obj)
        CSE.ChannelState_ExecuteCommand(self.m_state, "SetArrayElement", listArgsNC)

    def GetArrayElement(self, array, indices : list):
        valueFactory = NCValueFactory(self.m_factory)
        listArgsNC = []
        listArgsNC.append(valueFactory.CreateValue(array).m_obj)
        for index in indices:
            listArgsNC.append(CSE.ValueFactory_CreateIntegerValue(self.m_factory, index))
        retobj = CSE.ExprSystem_CallMethod(self.m_exprsys, "getArrayElement", listArgsNC)
        return NCObject.GetNativeObject(retobj)

    def SetStructField(self, struct, strField : str, obj):
        valueFactory = NCValueFactory(self.m_factory)
        listArgsNC = []
        listArgsNC.append(valueFactory.CreateValue(struct).m_obj)
        listArgsNC.append(CSE.ValueFactory_CreateStringValue(self.m_factory, strField))
        listArgsNC.append(valueFactory.CreateValue(obj).m_obj)
        CSE.ChannelState_ExecuteCommand(self.m_state, "SetStructField", listArgsNC)

    def GetStructField(self, struct, strField : str):
        valueFactory = NCValueFactory(self.m_factory)
        listArgsNC = []
        listArgsNC.append(valueFactory.CreateValue(struct).m_obj)
        listArgsNC.append(CSE.ValueFactory_CreateStringValue(self.m_factory, strField))
        retobj = CSE.ExprSystem_CallMethod(self.m_exprsys, "getStructField", listArgsNC)
        return NCObject.GetNativeObject(retobj)

    def SetStateAttribute(self, strAttrName : str, obj):
        valueFactory = NCValueFactory(self.m_factory)
        CSE.ChannelState_SetStateAttribute(self.m_state, strAttrName, valueFactory.CreateValue(obj).m_obj)

    def GetStateAttribute(self, strAttrName : str):
        return NCObject.GetNativeObject(CSE.ChannelState_GetStateAttribute(self.m_state, strAttrName))

    def GetPath(self, strPathType : str) -> str:
        listArgsNC = []
        listArgsNC.append(CSE.ValueFactory_CreateStringValue(self.m_factory, strPathType))
        retobj = CSE.ExprSystem_CallMethod(self.m_exprsys, "getPath", listArgsNC)
        return CSE.Value_GetString(retobj)

    def DoesProgramExist(self, strPrgID : str) -> bool:
        listArgsNC = []
        listArgsNC.append(CSE.ValueFactory_CreateStringValue(self.m_factory, strPrgID))
        retobj = CSE.ExprSystem_CallMethod(self.m_exprsys, "doesProgramExist", listArgsNC)
        return CSE.Value_GetBool(retobj)

    def GetStackSize(self) -> int:
        retobj = CSE.ExprSystem_CallMethod(self.m_exprsys, "getStackSize", [])
        return CSE.Value_GetInteger(retobj)

    def CallSubprog(self, strSubprogName : str, bInitial : bool):
        listArgsNC = []
        listArgsNC.append(CSE.ValueFactory_CreateStringValue(self.m_factory, strSubprogName))
        if bInitial != None:
            listArgsNC.append(CSE.ValueFactory_CreateBoolValue(self.m_factory, bInitial))
        CSE.ChannelState_ExecuteCommand(self.m_state, "CallSubProg", listArgsNC)

    def CallRemoteSubprog(self, strChannelName : str, strSubprogName : str):
        listArgsNC = []
        listArgsNC.append(CSE.ValueFactory_CreateStringValue(self.m_factory, strChannelName))
        listArgsNC.append(CSE.ValueFactory_CreateStringValue(self.m_factory, strSubprogName))
        CSE.ChannelState_ExecuteCommand(self.m_state, "CallRemoteSubProg", listArgsNC)

    def SetEndSubprog(self, bInitial : bool = None):
        listArgsNC = []
        if bInitial != None:
            listArgsNC.append(CSE.ValueFactory_CreateBoolValue(self.m_factory, bInitial))
        CSE.ChannelState_ExecuteCommand(self.m_state, "SetEndSubProg", listArgsNC)

    def CallRepeatSubprog(self, strStartLabel : str, strEndLabel : str, strDirection : str, strProgramName : str):
        listArgsNC = []
        listArgsNC.append(CSE.ValueFactory_CreateStringValue(self.m_factory, strStartLabel))
        listArgsNC.append(CSE.ValueFactory_CreateStringValue(self.m_factory, strEndLabel))
        if strDirection != None:
            listArgsNC.append(CSE.ValueFactory_CreateStringValue(self.m_factory, strDirection))
        if strProgramName != None:
            listArgsNC.append(CSE.ValueFactory_CreateStringValue(self.m_factory, strProgramName))
        CSE.ChannelState_ExecuteCommand(self.m_state, "CallRepeatSubProg", listArgsNC)

    def SetEndRepeatSubprog(self, strCurrentLabel : str, bInitial : bool = None):
        listArgsNC = []
        listArgsNC.append(CSE.ValueFactory_CreateStringValue(self.m_factory, strCurrentLabel))
        if bInitial != None:
            listArgsNC.append(CSE.ValueFactory_CreateBoolValue(self.m_factory, bInitial))
        CSE.ChannelState_ExecuteCommand(self.m_state, "SetEndRepeatSubProg", listArgsNC)

    def AddSubprogParameter(self, value, bInitial : bool = None):
        valueFactory = NCValueFactory(self.m_factory)
        listArgsNC = []
        listArgsNC.append(valueFactory.CreateValue(value).m_obj)
        if bInitial != None:
            listArgsNC.append(CSE.ValueFactory_CreateBoolValue(self.m_factory, bInitial))
        CSE.ChannelState_ExecuteCommand(self.m_state, "AddSubProgParameter", listArgsNC)

    def InitSubprogParameter(self, value, strParamName : str, nStackIndex : int):
        listArgsNC = []
        listArgsNC.append(CSE.ValueFactory_CreateStringValue(self.m_factory, strParamName))
        listArgsNC.append(CSE.ValueFactory_CreateIntegerValue(self.m_factory, nStackIndex))
        CSE.ChannelState_ExecuteCommand(self.m_state, "InitSubProgParameter", listArgsNC)

    def DoesSubprogParameterExist(self, nParamIndex : int) -> bool:
        listArgsNC = []
        listArgsNC.append(CSE.ValueFactory_CreateIntegerValue(self.m_factory, nParamIndex))
        retobj = CSE.ExprSystem_CallMethod(self.m_exprsys, "doesSubProgParameterExist", listArgsNC)
        return CSE.Value_GetBool(retobj)

    def HasSubprogDeclaration(strSubProgName : str) -> bool:
        listArgsNC = []
        listArgsNC.append(CSE.ValueFactory_CreateStringValue(self.m_factory, strSubProgName))
        retobj = CSE.ExprSystem_CallMethod(self.m_exprsys, "hasSubProgDeclaration", listArgsNC)
        return CSE.Value_GetBool(retobj)

    def ResetSubprogDeclaration(self, strSubprogName : str):
        listArgsNC = []
        listArgsNC.append(CSE.ValueFactory_CreateStringValue(self.m_factory, strSubprogName))
        CSE.ChannelState_ExecuteCommand(self.m_state, "ResetSubProgDeclaration", listArgsNC)

    def AddSubprogParameterDeclaration(self, strSubprogName : str, strMode : str):
        listArgsNC = []
        listArgsNC.append(CSE.ValueFactory_CreateStringValue(self.m_factory, strSubprogName))
        listArgsNC.append(CSE.ValueFactory_CreateStringValue(self.m_factory, strMode))
        CSE.ChannelState_ExecuteCommand(self.m_state, "AddSubProgParameterDeclaration", listArgsNC)

    def GetSubprogParameterMode(strSubProgName : str, nParamIndex : int) ->str:
        listArgsNC = []
        listArgsNC.append(CSE.ValueFactory_CreateStringValue(self.m_factory, strSubProgName))
        listArgsNC.append(CSE.ValueFactory_CreateIntegerValue(self.m_factory, nParamIndex))
        retobj = CSE.ExprSystem_CallMethod(self.m_exprsys, "getSubProgParameterMode", listArgsNC)
        return CSE.Value_GetString(retobj)

    def ResetModalSubprog(self):
        CSE.ChannelState_ExecuteCommand(self.m_state, "ResetModalSubProg", [])

    def SetModalSubprog(self, strSubprogName : str):
        listArgsNC = []
        listArgsNC.append(CSE.ValueFactory_CreateStringValue(self.m_factory, strSubprogName))
        CSE.ChannelState_ExecuteCommand(self.m_state, "SetModalSubProg", listArgsNC)

    def GetModalSubprog(self) -> str:
        retobj = CSE.ExprSystem_CallMethod(self.m_exprsys, "getModalSubProg", [])
        return CSE.Value_GetString(retobj)

    def HasModalSubprog(self) -> bool:
        retobj = CSE.ExprSystem_CallMethod(self.m_exprsys, "hasModalSubProg", [])
        return CSE.Value_GetBool(retobj)

    def AddModalSubprogParameter(self, value):
        valueFactory = NCValueFactory(self.m_factory)
        listArgsNC = []
        listArgsNC.append(valueFactory.CreateValue(value).m_obj)
        CSE.ChannelState_ExecuteCommand(self.m_state, "AddModalSubProgParameter", listArgsNC)

    def ResetGlobalModalSubprog(self):
        CSE.ChannelState_ExecuteCommand(self.m_state, "ResetGlobalModalSubProg", [])

    def SetGlobalModalSubprog(self, strSubprogName : str):
        listArgsNC = []
        listArgsNC.append(CSE.ValueFactory_CreateStringValue(self.m_factory, strSubprogName))
        CSE.ChannelState_ExecuteCommand(self.m_state, "SetGlobalModalSubProg", listArgsNC)

    def GetGlobalModalSubprog(self) -> str:
        retobj = CSE.ExprSystem_CallMethod(self.m_exprsys, "getGlobalModalSubProg", [])
        return CSE.Value_GetString(retobj)

    def HasGlobalModalSubprog(self) -> bool:
        retobj = CSE.ExprSystem_CallMethod(self.m_exprsys, "hasGlobalModalSubProg", [])
        return CSE.Value_GetBool(retobj)

    def AddGlobalModalSubprogParameter(self, value):
        valueFactory = NCValueFactory(self.m_factory)
        listArgsNC = []
        listArgsNC.append(valueFactory.CreateValue(value).m_obj)
        CSE.ChannelState_ExecuteCommand(self.m_state, "AddGlobalModalSubProgParameter", listArgsNC)

    def SetFirstGeoAxisName(self, strJointName : str):
        listArgsNC = []
        listArgsNC.append(CSE.ValueFactory_CreateStringValue(self.m_factory, strJointName))
        CSE.ChannelState_ExecuteCommand(self.m_state, "SetFirstGeoAxis", listArgsNC)

    def GetFirstGeoAxisName(self) -> str:
        retobj = CSE.ExprSystem_CallMethod(self.m_exprsys, "getFirstGeoAxis", [])
        return CSE.Value_GetString(retobj)

    def SetSecondGeoAxisName(self, strJointName : str):
        listArgsNC = []
        listArgsNC.append(CSE.ValueFactory_CreateStringValue(self.m_factory, strJointName))
        CSE.ChannelState_ExecuteCommand(self.m_state, "SetSecondGeoAxis", listArgsNC)

    def GetSecondGeoAxisName(self) -> str:
        retobj = CSE.ExprSystem_CallMethod(self.m_exprsys, "getSecondGeoAxis", [])
        return CSE.Value_GetString(retobj)

    def SetThirdGeoAxisName(self, strJointName : str):
        listArgsNC = []
        listArgsNC.append(CSE.ValueFactory_CreateStringValue(self.m_factory, strJointName))
        CSE.ChannelState_ExecuteCommand(self.m_state, "SetThirdGeoAxis", listArgsNC)

    def GetThirdGeoAxisName(self) -> str:
        retobj = CSE.ExprSystem_CallMethod(self.m_exprsys, "getThirdGeoAxis", [])
        return CSE.Value_GetString(retobj)

    def SetWorkingPlane(self, strWorkingPlane : str):
        listArgsNC = []
        listArgsNC.append(CSE.ValueFactory_CreateStringValue(self.m_factory, strWorkingPlane))
        CSE.ChannelState_ExecuteCommand(self.m_state, "SetWorkingPlane", listArgsNC)

    def SetFirstAxisName(self, strJointName : str):
        listArgsNC = []
        listArgsNC.append(CSE.ValueFactory_CreateStringValue(self.m_factory, strJointName))
        CSE.ChannelState_ExecuteCommand(self.m_state, "SetFirstAxis", listArgsNC)

    def GetFirstAxisName(self) -> str:
        retobj = CSE.ExprSystem_CallMethod(self.m_exprsys, "getFirstAxis", [])
        return CSE.Value_GetString(retobj)

    def SetSecondAxisName(self, strJointName : str):
        listArgsNC = []
        listArgsNC.append(CSE.ValueFactory_CreateStringValue(self.m_factory, strJointName))
        CSE.ChannelState_ExecuteCommand(self.m_state, "SetSecondAxis", listArgsNC)

    def GetSecondAxisName(self) -> str:
        retobj = CSE.ExprSystem_CallMethod(self.m_exprsys, "getSecondAxis", [])
        return CSE.Value_GetString(retobj)

    def SetThirdAxisName(self, strJointName : str):
        listArgsNC = []
        listArgsNC.append(CSE.ValueFactory_CreateStringValue(self.m_factory, strJointName))
        CSE.ChannelState_ExecuteCommand(self.m_state, "SetThirdAxis", listArgsNC)

    def GetThirdAxisName(self) -> str:
        retobj = CSE.ExprSystem_CallMethod(self.m_exprsys, "getThirdAxis", [])
        return CSE.Value_GetString(retobj)

    def SetMainSpindle(self, strSpindleName : str):
        listArgsNC = []
        listArgsNC.append(CSE.ValueFactory_CreateStringValue(self.m_factory, strSpindleName))
        CSE.ChannelState_ExecuteCommand(self.m_state, "SetMainSpindle", listArgsNC)

    def GetMainSpindle(self) -> str:
        retobj = CSE.ExprSystem_CallMethod(self.m_exprsys, "getMainSpindle", [])
        return CSE.Value_GetString(retobj)

    def SetFeed(self, dValue : float, bModal : bool = None):
        listArgsNC = []
        listArgsNC.append(CSE.ValueFactory_CreateDoubleValue(self.m_factory, dValue))
        if bModal != None:
            listArgsNC.append(CSE.ValueFactory_CreateBoolValue(self.m_factory, bModal))
        CSE.ChannelState_ExecuteCommand(self.m_state, "SetFeed", listArgsNC)

    def GetFeed(self) -> float:
        retobj = CSE.ExprSystem_CallMethod(self.m_exprsys, "getFeed", [])
        return CSE.Value_GetDouble(retobj)

    def SetFeedUnit(self, strUnit : str, bModal : bool = None):
        listArgsNC = []
        listArgsNC.append(CSE.ValueFactory_CreateStringValue(self.m_factory, strUnit))
        if bModal != None:
            listArgsNC.append(CSE.ValueFactory_CreateBoolValue(self.m_factory, bModal))
        CSE.ChannelState_ExecuteCommand(self.m_state, "SetFeedUnit", listArgsNC)

    def GetFeedUnit(self) -> str:
        retobj = CSE.ExprSystem_CallMethod(self.m_exprsys, "getFeedUnit", [])
        return CSE.Value_GetString(retobj)

    def SetAsyncJointFeed(self, strJointName : str, dValue : float, bModal : bool = None):
        listArgsNC = []
        listArgsNC.append(CSE.ValueFactory_CreateStringValue(self.m_factory, strJointName))
        listArgsNC.append(CSE.ValueFactory_CreateDoubleValue(self.m_factory, dValue))
        if bModal != None:
            listArgsNC.append(CSE.ValueFactory_CreateBoolValue(self.m_factory, bModal))
        CSE.ChannelState_ExecuteCommand(self.m_state, "SetAsyncJointFeed", listArgsNC)

    def GetAsyncJointFeed(self, strJointName : str) -> float:
        listArgsNC = []
        listArgsNC.append(CSE.ValueFactory_CreateStringValue(self.m_factory, strJointName))
        retobj = CSE.ExprSystem_CallMethod(self.m_exprsys, "getAsyncJointFeed", listArgsNC)
        return CSE.Value_GetDouble(retobj)

    def SetFeedCorrectionMode(self, strMode : str):
        listArgsNC = []
        listArgsNC.append(CSE.ValueFactory_CreateStringValue(self.m_factory, strMode))
        CSE.ChannelState_ExecuteCommand(self.m_state, "SetFeedCorrectionMode", listArgsNC)

    def GetFeedCorrectionMode(self) -> str:
        retobj = CSE.ExprSystem_CallMethod(self.m_exprsys, "getFeedCorrectionMode", [])
        return CSE.Value_GetString(retobj)

    def SetFeedGroup(self, strType : str, jointList : list):
        listArgsNC = []
        listArgsNC.append(CSE.ValueFactory_CreateStringValue(self.m_factory, strType))
        if jointList != None:
            valueList = []
            for joint in jointList:
                valueList.append(CSE.ValueFactory_CreateStringValue(self.m_factory, joint))
            listArgsNC.append(CSE.ValueFactory_CreateListValue(self.m_factory, valueList))
        CSE.ChannelState_ExecuteCommand(self.m_state, "SetFeedGroup", listArgsNC)

    def GetFeedGroup(self) -> list:
        retobj = CSE.ExprSystem_CallMethod(self.m_exprsys, "getFeedGroup", [])
        jointList = []
        valueList = CSE.Value_GetList(retobj)
        for jointName in valueList:
            jointList.append(CSE.Value_GetString(jointName))
        return jointList

    def SetMotionType(self, strType : str):
        listArgsNC = []
        listArgsNC.append(CSE.ValueFactory_CreateStringValue(self.m_factory, strType))
        CSE.ChannelState_ExecuteCommand(self.m_state, "SetMotionType", listArgsNC)

    def GetMotionType(self) -> str:
        retobj = CSE.ExprSystem_CallMethod(self.m_exprsys, "getMotionType", [])
        return CSE.Value_GetString(retobj)

    def SetMotionProfile(self, strMethodName : str):
        listArgsNC = []
        listArgsNC.append(CSE.ValueFactory_CreateStringValue(self.m_factory, strMethodName))
        CSE.ChannelState_ExecuteCommand(self.m_state, "SetMotionProfile", listArgsNC)

    def GetMotionProfile(self) -> str:
        retobj = CSE.ExprSystem_CallMethod(self.m_exprsys, "getMotionProfile", [])
        return CSE.Value_GetString(retobj)

    def SetDefaultMotionProfileType(self, strProfileType : str):
        listArgsNC = []
        listArgsNC.append(CSE.ValueFactory_CreateStringValue(self.m_factory, strProfileType))
        CSE.ChannelState_ExecuteCommand(self.m_state, "SetDefaultMotionProfileType", listArgsNC)

    def GetDefaultMotionProfileType(self) -> str:
        retobj = CSE.ExprSystem_CallMethod(self.m_exprsys, "getDefaultMotionProfileType", [])
        return CSE.Value_GetString(retobj)

    def SetPositioningMode(self, strMode : str):
        listArgsNC = []
        listArgsNC.append(CSE.ValueFactory_CreateStringValue(self.m_factory, strMode))
        CSE.ChannelState_ExecuteCommand(self.m_state, "SetPositioningMode", listArgsNC)

    def GetPositioningMode(self) -> str:
        retobj = CSE.ExprSystem_CallMethod(self.m_exprsys, "getPositioningMode", [])
        return CSE.Value_GetString(retobj)

    def SetIJKPositioningMode(self, strMode : str):
        listArgsNC = []
        listArgsNC.append(CSE.ValueFactory_CreateStringValue(self.m_factory, strMode))
        CSE.ChannelState_ExecuteCommand(self.m_state, "SetIJKPositioningMode", listArgsNC)

    def GetIJKPositioningMode(self) -> str:
        retobj = CSE.ExprSystem_CallMethod(self.m_exprsys, "getIJKPositioningMode", [])
        return CSE.Value_GetString(retobj)

    def SetFullCircleMode(self, bActive : bool):
        CSE.ChannelState_SetFullCircleMode(self.m_state, bActive)

    def SetCircleParameter(self, strParam : str, dValue : float, strPositioning : str = None):
        listArgsNC = []
        listArgsNC.append(CSE.ValueFactory_CreateStringValue(self.m_factory, strParam))
        listArgsNC.append(CSE.ValueFactory_CreateDoubleValue(self.m_factory, dValue))
        if strPositioning != None:
            listArgsNC.append(CSE.ValueFactory_CreateStringValue(self.m_factory, strPositioning))
        CSE.ChannelState_ExecuteCommand(self.m_state, "SetCircleParameter", listArgsNC)

    def GetCircleParameter(self, strParameterName : str):
        listArgsNC = []
        listArgsNC.append(CSE.ValueFactory_CreateStringValue(self.m_factory, strParameterName))
        retobj = CSE.ExprSystem_CallMethod(self.m_exprsys, "getCircleParameter", listArgsNC)
        strParameterName = strParameterName.lower()
        if strParameterName == "fullcircles":
            return CSE.Value_GetInteger(retobj)
        else:
            return CSE.Value_GetDouble(retobj)

    def SetPolarCoordinateMode(self, bActive : bool):
        listArgsNC = []
        listArgsNC.append(CSE.ValueFactory_CreateBoolValue(self.m_factory, bActive))
        CSE.ChannelState_ExecuteCommand(self.m_state, "SetPolarCoordinateMode", listArgsNC)

    def IsPolarCoordinateModeActive(self) -> bool:
        retobj = CSE.ExprSystem_CallMethod(self.m_exprsys, "isPolarCoordinateModeActive", [])
        return CSE.Value_GetBool(retobj)

    def SetPolarCoordinateParameter(self, strParam : str, dValue : float, strPositioning : str = None):
        listArgsNC = []
        listArgsNC.append(CSE.ValueFactory_CreateStringValue(self.m_factory, strParam))
        listArgsNC.append(CSE.ValueFactory_CreateDoubleValue(self.m_factory, dValue))
        if strPositioning != None:
            listArgsNC.append(CSE.ValueFactory_CreateStringValue(self.m_factory, strPositioning))
        CSE.ChannelState_ExecuteCommand(self.m_state, "SetPolarCoordinateParameter", listArgsNC)

    def GetPolarCoordinateParameter(self, strParam : str) -> float:
        listArgsNC = []
        listArgsNC.append(CSE.ValueFactory_CreateStringValue(self.m_factory, strParam))
        retobj = CSE.ExprSystem_CallMethod(self.m_exprsys, "getPolarCoordinateParameter", listArgsNC)
        return CSE.Value_GetDouble(retobj)

    def SetLinearFlyBy(self, bFlyBy : bool, bModal : bool = None):
        listArgsNC = []
        listArgsNC.append(CSE.ValueFactory_CreateBoolValue(self.m_factory, bFlyBy))
        if bModal != None:
            listArgsNC.append(CSE.ValueFactory_CreateBoolValue(self.m_factory, bModal))
        CSE.ChannelState_ExecuteCommand(self.m_state, "SetLinearFlyBy", listArgsNC)

    def IsLinearFlyByActive(self) -> bool:
        retobj = CSE.ExprSystem_CallMethod(self.m_exprsys, "isLinearFlyByActive", [])
        return CSE.Value_GetBool(retobj)

    def SetRapidFlyBy(self, bFlyBy : bool, bModal : bool = None):
        listArgsNC = []
        listArgsNC.append(CSE.ValueFactory_CreateBoolValue(self.m_factory, bFlyBy))
        if bModal != None:
            listArgsNC.append(CSE.ValueFactory_CreateBoolValue(self.m_factory, bModal))
        CSE.ChannelState_ExecuteCommand(self.m_state, "SetRapidFlyBy", listArgsNC)

    def IsRapidFlyByActive(self) -> bool:
        retobj = CSE.ExprSystem_CallMethod(self.m_exprsys, "isRapidFlyByActive", [])
        return CSE.Value_GetBool(retobj)

    def SetLookaheadLineCount(self, nCount : int):
        listArgsNC = []
        listArgsNC.append(CSE.ValueFactory_CreateIntegerValue(self.m_factory, nCount))
        CSE.ChannelState_ExecuteCommand(self.m_state, "SetLookaheadLineCount", listArgsNC)

    def GetLookaheadLineCount(self) -> int:
        retobj = CSE.ExprSystem_CallMethod(self.m_exprsys, "getLookaheadLineCount", [])
        return CSE.Value_GetInteger(retobj)

    def SetLookaheadMotionCount(self, nCount : int):
        listArgsNC = []
        listArgsNC.append(CSE.ValueFactory_CreateIntegerValue(self.m_factory, nCount))
        CSE.ChannelState_ExecuteCommand(self.m_state, "SetLookaheadMotionCount", listArgsNC)

    def GetLookaheadMotionCount(self) -> int:
        retobj = CSE.ExprSystem_CallMethod(self.m_exprsys, "getLookaheadMotionCount", [])
        return CSE.Value_GetInteger(retobj)

    def GetMotionPrecision(self) -> float:
        return CSE.ChannelState_GetMotionPrecision(self.m_state)

    def GetMotionBuffer(self) -> list:
        retobj = CSE.ExprSystem_CallMethod(self.m_exprsys, "getMotionBuffer", [])
        motionList = []
        valueList = CSE.Value_GetList(retobj)
        for motion in valueList:
            motionList.append(NCMotion(CSE.Value_GetObject(motion)))
        return motionList

    def SetMotionBuffering(self, bActive : bool):
        listArgsNC = []
        listArgsNC.append(CSE.ValueFactory_CreateBoolValue(self.m_factory, bActive))
        CSE.ChannelState_ExecuteCommand(self.m_state, "SetMotionBuffering", listArgsNC)

    def IsMotionBufferingActive(self) -> bool:
        retobj = CSE.ExprSystem_CallMethod(self.m_exprsys, "isMotionBufferingActive", [])
        return CSE.Value_GetBool(retobj)

    def AddMotionTask(self, strType : str):
        listArgsNC = []
        listArgsNC.append(CSE.ValueFactory_CreateStringValue(self.m_factory, strType))
        CSE.ChannelState_ExecuteCommand(self.m_state, "NewCoordinate", listArgsNC)

    def AddDelayTask(self, dTime : float):
        listArgsNC = []
        listArgsNC.append(CSE.ValueFactory_CreateDoubleValue(self.m_factory, dTime))
        CSE.ChannelState_ExecuteCommand(self.m_state, "AddDelayTask", listArgsNC)

    def AddWaitTask(self, strMethodName : str, bInitial : bool):
        listArgsNC = []
        listArgsNC.append(CSE.ValueFactory_CreateStringValue(self.m_factory, strMethodName))
        listArgsNC.append(CSE.ValueFactory_CreateBoolValue(self.m_factory, bInitial))
        CSE.ChannelState_ExecuteCommand(self.m_state, "AddWaitTask", listArgsNC)

    def AddWaitForAsyncTask(self, strTaskName : str, bInitial : bool):
        listArgsNC = []
        listArgsNC.append(CSE.ValueFactory_CreateStringValue(self.m_factory, strTaskName))
        listArgsNC.append(CSE.ValueFactory_CreateBoolValue(self.m_factory, bInitial))
        CSE.ChannelState_ExecuteCommand(self.m_state, "WaitForAsyncTask", listArgsNC)

    def StartAsyncMotion(self, strJointName : str, dValue : float, strPositioning : str = None, strTriggerMethod : str = None, *args):
        listArgsNC = []
        listArgsNC.append(CSE.ValueFactory_CreateStringValue(self.m_factory, strJointName))
        listArgsNC.append(CSE.ValueFactory_CreateDoubleValue(self.m_factory, dValue))
        if strPositioning != None:
            listArgsNC.append(CSE.ValueFactory_CreateStringValue(self.m_factory, strPositioning))
        if strTriggerMethod != None:
            listArgsNC.append(CSE.ValueFactory_CreateStringValue(self.m_factory, strTriggerMethod))

        valueFactory = NCValueFactory(self.m_factory)
        for arg in args:
            listArgsNC.append(valueFactory.CreateValue(arg).m_obj)

        CSE.ChannelState_ExecuteCommand(self.m_state, "StartAsyncMotion", listArgsNC)

    def StartAsyncDelayTask(self, strName : str, dTime : float, strTriggerMethod : str = None):
        listArgsNC = []
        listArgsNC.append(CSE.ValueFactory_CreateStringValue(self.m_factory, strName))
        listArgsNC.append(CSE.ValueFactory_CreateDoubleValue(self.m_factory, dTime))
        if strTriggerMethod != None:
            listArgsNC.append(CSE.ValueFactory_CreateStringValue(self.m_factory, strTriggerMethod))
        CSE.ChannelState_ExecuteCommand(self.m_state, "StartAsyncDelayTask", listArgsNC)

    def SetSyncMarker(self, strSyncID : str, bAcknowledge : bool, bInitial : bool):
        listArgsNC = []
        listArgsNC.append(CSE.ValueFactory_CreateStringValue(self.m_factory, strSyncID))
        listArgsNC.append(CSE.ValueFactory_CreateBoolValue(self.m_factory, bAcknowledge))
        listArgsNC.append(CSE.ValueFactory_CreateBoolValue(self.m_factory, bInitial))
        CSE.ChannelState_ExecuteCommand(self.m_state, "SetSyncMarker", listArgsNC)

    def SetSyncPoint(self, strSyncID : str, bResetAck : bool, bInitial : bool, *channels):
        listArgsNC = []
        listArgsNC.append(CSE.ValueFactory_CreateStringValue(self.m_factory, strSyncID))
        listArgsNC.append(CSE.ValueFactory_CreateBoolValue(self.m_factory, bResetAck))
        listArgsNC.append(CSE.ValueFactory_CreateBoolValue(self.m_factory, bInitial))
        for chan in channels:
            listArgsNC.append(CSE.ValueFactory_CreateStringValue(self.m_factory, chan))
        CSE.ChannelState_ExecuteCommand(self.m_state, "SetSyncPoint", listArgsNC)

    def SuspendProgramExecution(self, bConditional : bool):
        listArgsNC = []
        listArgsNC.append(CSE.ValueFactory_CreateBoolValue(self.m_factory, bConditional))
        CSE.ChannelState_ExecuteCommand(self.m_state, "SuspendProgramExecution", listArgsNC)

    def GetJointList(self, strScope : str = None) -> list:
        listArgsNC = []
        if strScope != None:
            listArgsNC.append(CSE.ValueFactory_CreateStringValue(self.m_factory, strScope))
        retobj = CSE.ExprSystem_CallMethod(self.m_exprsys, "getJointList", listArgsNC)
        jointList = []
        valueList = CSE.Value_GetList(retobj)
        for jointName in valueList:
            jointList.append(CSE.Value_GetString(jointName))
        return jointList

    def HasJoint(self, strJointName : str, bGlobal : bool = None) -> bool:
        listArgsNC = []
        listArgsNC.append(CSE.ValueFactory_CreateStringValue(self.m_factory, strJointName))
        if bGlobal != None:
            listArgsNC.append(CSE.ValueFactory_CreateBoolValue(self.m_factory, bGlobal))
        retobj = CSE.ExprSystem_CallMethod(self.m_exprsys, "doesJointExist", listArgsNC)
        return CSE.Value_GetBool(retobj)

    def HasSpindle(self, strSpindleName : str) -> bool:
        return CSE.ChannelState_HasSpindle(self.m_state, strSpindleName)

    def AttachJoint(self, strNewJointName : str, strChannelName : str, strJointName : str, bDirect : bool = None):
        listArgsNC = []
        listArgsNC.append(CSE.ValueFactory_CreateStringValue(self.m_factory, strNewJointName))
        listArgsNC.append(CSE.ValueFactory_CreateStringValue(self.m_factory, strChannelName))
        listArgsNC.append(CSE.ValueFactory_CreateStringValue(self.m_factory, strJointName))
        if bDirect != None:
            listArgsNC.append(CSE.ValueFactory_CreateBoolValue(self.m_factory, bDirect))
        CSE.ChannelState_ExecuteCommand(self.m_state, "AttachJoint", listArgsNC)

    def DetachJoint(self, strJointName : str, bDirect : bool = None):
        listArgsNC = []
        listArgsNC.append(CSE.ValueFactory_CreateStringValue(self.m_factory, strJointName))
        if bDirect != None:
            listArgsNC.append(CSE.ValueFactory_CreateBoolValue(self.m_factory, bDirect))
        CSE.ChannelState_ExecuteCommand(self.m_state, "DetachJoint", listArgsNC)

    def RetrieveJoint(self, strJointName : str, bDirect : bool = None):
        listArgsNC = []
        listArgsNC.append(CSE.ValueFactory_CreateStringValue(self.m_factory, strJointName))
        if bDirect != None:
            listArgsNC.append(CSE.ValueFactory_CreateBoolValue(self.m_factory, bDirect))
        CSE.ChannelState_ExecuteCommand(self.m_state, "RetrieveJoint", listArgsNC)

    def SetJointAlias(self, strNewJointName : str, strJointName : str):
        listArgsNC = []
        listArgsNC.append(CSE.ValueFactory_CreateStringValue(self.m_factory, strNewJointName))
        listArgsNC.append(CSE.ValueFactory_CreateStringValue(self.m_factory, strJointName))
        CSE.ChannelState_ExecuteCommand(self.m_state, "SetJointAlias", listArgsNC)

    def SetJointParameter(self, strJointName : str, strParamName : str, value):
        valueFactory = NCValueFactory(self.m_factory)
        listArgsNC = []
        listArgsNC.append(CSE.ValueFactory_CreateStringValue(self.m_factory, strJointName))
        listArgsNC.append(CSE.ValueFactory_CreateStringValue(self.m_factory, strParamName))
        listArgsNC.append(valueFactory.CreateValue(value).m_obj)
        CSE.ChannelState_ExecuteCommand(self.m_state, "SetJointParameter", listArgsNC)

    def ResetJointParameter(self, strJointName : str, strParamName : str):
        listArgsNC = []
        listArgsNC.append(CSE.ValueFactory_CreateStringValue(self.m_factory, strJointName))
        listArgsNC.append(CSE.ValueFactory_CreateStringValue(self.m_factory, strParamName))
        CSE.ChannelState_ExecuteCommand(self.m_state, "ResetJointParameter", listArgsNC)

    def GetJointParameter(self, strJointName : str, strParamName : str, strScope : str = None):
        listArgsNC = []
        listArgsNC.append(CSE.ValueFactory_CreateStringValue(self.m_factory, strJointName))
        listArgsNC.append(CSE.ValueFactory_CreateStringValue(self.m_factory, strParamName))
        if strScope != None:
            listArgsNC.append(CSE.ValueFactory_CreateStringValue(self.m_factory, strScope))
        retobj = CSE.ExprSystem_CallMethod(self.m_exprsys, "getJointParameter", listArgsNC)
        strParamName = strParamName.lower()
        if strParamName == "name" or strParamName == "alias" or strParamName == "type":
            return CSE.Value_GetString(retobj)
        else:
            return CSE.Value_GetDouble(retobj)

    def GetJointName(self, nJointNumber : int) -> str:
        listArgsNC = []
        listArgsNC.append(CSE.ValueFactory_CreateIntegerValue(self.m_factory, nJointNumber))
        retobj = CSE.ExprSystem_CallMethod(self.m_exprsys, "getJointName", listArgsNC)
        return CSE.Value_GetString(retobj)

    def GetJointNumber(self, strJointName : str) -> int:
        listArgsNC = []
        listArgsNC.append(CSE.ValueFactory_CreateStringValue(self.m_factory, strJointName))
        retobj = CSE.ExprSystem_CallMethod(self.m_exprsys, "getJointNumber", listArgsNC)
        return CSE.Value_GetInteger(retobj)

    def SetJointRotationMode(self, strMode : str, strJointName : str = None):
        listArgsNC = []
        listArgsNC.append(CSE.ValueFactory_CreateStringValue(self.m_factory, strMode))
        if strJointName != None:
            listArgsNC.append(CSE.ValueFactory_CreateStringValue(self.m_factory, strJointName))
        CSE.ChannelState_ExecuteCommand(self.m_state, "SetJointRotationMode", listArgsNC)

    def GetJointRotationMode(self, strJointName : str) -> str:
        listArgsNC = []
        listArgsNC.append(CSE.ValueFactory_CreateStringValue(self.m_factory, strJointName))
        retobj = CSE.ExprSystem_CallMethod(self.m_exprsys, "getJointRotationMode", listArgsNC)
        return CSE.Value_GetString(retobj)

    def ActivateTrailing(self, strTrailingJointName : str, strLeadingJointName : str, dOffset : float, dFactor : float):
        listArgsNC = []
        listArgsNC.append(CSE.ValueFactory_CreateStringValue(self.m_factory, strTrailingJointName))
        listArgsNC.append(CSE.ValueFactory_CreateStringValue(self.m_factory, strLeadingJointName))
        listArgsNC.append(CSE.ValueFactory_CreateDoubleValue(self.m_factory, dOffset))
        listArgsNC.append(CSE.ValueFactory_CreateDoubleValue(self.m_factory, dFactor))
        CSE.ChannelState_ExecuteCommand(self.m_state, "ActivateTrailing", listArgsNC)

    def DeactivateTrailing(self, strTrailingJointName : str):
        listArgsNC = []
        listArgsNC.append(CSE.ValueFactory_CreateStringValue(self.m_factory, strTrailingJointName))
        CSE.ChannelState_ExecuteCommand(self.m_state, "DeactivateTrailing", listArgsNC)

    def GetLeadingJoint(self, strJointName : str) -> str:
        listArgsNC = []
        listArgsNC.append(CSE.ValueFactory_CreateStringValue(self.m_factory, strJointName))
        retobj = CSE.ExprSystem_CallMethod(self.m_exprsys, "getLeadingJoint", listArgsNC)
        return CSE.Value_GetString(retobj)

    def SetTargetJointValue(self, strJointName : str, dValue : float, strPosMode : str = None):
        listArgsNC = []
        listArgsNC.append(CSE.ValueFactory_CreateStringValue(self.m_factory, strJointName))
        listArgsNC.append(CSE.ValueFactory_CreateDoubleValue(self.m_factory, dValue))
        if strPosMode != None:
            listArgsNC.append(CSE.ValueFactory_CreateStringValue(self.m_factory, strPosMode))
        CSE.ChannelState_ExecuteCommand(self.m_state, "SetJointValue", listArgsNC)

    def GetTargetJointValue(self, strJointName : str, strCoordSys : str = None) -> float:
        listArgsNC = []
        listArgsNC.append(CSE.ValueFactory_CreateStringValue(self.m_factory, strJointName))
        if strCoordSys != None:
            listArgsNC.append(CSE.ValueFactory_CreateStringValue(self.m_factory, strCoordSys))
        retobj = CSE.ExprSystem_CallMethod(self.m_exprsys, "getTargetJointValue", listArgsNC)
        return CSE.Value_GetDouble(retobj)

    def GetLastJointValue(self, strJointName : str, strCoordSys : str = None) -> float:
        listArgsNC = []
        listArgsNC.append(CSE.ValueFactory_CreateStringValue(self.m_factory, strJointName))
        if strCoordSys != None:
            listArgsNC.append(CSE.ValueFactory_CreateStringValue(self.m_factory, strCoordSys))
        retobj = CSE.ExprSystem_CallMethod(self.m_exprsys, "getLastJointValue", listArgsNC)
        return CSE.Value_GetDouble(retobj)

    def GetProgJointValue(self, strJointName : str, strCoordSys : str = None) -> float:
        listArgsNC = []
        listArgsNC.append(CSE.ValueFactory_CreateStringValue(self.m_factory, strJointName))
        if strCoordSys != None:
            listArgsNC.append(CSE.ValueFactory_CreateStringValue(self.m_factory, strCoordSys))
        retobj = CSE.ExprSystem_CallMethod(self.m_exprsys, "getProgJointValue", listArgsNC)
        return CSE.Value_GetDouble(retobj)

    def GetExactJointValue(self, strJointName : str, strCoordSys : str = None) -> float:
        listArgsNC = []
        listArgsNC.append(CSE.ValueFactory_CreateStringValue(self.m_factory, strJointName))
        if strCoordSys != None:
            listArgsNC.append(CSE.ValueFactory_CreateStringValue(self.m_factory, strCoordSys))
        retobj = CSE.ExprSystem_CallMethod(self.m_exprsys, "getJointValue", listArgsNC)
        return CSE.Value_GetDouble(retobj)

    def GetRealJointValue(self, strJointName : str, strCoordSys : str = None) -> float:
        listArgsNC = []
        listArgsNC.append(CSE.ValueFactory_CreateStringValue(self.m_factory, strJointName))
        if strCoordSys != None:
            listArgsNC.append(CSE.ValueFactory_CreateStringValue(self.m_factory, strCoordSys))
        retobj = CSE.ExprSystem_CallMethod(self.m_exprsys, "getRealJointValue", listArgsNC)
        return CSE.Value_GetDouble(retobj)

    def SetGlobalSpindleMode(self, strMode : str):
        listArgsNC = []
        listArgsNC.append(CSE.ValueFactory_CreateStringValue(self.m_factory, strMode))
        CSE.ChannelState_ExecuteCommand(self.m_state, "SetGlobalSpindleMode", listArgsNC)

    def SetSpindleMode(self, strSpindleName : str, strMode : str):
        listArgsNC = []
        listArgsNC.append(CSE.ValueFactory_CreateStringValue(self.m_factory, strSpindleName))
        listArgsNC.append(CSE.ValueFactory_CreateStringValue(self.m_factory, strMode))
        CSE.ChannelState_ExecuteCommand(self.m_state, "SetSpindleMode", listArgsNC)

    def GetSpindleMode(self, strSpindleName : str) -> str:
        listArgsNC = []
        listArgsNC.append(CSE.ValueFactory_CreateStringValue(self.m_factory, strSpindleName))
        retobj = CSE.ExprSystem_CallMethod(self.m_exprsys, "getSpindleMode", listArgsNC)
        return CSE.Value_GetString(retobj)

    def SetGlobalSpindleSpeed(self, dSpeed : float):
        listArgsNC = []
        listArgsNC.append(CSE.ValueFactory_CreateDoubleValue(self.m_factory, dSpeed))
        CSE.ChannelState_ExecuteCommand(self.m_state, "SetGlobalSpindleSpeed", listArgsNC)

    def SetSpindleSpeed(self, strSpindleName : str, dSpeed : float):
        listArgsNC = []
        listArgsNC.append(CSE.ValueFactory_CreateStringValue(self.m_factory, strSpindleName))
        listArgsNC.append(CSE.ValueFactory_CreateDoubleValue(self.m_factory, dSpeed))
        CSE.ChannelState_ExecuteCommand(self.m_state, "SetSpindleSpeed", listArgsNC)

    def GetSpindleSpeed(self, strSpindleName : str) -> float:
        listArgsNC = []
        listArgsNC.append(CSE.ValueFactory_CreateStringValue(self.m_factory, strSpindleName))
        retobj = CSE.ExprSystem_CallMethod(self.m_exprsys, "getSpindleSpeed", listArgsNC)
        return CSE.Value_GetDouble(retobj)

    def SetSpindleState(self, strSpindleName : str, strState : str):
        listArgsNC = []
        listArgsNC.append(CSE.ValueFactory_CreateStringValue(self.m_factory, strSpindleName))
        listArgsNC.append(CSE.ValueFactory_CreateStringValue(self.m_factory, strState))
        CSE.ChannelState_ExecuteCommand(self.m_state, "SetSpindleState", listArgsNC)

    def GetSpindleState(self, strSpindleName : str) -> str:
        listArgsNC = []
        listArgsNC.append(CSE.ValueFactory_CreateStringValue(self.m_factory, strSpindleName))
        retobj = CSE.ExprSystem_CallMethod(self.m_exprsys, "getSpindleState", listArgsNC)
        return CSE.Value_GetString(retobj)

    def LoadOffset(self, strOffsetName : str):
        listArgsNC = []
        listArgsNC.append(CSE.ValueFactory_CreateStringValue(self.m_factory, strOffsetName))
        CSE.ChannelState_ExecuteCommand(self.m_state, "LoadOffset", listArgsNC)

    def DoesTransformationExist(self, strTrafoName : str) -> bool:
        listArgsNC = []
        listArgsNC.append(CSE.ValueFactory_CreateStringValue(self.m_factory, strTrafoName))
        retobj = CSE.ExprSystem_CallMethod(self.m_exprsys, "doesTransformationExist", listArgsNC)
        return CSE.Value_GetBool(retobj)

    def GetTransformationList(self) -> list:
        retobj = CSE.ExprSystem_CallMethod(self.m_exprsys, "getTransformationList", [])
        trafoList = []
        valueList = CSE.Value_GetList(retobj)
        for trafoName in valueList:
            trafoList.append(CSE.Value_GetString(trafoName))
        return trafoList

    def SetTrafoRotationOrder(self, strOrder : str):
        listArgsNC = []
        listArgsNC.append(CSE.ValueFactory_CreateStringValue(self.m_factory, strOrder))
        CSE.ChannelState_ExecuteCommand(self.m_state, "SetTrafoRotationOrder", listArgsNC)

    def GetTrafoRotationOrder(self) -> str:
        retobj = CSE.ExprSystem_CallMethod(self.m_exprsys, "getTrafoRotationOrder", [])
        return CSE.Value_GetString(retobj)

    def ResetTransformation(self, strTrafoName : str):
        listArgsNC = []
        listArgsNC.append(CSE.ValueFactory_CreateStringValue(self.m_factory, strTrafoName))
        CSE.ChannelState_ExecuteCommand(self.m_state, "ResetTransformation", listArgsNC)

    def ActivateTransformation(self, strTrafoName : str, bActive : bool, bModal : bool):
        listArgsNC = []
        listArgsNC.append(CSE.ValueFactory_CreateStringValue(self.m_factory, strTrafoName))
        listArgsNC.append(CSE.ValueFactory_CreateBoolValue(self.m_factory, bActive))
        listArgsNC.append(CSE.ValueFactory_CreateBoolValue(self.m_factory, bModal))
        CSE.ChannelState_ExecuteCommand(self.m_state, "ActivateTransformation", listArgsNC)

    def IsTransformationActive(self, strTrafoName : str) -> bool:
        listArgsNC = []
        listArgsNC.append(CSE.ValueFactory_CreateStringValue(self.m_factory, strTrafoName))
        retobj = CSE.ExprSystem_CallMethod(self.m_exprsys, "isTransformationActive", listArgsNC)
        return CSE.Value_GetBool(retobj)

    def SetTransformationMatrix(self, strTrafoName : str, matrix : Matrix4):
        listArgsNC = []
        listArgsNC.append(CSE.ValueFactory_CreateStringValue(self.m_factory, strTrafoName))
        listArgsNC.append(CSE.ValueFactory_CreateMatrixValue(self.m_factory, matrix.mat))
        CSE.ChannelState_ExecuteCommand(self.m_state, "SetTrafoMatrix", listArgsNC)

    def GetTransformationMatrix(self, strTrafoName : str) -> Matrix4:
        listArgsNC = []
        listArgsNC.append(CSE.ValueFactory_CreateStringValue(self.m_factory, strTrafoName))
        retobj = CSE.ExprSystem_CallMethod(self.m_exprsys, "getTrafoMatrix", listArgsNC)
        return Matrix4.CreateMatrixFromList(CSE.Value_GetMatrix(retobj))

    def SetTransformationOffset(self, strTrafoName : str, strJointName : str, dOffset : float, bRelative : bool):
        listArgsNC = []
        listArgsNC.append(CSE.ValueFactory_CreateStringValue(self.m_factory, strTrafoName))
        listArgsNC.append(CSE.ValueFactory_CreateBoolValue(self.m_factory, bRelative))
        listArgsNC.append(CSE.ValueFactory_CreateStringValue(self.m_factory, strJointName))
        listArgsNC.append(CSE.ValueFactory_CreateDoubleValue(self.m_factory, dOffset))
        CSE.ChannelState_ExecuteCommand(self.m_state, "DisplaceOrigin", listArgsNC)

    def GetTransformationOffset(self, strTrafoName : str, strJointName : str) -> float:
        listArgsNC = []
        listArgsNC.append(CSE.ValueFactory_CreateStringValue(self.m_factory, strTrafoName))
        listArgsNC.append(CSE.ValueFactory_CreateStringValue(self.m_factory, strJointName))
        retobj = CSE.ExprSystem_CallMethod(self.m_exprsys, "getTrafoOffset", listArgsNC)
        return CSE.Value_GetDouble(retobj)

    def SetTransformationRotation(self, strTrafoName : str, strJointName : str, dAngle : float, bRelative : bool):
        listArgsNC = []
        listArgsNC.append(CSE.ValueFactory_CreateStringValue(self.m_factory, strTrafoName))
        listArgsNC.append(CSE.ValueFactory_CreateBoolValue(self.m_factory, bRelative))
        listArgsNC.append(CSE.ValueFactory_CreateStringValue(self.m_factory, strJointName))
        listArgsNC.append(CSE.ValueFactory_CreateDoubleValue(self.m_factory, dAngle))
        CSE.ChannelState_ExecuteCommand(self.m_state, "SetRotation", listArgsNC)

    def SetTransformationScale(self, strTrafoName : str, strJointName : str, dScale : float, bRelative : bool):
        listArgsNC = []
        listArgsNC.append(CSE.ValueFactory_CreateStringValue(self.m_factory, strTrafoName))
        listArgsNC.append(CSE.ValueFactory_CreateBoolValue(self.m_factory, bRelative))
        listArgsNC.append(CSE.ValueFactory_CreateStringValue(self.m_factory, strJointName))
        listArgsNC.append(CSE.ValueFactory_CreateDoubleValue(self.m_factory, dScale))
        CSE.ChannelState_ExecuteCommand(self.m_state, "SetScale", listArgsNC)

    def CreateCoordinate(self) -> NCCoordinate:
        retobj = CSE.ExprSystem_CallMethod(self.m_exprsys, "createCoordinate", [])
        return NCCoordinate(CSE.Value_GetObject(retobj))

    def GetCurrentCoordinate(self, strKind : str, strCoordSystem : str) -> NCCoordinate:
        listArgsNC = []
        listArgsNC.append(CSE.ValueFactory_CreateStringValue(self.m_factory, strKind))
        listArgsNC.append(CSE.ValueFactory_CreateStringValue(self.m_factory, strCoordSystem))
        retobj = CSE.ExprSystem_CallMethod(self.m_exprsys, "getCurrentCoordinate", listArgsNC)
        return NCCoordinate(CSE.Value_GetObject(retobj))

    def TransformCoordinate(self, coord : NCCoordinate, strTrafoStart : str, strTrafoEnd : str) -> NCCoordinate:
        listArgsNC = []
        listArgsNC.append(CSE.ValueFactory_CreateObjectValue(coord.m_nccoord))
        listArgsNC.append(CSE.ValueFactory_CreateStringValue(self.m_factory, strTrafoStart))
        listArgsNC.append(CSE.ValueFactory_CreateStringValue(self.m_factory, strTrafoEnd))
        retobj = CSE.ExprSystem_CallMethod(self.m_exprsys, "transformCoordinate", listArgsNC)
        return NCCoordinate(CSE.Value_GetObject(retobj))

    def AttachCarrier(self, strCarrierName : str, bDirect : bool = None):
        listArgsNC = []
        listArgsNC.append(CSE.ValueFactory_CreateStringValue(self.m_factory, strCarrierName))
        if bDirect != None:
            listArgsNC.append(CSE.ValueFactory_CreateBoolValue(self.m_factory, bDirect))
        CSE.ChannelState_ExecuteCommand(self.m_state, "AttachCarrier", listArgsNC)

    def DetachCarrier(self, strCarrierName : str):
        listArgsNC = []
        listArgsNC.append(CSE.ValueFactory_CreateStringValue(self.m_factory, strCarrierName))
        CSE.ChannelState_ExecuteCommand(self.m_state, "DetachCarrier", listArgsNC)

    def GetCarrierList(self) -> str:
        retobj = CSE.ExprSystem_CallMethod(self.m_exprsys, "getCarrierList", [])
        carrierList = []
        valueList = CSE.Value_GetList(retobj)
        for carrierName in valueList:
            carrierList.append(CSE.Value_GetString(carrierName))
        return carrierList

    def GetCarrierTool(self, strCarrierName : str, strSlotID : str) -> str:
        listArgsNC = []
        listArgsNC.append(CSE.ValueFactory_CreateStringValue(self.m_factory, strCarrierName))
        listArgsNC.append(CSE.ValueFactory_CreateStringValue(self.m_factory, strSlotID))
        retobj = CSE.ExprSystem_CallMethod(self.m_exprsys, "getCarrierTool", listArgsNC)
        return CSE.Value_GetString(retobj)

    def GetSlotIDByTool(self, strCarrierName : str, strToolID : str) -> str:
        listArgsNC = []
        listArgsNC.append(CSE.ValueFactory_CreateStringValue(self.m_factory, strCarrierName))
        listArgsNC.append(CSE.ValueFactory_CreateStringValue(self.m_factory, strToolID))
        retobj = CSE.ExprSystem_CallMethod(self.m_exprsys, "getSlotIDByTool", listArgsNC)
        return CSE.Value_GetString(retobj)

    def MountHead(self, strDeviceName : str, strCarrierName : str):
        listArgsNC = []
        listArgsNC.append(CSE.ValueFactory_CreateStringValue(self.m_factory, strDeviceName))
        listArgsNC.append(CSE.ValueFactory_CreateStringValue(self.m_factory, strCarrierName))
        CSE.ChannelState_ExecuteCommand(self.m_state, "MountHead", listArgsNC)

    def UnmountHead(self, strCarrierName : str):
        listArgsNC = []
        listArgsNC.append(CSE.ValueFactory_CreateStringValue(self.m_factory, strCarrierName))
        CSE.ChannelState_ExecuteCommand(self.m_state, "UnmountHead", listArgsNC)

    def GetCurrentHead(self, strCarrierName : str) -> str:
        listArgsNC = []
        listArgsNC.append(CSE.ValueFactory_CreateStringValue(self.m_factory, strCarrierName))
        retobj = CSE.ExprSystem_CallMethod(self.m_exprsys, "getCurrentHead", listArgsNC)
        return CSE.Value_GetString(retobj)

    def GenerateTool(self, strToolName : str, strCarrierName : str):
        listArgsNC = []
        listArgsNC.append(CSE.ValueFactory_CreateStringValue(self.m_factory, strToolName))
        listArgsNC.append(CSE.ValueFactory_CreateStringValue(self.m_factory, strCarrierName))
        CSE.ChannelState_ExecuteCommand(self.m_state, "GenerateTool", listArgsNC)

    def GetCurrentTool(self, strCarrierName : str) -> str:
        listArgsNC = []
        listArgsNC.append(CSE.ValueFactory_CreateStringValue(self.m_factory, strCarrierName))
        retobj = CSE.ExprSystem_CallMethod(self.m_exprsys, "getCurrentTool", listArgsNC)
        return CSE.Value_GetString(retobj)

    def ActivateNextTool(self, strCarrierName : str):
        listArgsNC = []
        listArgsNC.append(CSE.ValueFactory_CreateStringValue(self.m_factory, strCarrierName))
        CSE.ChannelState_ExecuteCommand(self.m_state, "ActivateNextTool", listArgsNC)

    def SetNextTool(self, strToolID : str, strCarrierName : str):
        listArgsNC = []
        listArgsNC.append(CSE.ValueFactory_CreateStringValue(self.m_factory, strToolID))
        listArgsNC.append(CSE.ValueFactory_CreateStringValue(self.m_factory, strCarrierName))
        CSE.ChannelState_ExecuteCommand(self.m_state, "SetNextTool", listArgsNC)

    def GetNextTool(self, strCarrierName : str) -> str:
        listArgsNC = []
        listArgsNC.append(CSE.ValueFactory_CreateStringValue(self.m_factory, strCarrierName))
        retobj = CSE.ExprSystem_CallMethod(self.m_exprsys, "getNextTool", listArgsNC)
        return CSE.Value_GetString(retobj)

    def GetToolParameter(self, strToolID : str, strAttribute : str, switch = None):
        listArgsNC = []
        listArgsNC.append(CSE.ValueFactory_CreateStringValue(self.m_factory, strToolID))
        listArgsNC.append(CSE.ValueFactory_CreateStringValue(self.m_factory, strAttribute))
        if switch != None:
            if isinstance(switch, int):
                listArgsNC.append(CSE.ValueFactory_CreateIntegerValue(self.m_factory, switch))
            else:
                listArgsNC.append(CSE.ValueFactory_CreateStringValue(self.m_factory, switch))
        retobj = CSE.ExprSystem_CallMethod(self.m_exprsys, "getToolParameter", listArgsNC)
        strAttribute = strAttribute.lower()
        if strAttribute == "type" or strAttribute == "quadrant":
            return CSE.Value_GetString(retobj)
        else:
            return CSE.Value_GetDouble(retobj)

    def SetToolCorrection(self, nIndex : int, strCarrierName : str, bIgnoreErrors : bool = None, strSpindleName : str = None):
        listArgsNC = []
        listArgsNC.append(CSE.ValueFactory_CreateIntegerValue(self.m_factory, nIndex))
        listArgsNC.append(CSE.ValueFactory_CreateStringValue(self.m_factory, strCarrierName))
        if bIgnoreErrors != None:
            listArgsNC.append(CSE.ValueFactory_CreateBoolValue(self.m_factory, bIgnoreErrors))
        if strSpindleName != None:
            listArgsNC.append(CSE.ValueFactory_CreateStringValue(self.m_factory, strSpindleName))
        CSE.ChannelState_ExecuteCommand(self.m_state, "SetToolCorrection", listArgsNC)

    def SetToolWear(self, strCarrierName : str, strWearType : str, nIndex : int, dValue : float):
        listArgsNC = []
        listArgsNC.append(CSE.ValueFactory_CreateStringValue(self.m_factory, strCarrierName))
        listArgsNC.append(CSE.ValueFactory_CreateStringValue(self.m_factory, strWearType))
        listArgsNC.append(CSE.ValueFactory_CreateIntegerValue(self.m_factory, nIndex))
        listArgsNC.append(CSE.ValueFactory_CreateDoubleValue(self.m_factory, dValue))
        CSE.ChannelState_ExecuteCommand(self.m_state, "SetToolWear", listArgsNC)

    def SetCorrectionSwitch(self, strValue : str):
        listArgsNC = []
        listArgsNC.append(CSE.ValueFactory_CreateStringValue(self.m_factory, strValue))
        CSE.ChannelState_ExecuteCommand(self.m_state, "SetCorrectionSwitch", listArgsNC)

    def GetCorrectionSwitch(self) -> str:
        retobj = CSE.ExprSystem_CallMethod(self.m_exprsys, "getCorrectionSwitch", [])
        return CSE.Value_GetString(retobj)

    def SetLCorrection(self, dValue : float):
        listArgsNC = []
        listArgsNC.append(CSE.ValueFactory_CreateDoubleValue(self.m_factory, dValue))
        CSE.ChannelState_ExecuteCommand(self.m_state, "SetLCorrection", listArgsNC)

    def GetLCorrection(self) -> float:
        retobj = CSE.ExprSystem_CallMethod(self.m_exprsys, "getLCorrection", [])
        return CSE.Value_GetDouble(retobj)

    def SetQCorrection(self, dValue : float):
        listArgsNC = []
        listArgsNC.append(CSE.ValueFactory_CreateDoubleValue(self.m_factory, dValue))
        CSE.ChannelState_ExecuteCommand(self.m_state, "SetQCorrection", listArgsNC)

    def GetQCorrection(self) -> float:
        retobj = CSE.ExprSystem_CallMethod(self.m_exprsys, "getQCorrection", [])
        return CSE.Value_GetDouble(retobj)

    def SetZCorrection(self, dValue : float):
        listArgsNC = []
        listArgsNC.append(CSE.ValueFactory_CreateDoubleValue(self.m_factory, dValue))
        CSE.ChannelState_ExecuteCommand(self.m_state, "SetZCorrection", listArgsNC)

    def GetZCorrection(self) -> float:
        retobj = CSE.ExprSystem_CallMethod(self.m_exprsys, "getZCorrection", [])
        return CSE.Value_GetDouble(retobj)

    def SetRadCorrection(self, dValue : float):
        listArgsNC = []
        listArgsNC.append(CSE.ValueFactory_CreateDoubleValue(self.m_factory, dValue))
        CSE.ChannelState_ExecuteCommand(self.m_state, "SetRadCorrection", listArgsNC)

    def GetRadCorrection(self) -> float:
        retobj = CSE.ExprSystem_CallMethod(self.m_exprsys, "getRadCorrection", [])
        return CSE.Value_GetDouble(retobj)

    def SetQuadrant(self, strQuadrant : str):
        listArgsNC = []
        listArgsNC.append(CSE.ValueFactory_CreateStringValue(self.m_factory, strQuadrant))
        CSE.ChannelState_ExecuteCommand(self.m_state, "SetQuadrant", listArgsNC)

    def GetQuadrant(self) -> str:
        retobj = CSE.ExprSystem_CallMethod(self.m_exprsys, "getQuadrant", [])
        return CSE.Value_GetString(retobj)

    def GetHeadCorrection(self, strCarrierName : str, strPocketID : str, *args) -> Matrix4:
        listArgsNC = []
        listArgsNC.append(CSE.ValueFactory_CreateStringValue(self.m_factory, strCarrierName))
        listArgsNC.append(CSE.ValueFactory_CreateStringValue(self.m_factory, strPocketID))
        for index, arg in enumerate(args):
            if (index & 1) == 0:
                listArgsNC.append(CSE.ValueFactory_CreateStringValue(self.m_factory, arg))
            else:
                listArgsNC.append(CSE.ValueFactory_CreateDoubleValue(self.m_factory, arg))
        retobj = CSE.ExprSystem_CallMethod(self.m_exprsys, "getHeadCorrection", listArgsNC)
        return Matrix4.CreateMatrixFromList(CSE.Value_GetMatrix(retobj))

    def SetKinematicTransformation(self, strChainName : str, bWCS : bool = None):
        listArgsNC = []
        listArgsNC.append(CSE.ValueFactory_CreateStringValue(self.m_factory, strChainName))
        if bWCS != None:
            listArgsNC.append(CSE.ValueFactory_CreateDoubleValue(self.m_factory, bWCS))
        CSE.ChannelState_ExecuteCommand(self.m_state, "SetKinematicTransformation", listArgsNC)

    def GetKinematicTransformation(self) -> str:
        retobj = CSE.ExprSystem_CallMethod(self.m_exprsys, "getKinematicTransformation", [])
        return CSE.Value_GetString(retobj)

    def GetKinematicChainType(self, strChainName : str) -> str:
        listArgsNC = []
        listArgsNC.append(CSE.ValueFactory_CreateStringValue(self.m_factory, strChainName))
        retobj = CSE.ExprSystem_CallMethod(self.m_exprsys, "getKinematicChainType", listArgsNC)
        return CSE.Value_GetString(retobj)

    def GetKinematicChainAxis(self, strChainName : str, strAxisType : str) -> str:
        listArgsNC = []
        listArgsNC.append(CSE.ValueFactory_CreateStringValue(self.m_factory, strChainName))
        listArgsNC.append(CSE.ValueFactory_CreateStringValue(self.m_factory, strAxisType))
        retobj = CSE.ExprSystem_CallMethod(self.m_exprsys, "getKinematicChainAxis", listArgsNC)
        return CSE.Value_GetString(retobj)

    def GetKinematicChainPos(self, strChainName : str, coord : NCCoordinate, bWCS : bool, strScope : str, strAxisName : str = None) -> Matrix4:
        listArgsNC = []
        listArgsNC.append(CSE.ValueFactory_CreateStringValue(self.m_factory, strChainName))
        listArgsNC.append(CSE.ValueFactory_CreateObjectValue(self.m_factory, coord.m_nccoord))
        listArgsNC.append(CSE.ValueFactory_CreateBoolValue(self.m_factory, bWCS))
        listArgsNC.append(CSE.ValueFactory_CreateStringValue(self.m_factory, strScope))
        if strAxisName != None:
            listArgsNC.append(CSE.ValueFactory_CreateStringValue(self.m_factory, strAxisName))
        retobj = CSE.ExprSystem_CallMethod(self.m_exprsys, "getKinematicChainPos", listArgsNC)
        return Matrix4.CreateMatrixFromList(CSE.Value_GetMatrix(retobj))

    def GetKinematicChainAxisList(self, strChainName : str) -> list:
        listArgsNC = []
        listArgsNC.append(CSE.ValueFactory_CreateStringValue(self.m_factory, strChainName))
        retobj = CSE.ExprSystem_CallMethod(self.m_exprsys, "getKinematicChainAxisList", listArgsNC)
        axisList = []
        valueList = CSE.Value_GetList(retobj)
        for axisName in valueList:
            axisList.append(CSE.Value_GetString(axisName))
        return axisList

    def SetNormalComponent(self, strJointName : str, dValue : float):
        listArgsNC = []
        listArgsNC.append(CSE.ValueFactory_CreateStringValue(self.m_factory, strJointName))
        listArgsNC.append(CSE.ValueFactory_CreateDoubleValue(self.m_factory, dValue))
        CSE.ChannelState_ExecuteCommand(self.m_state, "SetNormalComponent", listArgsNC)

    def SetInterpolationMode(self, strMode : str):
        listArgsNC = []
        listArgsNC.append(CSE.ValueFactory_CreateStringValue(self.m_factory, strMode))
        CSE.ChannelState_ExecuteCommand(self.m_state, "SetInterpolationMode", listArgsNC)

    def GetInterpolationMode(self) -> str:
        retobj = CSE.ExprSystem_CallMethod(self.m_exprsys, "getInterpolationMode", [])
        return CSE.Value_GetString(retobj)

    def CalculateIKSAngles(self, strChainName : str, vecOri : Vector3, coord : NCCoordinate = None) -> NCStruct:
        listArgsNC = []
        listArgsNC.append(CSE.ValueFactory_CreateStringValue(self.m_factory, strChainName))
        listArgsNC.append(CSE.ValueFactory_CreateVectorValue(self.m_factory, vecOri.vec))
        if coord != None:
            listArgsNC.append(CSE.ValueFactory_CreateObjectValue(coord.m_nccoord))
        return NCStruct(CSE.ExprSystem_CallMethod(self.m_exprsys, "calculateIKSAngles", listArgsNC))

    def CalculateIKSLinears(self, strChainName : str, coord : NCCoordinate, dPartAngle : float, dToolAngle : float) -> Vector3:
        listArgsNC = []
        listArgsNC.append(CSE.ValueFactory_CreateStringValue(self.m_factory, strChainName))
        listArgsNC.append(CSE.ValueFactory_CreateObjectValue(coord.m_nccoord))
        listArgsNC.append(CSE.ValueFactory_CreateDoubleValue(self.m_factory, dPartAngle))
        listArgsNC.append(CSE.ValueFactory_CreateDoubleValue(self.m_factory, dToolAngle))
        retobj = CSE.ExprSystem_CallMethod(self.m_exprsys, "calculateIKSLinears", listArgsNC)
        vec = CSE.Value_GetVector(retobj)
        return Vector3(vec[0], vec[1], vec[2])

    def SetToolRadiusCorrectionMode(self, bActive : bool, bLeft : bool = None, bModal : bool = None):
        listArgsNC = []
        listArgsNC.append(CSE.ValueFactory_CreateBoolValue(self.m_factory, bActive))
        if bLeft != None:
            listArgsNC.append(CSE.ValueFactory_CreateBoolValue(self.m_factory, bLeft))
        if bModal != None:
            listArgsNC.append(CSE.ValueFactory_CreateBoolValue(self.m_factory, bModal))
        CSE.ChannelState_ExecuteCommand(self.m_state, "SetToolRadiusCorrectionMode", listArgsNC)

    def IsToolRadiusCorrectionActive(self) -> bool:
        retobj = CSE.ExprSystem_CallMethod(self.m_exprsys, "isToolRadiusCorrectionActive", [])
        return CSE.Value_GetBool(retobj)

    def IsToolRadiusCorrectionLeft(self) -> bool:
        retobj = CSE.ExprSystem_CallMethod(self.m_exprsys, "isToolRadiusCorrectionLeft", [])
        return CSE.Value_GetBool(retobj)

    def SetRadiusCorrectionApproachingMode(self, strMode : str, bModal : bool = None):
        listArgsNC = []
        listArgsNC.append(CSE.ValueFactory_CreateStringValue(self.m_factory, strMode))
        if bModal != None:
            listArgsNC.append(CSE.ValueFactory_CreateBoolValue(self.m_factory, bModal))
        CSE.ChannelState_ExecuteCommand(self.m_state, "SetRadiusCorrectionApproachingMode", listArgsNC)

    def GetRadiusCorrectionApproachingMode(self) -> str:
        retobj = CSE.ExprSystem_CallMethod(self.m_exprsys, "getRadiusCorrectionApproachingMode", [])
        return CSE.Value_GetString(retobj)

    def SetRadiusCorrectionDepartingMode(self, strMode : str, bModal : bool = None):
        listArgsNC = []
        listArgsNC.append(CSE.ValueFactory_CreateStringValue(self.m_factory, strMode))
        if bModal != None:
            listArgsNC.append(CSE.ValueFactory_CreateBoolValue(self.m_factory, bModal))
        CSE.ChannelState_ExecuteCommand(self.m_state, "SetRadiusCorrectionDepartingMode", listArgsNC)

    def GetRadiusCorrectionDepartingMode(self) -> str:
        retobj = CSE.ExprSystem_CallMethod(self.m_exprsys, "getRadiusCorrectionDepartingMode", [])
        return CSE.Value_GetString(retobj)

    def SetRadiusCorrectionCornerMode(self, strMode : str):
        listArgsNC = []
        listArgsNC.append(CSE.ValueFactory_CreateStringValue(self.m_factory, strMode))
        CSE.ChannelState_ExecuteCommand(self.m_state, "SetRadiusCorrectionCornerMode", listArgsNC)

    def GetRadiusCorrectionCornerMode(self) -> str:
        retobj = CSE.ExprSystem_CallMethod(self.m_exprsys, "getRadiusCorrectionCornerMode", [])
        return CSE.Value_GetString(retobj)

    def SetApproachingPlaneRadius(self, dValue : float, bModal : bool = None):
        listArgsNC = []
        listArgsNC.append(CSE.ValueFactory_CreateDoubleValue(self.m_factory, dValue))
        if bModal != None:
            listArgsNC.append(CSE.ValueFactory_CreateBoolValue(self.m_factory, bModal))
        CSE.ChannelState_ExecuteCommand(self.m_state, "SetApproachingPlaneRadius", listArgsNC)

    def GetApproachingPlaneRadius(self) -> float:
        retobj = CSE.ExprSystem_CallMethod(self.m_exprsys, "getApproachingPlaneRadius", [])
        return CSE.Value_GetDouble(retobj)

    def SetApproachingPlaneDist(self, dValue : float, bModal : bool = None):
        listArgsNC = []
        listArgsNC.append(CSE.ValueFactory_CreateDoubleValue(self.m_factory, dValue))
        if bModal != None:
            listArgsNC.append(CSE.ValueFactory_CreateBoolValue(self.m_factory, bModal))
        CSE.ChannelState_ExecuteCommand(self.m_state, "SetApproachingPlaneDist", listArgsNC)

    def GetApproachingPlaneDist(self) -> float:
        retobj = CSE.ExprSystem_CallMethod(self.m_exprsys, "getApproachingPlaneDist", [])
        return CSE.Value_GetDouble(retobj)

    def Set3DApproaching(self, bActive : bool, bModal : bool = None):
        listArgsNC = []
        listArgsNC.append(CSE.ValueFactory_CreateBoolValue(self.m_factory, bActive))
        if bModal != None:
            listArgsNC.append(CSE.ValueFactory_CreateBoolValue(self.m_factory, bModal))
        CSE.ChannelState_ExecuteCommand(self.m_state, "Set3DApproaching", listArgsNC)

    def Is3DApproachingActive(self) -> bool:
        retobj = CSE.ExprSystem_CallMethod(self.m_exprsys, "is3DApproachingActive", [])
        return CSE.Value_GetBool(retobj)

    def SetContourSelfIntersectMode(self, strMode : str):
        listArgsNC = []
        listArgsNC.append(CSE.ValueFactory_CreateStringValue(self.m_factory, strMode))
        CSE.ChannelState_ExecuteCommand(self.m_state, "SetContourSelfIntersectMode", listArgsNC)

    def GetContourSelfIntersectMode(self) -> str:
        retobj = CSE.ExprSystem_CallMethod(self.m_exprsys, "getContourSelfIntersectMode", [])
        return CSE.Value_GetString(retobj)

    def SetAngle(self, dValue : float):
        listArgsNC = []
        listArgsNC.append(CSE.ValueFactory_CreateDoubleValue(self.m_factory, dValue))
        CSE.ChannelState_ExecuteCommand(self.m_state, "SetAngle", listArgsNC)

    def SetContourFeature(self, strFeatureType : str, strValueType : str, dValue : float, bModal : bool = None, strScope : str = None):
        listArgsNC = []
        listArgsNC.append(CSE.ValueFactory_CreateStringValue(self.m_factory, strFeatureType))
        listArgsNC.append(CSE.ValueFactory_CreateStringValue(self.m_factory, strValueType))
        listArgsNC.append(CSE.ValueFactory_CreateDoubleValue(self.m_factory, dValue))
        if bModal != None:
            listArgsNC.append(CSE.ValueFactory_CreateBoolValue(self.m_factory, bModal))
        if strScope != None:
            listArgsNC.append(CSE.ValueFactory_CreateStringValue(self.m_factory, strScope))
        CSE.ChannelState_ExecuteCommand(self.m_state, "SetContourFeature", listArgsNC)

    def ActivateMeasuringCycle(self):
        CSE.ChannelState_ExecuteCommand(self.m_state, "ActivateMeasuringCycle", [])

    def ResetMeasuringProbeCollision(self):
        CSE.ChannelState_ExecuteCommand(self.m_state, "ResetMeasuringProbeCollision", [])

    def HasMeasuringProbeCollided(self) -> bool:
        retobj = CSE.ExprSystem_CallMethod(self.m_exprsys, "hasMeasuringProbeCollided", [])
        return CSE.Value_GetBool(retobj)

    def SetStopAtCollision(self, strGroup1 : str, strGroupSel1 : str, strGroup2 : str = None, strGroupSel2 : str = None):
        listArgsNC = []
        listArgsNC.append(CSE.ValueFactory_CreateStringValue(self.m_factory, strGroup1))
        listArgsNC.append(CSE.ValueFactory_CreateStringValue(self.m_factory, strGroupSel1))
        if strGroup2 != None:
            listArgsNC.append(CSE.ValueFactory_CreateStringValue(self.m_factory, strGroup2))
        if strGroupSel2 != None:
            listArgsNC.append(CSE.ValueFactory_CreateStringValue(self.m_factory, strGroupSel2))
        CSE.ChannelState_ExecuteCommand(self.m_state, "SetStopAtCollision", listArgsNC)

    def ResetMotionStopCollision(self, strMode : str):
        CSE.ChannelState_ExecuteCommand(self.m_state, "ResetMotionStopCollision", [])

    def WasMotionStoppedByCollision(self) -> bool:
        retobj = CSE.ExprSystem_CallMethod(self.m_exprsys, "wasMotionStoppedByCollision", [])
        return CSE.Value_GetBool(retobj)

    def CallMethod(self, strMethodName : str, *args) -> str:
        valueFactory = NCValueFactory(self.m_factory)
        listArgsNC = []
        for obj in args:
            listArgsNC.append(valueFactory.CreateValue(obj).m_obj)
        retobj = CSE.ExprSystem_CallMethod(self.m_exprsys, strMethodName, listArgsNC)
        if retobj == None:
            return None
        return NCObject.GetNativeObject(retobj)

    def DoesObjectExist(self, strObjName : str) -> bool:
        listArgsNC = []
        listArgsNC.append(CSE.ValueFactory_CreateStringValue(self.m_factory, strObjName))
        retobj = CSE.ExprSystem_CallMethod(self.m_exprsys, "exists", listArgsNC)
        return CSE.Value_GetBool(retobj)

    def GetToolNameByNumber(self, nToolNumber : int) -> str:
        listArgsNC = []
        listArgsNC.append(CSE.ValueFactory_CreateIntegerValue(self.m_factory, nToolNumber))
        retobj = CSE.ExprSystem_CallMethod(self.m_exprsys, "getToolNameByNumber", listArgsNC)
        return CSE.Value_GetString(retobj)

    def GetJunction(self, strComponent : str, strJunction : str) -> str:
        listArgsNC = []
        listArgsNC.append(CSE.ValueFactory_CreateStringValue(self.m_factory, strComponent))
        listArgsNC.append(CSE.ValueFactory_CreateStringValue(self.m_factory, strJunction))
        retobj = CSE.ExprSystem_CallMethod(self.m_exprsys, "getJunction", listArgsNC)
        return CSE.Value_GetString(retobj)

    def Grasp(self, strChildName : str, strParentName : str):
        listArgsNC = []
        listArgsNC.append(CSE.ValueFactory_CreateStringValue(self.m_factory, strChildName))
        listArgsNC.append(CSE.ValueFactory_CreateStringValue(self.m_factory, strParentName))
        CSE.ChannelState_ExecuteCommand(self.m_state, "Grasp", listArgsNC)

    def Release(self, strChildName : str, strParentName : str = None):
        listArgsNC = []
        listArgsNC.append(CSE.ValueFactory_CreateStringValue(self.m_factory, strChildName))
        if strParentName != None:
            listArgsNC.append(CSE.ValueFactory_CreateStringValue(self.m_factory, strParentName))
        CSE.ChannelState_ExecuteCommand(self.m_state, "Release", listArgsNC)

    def SetPosition(self, strObjName : str, x : float, y : float, z : float, a : float, b : float, c : float):
        listArgsNC = []
        listArgsNC.append(CSE.ValueFactory_CreateStringValue(self.m_factory, strObjName))
        listArgsNC.append(CSE.ValueFactory_CreateDoubleValue(self.m_factory, x))
        listArgsNC.append(CSE.ValueFactory_CreateDoubleValue(self.m_factory, y))
        listArgsNC.append(CSE.ValueFactory_CreateDoubleValue(self.m_factory, z))
        listArgsNC.append(CSE.ValueFactory_CreateDoubleValue(self.m_factory, a))
        listArgsNC.append(CSE.ValueFactory_CreateDoubleValue(self.m_factory, b))
        listArgsNC.append(CSE.ValueFactory_CreateDoubleValue(self.m_factory, c))
        CSE.ChannelState_ExecuteCommand(self.m_state, "Position", listArgsNC)

    def SetVisibility(self, strObjName : str, strMode : str):
        listArgsNC = []
        listArgsNC.append(CSE.ValueFactory_CreateStringValue(self.m_factory, strObjName))
        listArgsNC.append(CSE.ValueFactory_CreateStringValue(self.m_factory, strMode))
        CSE.ChannelState_ExecuteCommand(self.m_state, "Visibility", listArgsNC)



# Factory class to create calls which are CSE executable objects. This class is used during
# NC language parsing to translate a line of NC code into a sequence of calls. The generated
# calls are not returned by the methods of this class but registered inside CSE instead.
class CallFactory:
    # Call execution mode enum definition. Don't modify!
    DIRECT_EXECUTION, SYNC_EXECUTION, SYNC_DIRECT_EXECUTION = range(3)

    # Sync call type enum definition. Don't modify!
    NO_SYNC_CALL, DO_SYNC_CALL, FROM_SYNC_CALL, EVERY_SYNC_CALL, WHEN_SYNC_CALL, WHENEVER_SYNC_CALL = range(6)

    # Search mode enum definition. Don't modify!
    SEARCH_FORWARD, SEARCH_BACKWARD, SEARCH_FORWARD_THEN_BACKWARD, SEARCH_BACKWARD_THEN_FORWARD, SEARCH_FORWARD_FROM_START, SEARCH_BACKWARD_FROM_END = range(6)

    # Used by wrapper code. Don't call directly.
    def __init__(self, factory):
        self.m_factory = factory

    # Returns the expression system associated with this call factory.
    # @return An NCExpressionSystem object.
    def GetExprSystem(self) -> NCExpressionSystem:
        return NCExpressionSystem(CSE.CallFactory_GetExprSystem(self.m_factory))

    # Checks whether a metacode is defined.
    # @param strMetacodeName The metacode name.
    # @return True iff the metacode is implemented.
    def IsMetacodeDefined(self, strMetacodeName : str) -> bool:
        return CSE.CallFactory_IsMetacodeDefined(self.m_factory, strMetacodeName)

    # Query the current NC program line index. This value is incremented by
    # calls to GetNextLine.
    # @return The current line index.
    def GetCurrentLineIndex(self) -> int:
        return CSE.CallFactory_GetCurrentLineIndex(self.m_factory)

    # Returns the next line of NC code. This is required for multi-line NC code where
    # contiguous NC statements are spread across multiple lines.
    # @return A string containing the next line of NC code.
    def GetNextLine(self) -> str:
        return CSE.CallFactory_GetNextLine(self.m_factory)

    # Reads an adjacent line of NC code. This doesn't progress the internal
    # line counter. The position of the requested line is specified by a line
    # offset which is relative to the current program line.
    # @param nLineOffset The line index offset relative to the current line.
    # @return A string containing the requested line of NC code.
    def PeekLine(self, nLineOffset : int) -> str:
        return CSE.CallFactory_PeekLine(self.m_factory, nLineOffset)

    # Checks whether this call factory is in scanning mode (used e.g. for CheckSyntax in NX CAM).
    # @return True iff scanning mode is being used.
    def IsScanning(self) -> bool:
        return CSE.CallFactory_IsScanning(self.m_factory)

    # Creates a label call. Labels are identified by their name and can be used as the target
    # of if and goto calls.
    # @param strLabel The label's name.
    def CreateLabelCall(self, strLabel : str):
        CSE.CallFactory_CreateLabelCall(self.m_factory, strLabel)

    # Creates an if call.
    # @param exprCondition An NC expression object that is evaluated at simulation runtime
    # to yield a boolean value that determines whether execution jumps to the specified target
    # label (True) or not (False).
    # @param exprTarget An NCExpression object that is evaluated at simulation runtime to
    # yield a string value that specifies the label name of the conditional jump's target.
    # @param enumSearchMode An enum specifying how to search for the target label in the
    # NC program code (using the enum definition at the top of this class).
    def CreateIfCall(self, exprCondition : NCExpression, exprTarget : NCExpression, enumSearchMode : int):
        if not isinstance(exprCondition, NCExpression) or not isinstance(exprTarget, NCExpression):
            raise CseTypeError
        CSE.CallFactory_CreateIfCall(self.m_factory, exprCondition.m_expr, exprTarget.m_expr, enumSearchMode)

    # Creates a nested if call. It skips blocks of code identified by a start and end label when looking
    # for the target label. This call is required for implementing nested control instructions (like for
    # or while statements).
    # @param exprCondition An NC expression object that is evaluated at simulation runtime
    # to yield a boolean value that determines whether execution jumps to the specified target
    # label (True) or not (False).
    # @param exprTarget An NCExpression object that is evaluated at simulation runtime to
    # yield a string value that specifies the label name of the conditional jump's target.
    # @param enumSearchMode An enum specifying how to search for the target label in the
    # NC program code (using the enum definition at the top of this class).
    # @param strStartBlockLabel The name of the block's start label.
    # @param strEndBlockLabel The name of the block's end label.
    def CreateNestedIfCall(self, exprCondition : NCExpression, exprTarget : NCExpression, enumSearchMode : int, strStartBlockLabel : str, strEndBlockLabel : str):
        if not isinstance(exprCondition, NCExpression) or not isinstance(exprTarget, NCExpression):
            raise CseTypeError
        CSE.CallFactory_CreateNestedIfCall(self.m_factory, exprCondition.m_expr, exprTarget.m_expr, enumSearchMode, strStartBlockLabel, strEndBlockLabel)

    # Creates a goto call.
    # @param exprTarget An NCExpression object that is evaluated at simulation runtime to
    # yield a string value that specifies the label name of the conditional jump's target.
    # @param enumSearchMode An enum specifying how to search for the target label in the
    # NC program code (using the enum definition at the top of this class).
    def CreateGotoCall(self,  exprTarget : NCExpression, enumSearchMode : int):
        if not isinstance(exprTarget, NCExpression):
            raise CseTypeError
        CSE.CallFactory_CreateGotoCall(self.m_factory, exprTarget.m_expr, enumSearchMode)

    # Creates a nested goto call (see CreateNestedIfCall).
    # @param exprTarget An NCExpression object that is evaluated at simulation runtime to
    # yield a string value that specifies the label name of the conditional jump's target.
    # @param enumSearchMode An enum specifying how to search for the target label in the
    # NC program code (using the enum definition at the top of this class).
    # @param strStartBlockLabel The name of the block's start label.
    # @param strEndBlockLabel The name of the block's end label.
    # @param bErrorInvalidTarget Specifies whether the system is supposed to throw an error
    # if the target label can't be found.
    def CreateNestedGotoCall(self, exprTarget : NCExpression, enumSearchMode : int, strStartBlockLabel : str, strEndBlockLabel : str, bErrorOnInvalidTarget : bool):
        if not isinstance(exprTarget, NCExpression):
            raise CseTypeError
        CSE.CallFactory_CreateNestedGotoCall(self.m_factory, exprTarget.m_expr, enumSearchMode, strStartBlockLabel, strEndBlockLabel, bErrorOnInvalidTarget)

    # Terminates execution of the current NC line. Used to implement NC machine skip levels which
    # are defined in the CSE options object.
    # @param nSuppressionLevel The suppression level which is associated with the corresponding
    # CSE option to determine whether the break call is executed or ignored.
    def CreateBreakCall(self, nSuppressionLevel : int):
        CSE.CallFactory_CreateBreakCall(self.m_factory, nSuppressionLevel)

    # Creates an execute call which executes all previous calls (including task planning and execution)
    # before proceeding.
    def CreateExecuteCall(self):
        CSE.CallFactory_CreateExecuteCall(self.m_factory)

    # Creates a variable declaration call which creates a new variable at simulation runtime
    # (i.e. it executes VariableManager.RegisterVariable internally).
    # @param exprVarName An NCExpression object that is evaluated at simulation runtime to
    # yield a string value that specifies the variable name.
    # @param enumVarType The variable's scalar type specified as an enum value from the NCBasicType enum definition.
    # @param enumVarAccessMode An enum value from the definition at the top of this class which specifies
    # the scope of this variable.
    # @param exprDefaultValue An NCExpression object that is evaluated at simulation runtime to
    # determine the variable's initial value.
    def CreateDeclareVariableCall(self, exprVarName : NCExpression, enumVarType : int, enumVarAccessMode : int, exprDefaultValue : NCExpression):
        if not isinstance(exprVarName, NCExpression) or not isinstance(exprDefaultValue, NCExpression):
            raise CseTypeError
        CSE.CallFactory_CreateDeclareVariableCall(self.m_factory, exprVarName.m_expr, enumVarType, enumVarAccessMode, exprDefaultValue.m_expr)

    # Creates an array variable declaration call which creates a new variable at simulation runtime.
    # @param exprVarName An NCExpression object that is evaluated at simulation runtime to
    # yield a string value that specifies the variable name.
    # @param arrayVarType An NCArrayType object that specifies the type of this variable.
    # @param enumVarAccessMode An enum value from the definition at the top of this class which specifies
    # the scope of this variable.
    def CreateDeclareArrayVariableCall(self, exprVarName : NCExpression, arrayVarType : NCArrayType, enumVarAccessMode : int):
        if not isinstance(exprVarName, NCExpression) or not isinstance(arrayVarType, NCArrayType):
            raise CseTypeError
        CSE.CallFactory_CreateDeclareArrayVariableCall(self.m_factory, exprVarName.m_expr, arrayVarType.m_nctype, enumVarAccessMode)

    # Creates a struct variable declaration call which creates a new variable at simulation runtime.
    # @param exprVarName An NCExpression object that is evaluated at simulation runtime to
    # yield a string value that specifies the variable name.
    # @param structVarType An NCStructType object that specifies the type of this variable.
    # @param enumVarAccessMode An enum value from the definition at the top of this class which specifies
    # the scope of this variable.
    def CreateDeclareStructVariableCall(self, exprVarName : NCExpression, structVarType : NCStructType, enumVarAccessMode : int):
        if not isinstance(exprVarName, NCExpression) or not isinstance(structVarType, NCStructType):
            raise CseTypeError
        CSE.CallFactory_CreateDeclareStructVariableCall(self.m_factory, exprVarName.m_expr, structVarType.m_nctype, enumVarAccessMode)

    # Creates an assignment call which assigns a new value to a variable at simulation runtime.
    # @param lvalue An NCLValue object that is associated to a modifiable object, typically a variable.
    # @param expr An NCExpression object that is evaluated at simulation runtime to determine the
    # new variable value.
    def CreateAssignCall(self, lvalue : NCLValue, expr : NCExpression):
        if not isinstance(lvalue, NCLValue) or not isinstance(expr, NCExpression):
            raise CseTypeError
        CSE.CallFactory_CreateAssignCall(self.m_factory, lvalue.m_expr, expr.m_expr)

    # Creates an assignment call which assigns a new value to an array object at simulation runtime.
    # @param exprLArray An NCArrayExpression object.
    # @param exprArray An NCArrayExpression object that is evaluated at simulation runtime to determine the
    # new array value.
    def CreateArrayAssignCall(self, exprLArray : NCArrayExpression, exprArray : NCArrayExpression):
        if not isinstance(exprLArray, NCArrayExpression) or not isinstance(exprArray, NCArrayExpression):
            raise CseTypeError
        CSE.CallFactory_CreateArrayAssignCall(self.m_factory, exprLArray.m_expr, exprArray.m_expr)

    # Creates an assignment call which assigns a new value to a struct object at simulation runtime.
    # @param exprLStruct An NCStructExpression object.
    # @param exprStruct An NCStructExpression object that is evaluated at simulation runtime to determine the
    # new struct value.
    def CreateStructAssignCall(self, exprLStruct : NCStructExpression, exprStruct : NCStructExpression):
        if not isinstance(exprLStruct, NCStructExpression) or not isinstance(exprStruct, NCStructExpression):
            raise CseTypeError
        CSE.CallFactory_CreateStructAssignCall(self.m_factory, exprLStruct.m_expr, exprStruct.m_expr)

    # Creates an assignment call which assigns a new value to an object at simulation runtime.
    # @param exprLObject An NCObjectExpression object.
    # @param exprObject An NCObjectExpression object that is evaluated at simulation runtime to determine the
    # new value.
    def CreateObjectAssignCall(self, exprLObject : NCObjectExpression, exprObject : NCObjectExpression):
        if not isinstance(exprLObject, NCObjectExpression) or not isinstance(exprObject, NCObjectExpression):
            raise CseTypeError
        CSE.CallFactory_CreateObjectAssignCall(self.m_factory, exprLObject.m_expr, exprObject.m_expr)

    # Creates a command call which executes a CSE command at simulation runtime. The command can be
    # implemented in CSE kernel or in Python where it is invoked through the Controller.ExecuteCommand
    # interface method.
    # @param strCommandName The command name.
    # @param listArgs A list of NCObjectExpression objects specifying the command arguments.
    def CreateCommandCall(self, strCommandName : str, listArgs : list):
        listArgsNC = []
        for arg in listArgs:
            listArgsNC.append(arg.m_expr)
        CSE.CallFactory_CreateCommandCall(self.m_factory, strCommandName, listArgsNC)

    # Creates a metacode call which executes a CSE metacode script at simulation runtime. The script
    # has to be implemented in the MCF/CCF.
    # @param strMetacodeName The metacode name.
    # @param dictArgs A map of NCObjectExpression objects specifying named metacode arguments.
    # @param listArgs A list of NCObjectExpression objects specifying unnamed metacode arguments.
    def CreateMetacodeCall(self, strMetacodeName : str, dictArgs : dict = {}, listArgs : list = [], bMustBeImplemented : bool = True):
        dictArgsNC = {}
        for strName, expr in dictArgs.items():
            dictArgsNC[strName] = expr.m_expr
        listArgsNC = []
        for arg in listArgs:
            listArgsNC.append(arg.m_expr)
        CSE.CallFactory_CreateMetacodeCall(self.m_factory, strMetacodeName, dictArgsNC, listArgsNC, bMustBeImplemented)

    # Creates a dynamic metacode call, i.e. its name is determined at simulation runtime.
    # @param exprMetacodeName An NCExpression object that is evaluated at simulation runtime to
    # yield a string value that specifies the metacode name.
    # @param dictArgs A map of NCObjectExpression objects specifying named metacode arguments.
    # @param listArgs A list of NCObjectExpression objects specifying unnamed metacode arguments.
    def CreateDynamicMetacodeCall(self, exprMetacodeName : NCExpression, dictArgs : dict = {}, listArgs : list = [], bMustBeImplemented : bool = True):
        if not isinstance(exprMetacodeName, NCExpression):
            raise CseTypeError
        dictArgsNC = {}
        for strName, expr in dictArgs.items():
            dictArgsNC[strName] = expr.m_expr
        listArgsNC = []
        for arg in listArgs:
            listArgsNC.append(arg.m_expr)
        CSE.CallFactory_CreateDynamicMetacodeCall(self.m_factory, exprMetacodeName.m_expr, dictArgsNC, listArgsNC, bMustBeImplemented)

    # Sets the call execution mode for sync calls.
    # @param enumCallExecutionMode The new call execution mode.
    def SetCallExecutionMode(self, enumCallExecutionMode : int):
        CSE.CallFactory_SetCallExecutionMode(self.m_factory, enumCallExecutionMode)

    # Returns the call execution mode for sync calls.
    # @return The current call execution mode.
    def GetCallExecutionMode(self) -> int:
        return CSE.CallFactory_GetCallExecutionMode(self.m_factory)

    # Creates a call that adds a sync call.
    # @param strCallName The name of the sync call.
    # @param exprCondition An NCExpression object that is evaluated at simulation runtime to determine
    # when the sync call will be executed.
    # @param enumSyncCallMode The type of the sync call.
    def CreateAddSyncCall(self, strCallName : str, exprCondition : NCExpression, enumSyncCallMode : int):
        if not isinstance(exprCondition, NCExpression):
            raise CseTypeError
        CSE.CallFactory_CreateAddSyncCall(self.m_factory, strCallName, exprCondition.m_expr, enumSyncCallMode)

    # Creates a call that removes a sync call.
    # @param strCallName The name of the sync call.
    def CreateRemoveSyncCall(self, strCallName : str):
        CSE.CallFactory_CreateRemoveSyncCall(self.m_factory, strCallName)



# This class implements a controller for the CSE engine. It contains methods which are
# called by CSE kernel to fulfil tasks like NC code parsing or command and method execution.
class Controller:
    # Used by wrapper code. Don't call directly.
    def __init__(self, delegate):
        self.m_delegate = delegate

    def Initialize(self, value, typeSys):
        initMethod = getattr(self.m_delegate, "Initialize", None)
        if initMethod == None:
            return True

        return initMethod(NCTypeSystem(typeSys))

    def IsConvertValueImplemented(self) -> bool:
        return hasattr(self.m_delegate, "ConvertValue")

    def ConvertValue(self, value, nTargetType : int, valueFactory):
        convMethod = getattr(self.m_delegate, "ConvertValue", None)
        if convMethod == None:
            return None

        convValue = convMethod(NCValue(value), nTargetType, NCValueFactory(valueFactory))
        if convValue == None:
            return None

        return convValue.m_obj

    # Called by CSE kernel to parse a line of NC code. The task of this method is to
    # translate NC code into a list of calls which are created using the CallFactory
    # interface. It is typically called during NC program execution.
    # @param strLine A line of NC code.
    # @param factory A CallFactory object.
    # @return True iff parsing was successful.
    def ParseNCLine(self, strLine : str, factory) -> bool:
        try:
            return self.m_delegate.ParseNCLine(strLine, CallFactory(factory))
        except CseParseError:
            return False

    # Called by CSE kernel to parse an NC code expression. The task of this method is to
    # translate NC code into an NCExpression object using the NCExpressionSystem interface.
    # It is typically called from the application UI for diagnostic purposes.
    # @param strExpr A string containing an NC code expression.
    # @param exprsys An NCExpressionSystem object.
    # @return A string containing the result of expression evaluation.
    def ParseNCExpression(self, strExpr : str, exprsys) -> str:
        try:
            return self.m_delegate.ParseNCExpression(strExpr, NCExpressionSystem(exprsys)).m_expr
        except CseParseError:
            return None

    # Called by CSE kernel to execute a controller specific command. It is invoked during
    # metacode execution.
    # @param strCommandName The command name.
    # @param listArgs A list of NCObjectExpression objects specifying the command arguments.
    # @param state A pointer to the channel state which provides the context for this command.
    # @return True if command execution was successful. None if the command is not implemented.
    # Otherwise False.
    def ExecuteCommand(self, strCommandName : str, listArgs : list, state) -> bool:
        listArgsNC = []
        for arg in listArgs:
            kind = CSE.Object_GetKind(arg)
            if kind == NCObject.KIND_VALUE:
                listArgsNC.append(NCValue(arg))
            elif kind == NCObject.KIND_ARRAY:
                listArgsNC.append(NCArray(arg))
            else:
                listArgsNC.append(NCStruct(arg))
        return self.m_delegate.ExecuteCommand(strCommandName, listArgsNC, ChannelState(state))

    # Checks whether a metacode exists.
    # @param strMetacodeName The metacode's name.
    # @return True iff the given metacode exists.
    def HasMetacode(self, strMetacodeName : str) -> bool:
        mcMethod = getattr(self.m_delegate, "HasMetacode", None)
        if mcMethod == None:
            return False
        return mcMethod(strMetacodeName)

    # Checks whether a meta code parameter name is registered with a given metacode.
    # @param strMetaCodeName Meta code to search in.
    # @param strMCParamName Meta code parameter to be searched for.
    # @return True iff the given parameter is registered.
    def HasMCParameter(self, strMetacodeName : str, strMCParamName : str) -> bool:
        mcMethod = getattr(self.m_delegate, "HasMCParameter", None)
        if mcMethod == None:
            return False
        return mcMethod(strMetacodeName, strMCParamName)

    def ExecuteMetacode(self, strMetacodeName, dictArgs, listArgs, state):
        mcMethod = getattr(self.m_delegate, "ExecuteMetacode", None)
        if mcMethod == None:
            return None

        dictArgsNC = {}
        for strName, arg in dictArgs.items():
            kind = CSE.Object_GetKind(arg)
            if kind == NCObject.KIND_VALUE:
                dictArgsNC[strName] = NCValue(arg)
            elif kind == NCObject.KIND_ARRAY:
                dictArgsNC[strName] = NCArray(arg)
            else:
                dictArgsNC[strName] = NCStruct(arg)

        listArgsNC = []
        for arg in listArgs:
            kind = CSE.Object_GetKind(arg)
            if kind == NCObject.KIND_VALUE:
                listArgsNC.append(NCValue(arg))
            elif kind == NCObject.KIND_ARRAY:
                listArgsNC.append(NCArray(arg))
            else:
                listArgsNC.append(NCStruct(arg))

        try:
            return mcMethod(strMetacodeName, dictArgsNC, listArgsNC, ChannelState(state))
        except (CSE.CommandError, CSE.MethodError):
            return False

    # Checks whether a method exists.
    # @param strMethodName The method's name.
    # @return True iff the given method exists.
    def HasMethod(self, strMethodName : str) -> bool:
        return self.m_delegate.HasMethod(strMethodName)

    # Query a method's return type.
    # @param strMethodName The method's name.
    # @param exprsys An NCExpressionSystem object.
    # @return An NCType object (the wrapper returns its Python capsule).
    def GetMethodType(self, strMethodName : str, exprsys):
        return self.m_delegate.GetMethodType(strMethodName, NCExpressionSystem(exprsys)).m_nctype

    # Called by CSE kernel to execute a controller specific method. This is typically invoked during
    # expression evaluation, metacode execution or from specific entry points in CSE kernel (e.g. to
    # determine the location of an inline subprogram).
    # @param strMethodName The method name.
    # @param listArgs A list of NCObjectExpression objects specifying the command arguments.
    # @param exprsys An NCExpressionSystem object which provides the context for this method.
    # @return An NC object which contains the return value of this method (the wrapper returns its
    # Python capsule).
    def ExecuteMethod(self, strMethodName : str, listArgs : list, exprsys):
        listArgsNC = []
        for arg in listArgs:
            kind = CSE.Object_GetKind(arg)
            if kind == NCObject.KIND_VALUE:
                listArgsNC.append(NCValue(arg))
            elif kind == NCObject.KIND_ARRAY:
                listArgsNC.append(NCArray(arg))
            else:
                listArgsNC.append(NCStruct(arg))
        result = self.m_delegate.ExecuteMethod(strMethodName, listArgsNC, NCExpressionSystem(exprsys))
        if result != None:
            return result.m_obj
        return None

    # Creates a new controller state object which can be used to hold controller specific data.
    # @param state A ChannelState object for the associated machine channel.
    # @return The new controller state object. This can be an instance of any Python class.
    # CSE treats this as a black box.
    def InitializeChannel(self, state):
        return self.m_delegate.InitializeChannel(ChannelState(state))

    # Clones a controller state object. This is called whenever a copy of the complete channel state
    # has to be created (e.g. for CSE lookahead).
    # @param channelobj The original controller state object.
    # @param state A ChannelState object for the associated machine channel.
    # @return The cloned controller state object.
    def CloneChannel(self, channelobj, state):
        return self.m_delegate.CloneChannel(channelobj, ChannelState(state))
