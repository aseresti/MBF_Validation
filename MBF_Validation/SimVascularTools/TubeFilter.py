import vtk
import numpy as np
from vtk.util.numpy_support import vtk_to_numpy

def create_tube(centerline_points, tube_radius):
    # Create VTK points
    vtk_points = vtk.vtkPoints()
    for point in centerline_points:
        vtk_points.InsertNextPoint(point)

    # Create a polyline from the points
    polyline = vtk.vtkPolyLine()
    polyline.GetPointIds().SetNumberOfIds(len(centerline_points))
    for i, point in enumerate(centerline_points):
        polyline.GetPointIds().SetId(i, i)

    # Create a polydata object
    polydata = vtk.vtkPolyData()
    polydata.SetPoints(vtk_points)
    polydata.GetLines().InsertNextCell(polyline)

    # Create a tube filter
    tube_filter = vtk.vtkTubeFilter()
    tube_filter.SetInputData(polydata)
    tube_filter.SetRadius(tube_radius)  # Larger than lumen radius
    tube_filter.SetNumberOfSides(50)
    tube_filter.Update()

    return tube_filter.GetOutput()


def mask_gradient_image(tube, gradient_image):
    # Create a stencil to mask the gradient image
    stencil = vtk.vtkPolyDataToImageStencil()
    stencil.SetInputData(tube)
    stencil.SetOutputSpacing(gradient_image.GetSpacing())
    stencil.SetOutputOrigin(gradient_image.GetOrigin())
    stencil.SetOutputWholeExtent(gradient_image.GetExtent())
    stencil.Update()

    # Apply the stencil to the gradient image
    stencil_filter = vtk.vtkImageStencil()
    stencil_filter.SetInputData(gradient_image)
    stencil_filter.SetStencilConnection(stencil.GetOutputPort())
    stencil_filter.ReverseStencilOff()
    stencil_filter.Update()

    return stencil_filter.GetOutput()


def detect_lumen_radius(masked_gradient_image, centerline_points):
    # Convert the gradient image to a NumPy array
    dims = masked_gradient_image.GetDimensions()
    spacing = masked_gradient_image.GetSpacing()
    origin = masked_gradient_image.GetOrigin()

    gradient_array = vtk_to_numpy(masked_gradient_image.GetPointData().GetScalars())
    gradient_array = gradient_array.reshape(dims, order="F")

    lumen_radii = []
    for point in centerline_points:
        # Map the centerline point to voxel space
        voxel_coords = [int((p - o) / s) for p, o, s in zip(point, origin, spacing)]

        # Extract the radial gradient around the point
        z, y, x = voxel_coords
        radial_gradient = gradient_array[z, y-10:y+10, x-10:x+10]  # Adjust the search window
        max_gradient_index = np.argmax(radial_gradient)
        radius = np.sqrt((max_gradient_index - 10) ** 2) * spacing[0]  # Convert to physical space
        lumen_radii.append(radius)

    return lumen_radii

def create_lumen_mask(centerline_points, lumen_radii, dims, spacing, origin):
    lumen_mask = np.zeros(dims, dtype=np.uint8)

    for point, radius in zip(centerline_points, lumen_radii):
        voxel_coords = [int((p - o) / s) for p, o, s in zip(point, origin, spacing)]
        z, y, x = voxel_coords

        # Mark the region within the radius as lumen
        for i in range(-int(radius), int(radius) + 1):
            for j in range(-int(radius), int(radius) + 1):
                if (i**2 + j**2) <= radius**2:
                    lumen_mask[z, y + i, x + j] = 1

    return lumen_mask

def Read_vtk_image(image_location):
    reader = vtk.vtkStructuredPointsReader()
    reader.SetFileName(image_location)
    reader.ReadAllVectorsOn()
    reader.ReadAllScalarsOn()
    reader.Update()

    return reader.GetOutput()

def save_lumen_mask_as_vtp(lumen_mask, output_path, spacing=(1, 1, 1), origin=(0, 0, 0)):
    """
    Save the lumen mask as a .vtp file.

    Parameters:
        lumen_mask (np.ndarray): 3D NumPy array (binary mask).
        output_path (str): Path to save the .vtp file.
        spacing (tuple): Spacing of the image in physical space.
        origin (tuple): Origin of the image in physical space.
    """
    # Create vtkPoints for all points in the mask where value == 1
    vtk_points = vtk.vtkPoints()
    dims = lumen_mask.shape
    for z in range(dims[0]):
        for y in range(dims[1]):
            for x in range(dims[2]):
                if lumen_mask[z, y, x] == 1:
                    # Convert voxel coordinates to physical space
                    px = origin[0] + x * spacing[0]
                    py = origin[1] + y * spacing[1]
                    pz = origin[2] + z * spacing[2]
                    vtk_points.InsertNextPoint(px, py, pz)

    # Create a vtkPolyData object
    polydata = vtk.vtkPolyData()
    polydata.SetPoints(vtk_points)

    # Optionally, add scalar values (e.g., binary mask values)
    mask_values = vtk.vtkUnsignedCharArray()
    mask_values.SetName("Mask")
    mask_values.SetNumberOfComponents(1)
    mask_values.SetNumberOfTuples(vtk_points.GetNumberOfPoints())
    for _ in range(vtk_points.GetNumberOfPoints()):
        mask_values.InsertNextValue(1)  # All points have value 1
    polydata.GetPointData().SetScalars(mask_values)

    # Write to .vtp file
    writer = vtk.vtkXMLPolyDataWriter()
    writer.SetFileName(output_path)
    writer.SetInputData(polydata)
    writer.Write()

def save_lumen_mask_as_vtp_with_polyline(lumen_mask, output_path, spacing=(1, 1, 1), origin=(0, 0, 0)):
    """
    Save lumen mask as a .vtp file with polyline connectivity.
    
    Parameters:
        lumen_mask (np.ndarray): 3D NumPy array (binary mask).
        output_path (str): Path to save the .vtp file.
        spacing (tuple): Spacing of the image in physical space.
        origin (tuple): Origin of the image in physical space.
    """
    # Create vtkPoints for all points in the mask where value == 1
    vtk_points = vtk.vtkPoints()
    dims = lumen_mask.shape
    point_ids = []
    for z in range(dims[0]):
        for y in range(dims[1]):
            for x in range(dims[2]):
                if lumen_mask[z, y, x] != 0:
                    # Convert voxel coordinates to physical space
                    px = origin[0] + x * spacing[0]
                    py = origin[1] + y * spacing[1]
                    pz = origin[2] + z * spacing[2]
                    point_id = vtk_points.InsertNextPoint(px, py, pz)
                    point_ids.append(point_id)

    # Create a polyline to connect the points
    polyline = vtk.vtkPolyLine()
    polyline.GetPointIds().SetNumberOfIds(len(point_ids))
    for i, pid in enumerate(point_ids):
        polyline.GetPointIds().SetId(i, pid)

    # Create a cell array to store the polyline
    cells = vtk.vtkCellArray()
    cells.InsertNextCell(polyline)

    # Create a polydata object
    polydata = vtk.vtkPolyData()
    polydata.SetPoints(vtk_points)
    polydata.SetLines(cells)

    # Optionally, add scalar values
    mask_values = vtk.vtkUnsignedCharArray()
    mask_values.SetName("Mask")
    mask_values.SetNumberOfComponents(1)
    mask_values.SetNumberOfTuples(len(point_ids))
    for _ in point_ids:
        mask_values.InsertNextValue(1)
    polydata.GetPointData().SetScalars(mask_values)

    # Write to .vtp file
    

def Write_vtk_image(Image,output_path):
    writer = vtk.vtkDataSetWriter()#vtkXMLImageDataWriter()
    writer.SetFileName(output_path)
    writer.SetInputData(Image)
    writer.Write()

def Write_vtp(polydata, output_path):
    writer = vtk.vtkXMLPolyDataWriter()
    writer.SetFileName(output_path)
    writer.SetInputData(polydata)
    writer.Write()

def SphereClip(volume_image,center,radius):
    sphere = vtk.vtkSphere()
    sphere.SetCenter(center)
    sphere.SetRadius(radius)

    clipper = vtk.vtkClipDataSet()
    clipper.SetInputData(volume_image)
    clipper.SetClipFunction(sphere)
    clipper.InsideOutOn()
    clipper.GetOutputInformation(1)
    clipper.Update()

    SphereOutput = clipper.GetOutput()#.GetPointData().GetArray("Magnitude")

    return SphereOutput

def AppendVolume(volume1, volume2):

    append_filter = vtk.vtkAppendFilter()
    append_filter.AddInputData(volume1)
    append_filter.AddInputData(volume2)
    append_filter.Update()

    return append_filter.GetOutput()

def WriteVTUFile(FileName,Data):
	writer=vtk.vtkXMLUnstructuredGridWriter()
	writer.SetFileName(FileName)
	writer.SetInputData(Data)
	writer.Update()

def ThresholdByUpper(Volume,arrayname,value):
	Threshold=vtk.vtkThreshold()
	Threshold.SetInputData(Volume)
	Threshold.ThresholdByUpper(value)
	Threshold.SetInputArrayToProcess(0,0,0,"vtkDataObject::FIELD_ASSOCIATION_POINTS",arrayname)
	Threshold.Update()
	return Threshold.GetOutput()