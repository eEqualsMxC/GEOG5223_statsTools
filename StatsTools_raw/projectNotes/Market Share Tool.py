import arcpy

# Input variables 
point_feature = arcpy.GetParameterAsText(0)
polygon_feature = arcpy.GetParameterAsText(1)
field_for_join = arcpy.GetParameterAsText(2)
old_area = arcpy.GetParameter(3)
data_table_polygons = arcpy.GetParameterAsText(4)
table_field_for_join = arcpy.GetParameterAsText(5)
population_field = arcpy.GetParameterAsText(6)
in_number_of_classes = arcpy.GetParameterAsText(7)
in_output = arcpy.GetParameterAsText(8)
type_of_map = arcpy.GetParameterAsText(9)

# Creates the thiessen polygons
arcpy.env.overwriteOutput = True
out_thiessen = arcpy.env.scratchGDB+'/thiessen'
arcpy.env.extent = polygon_feature
arcpy.CreateThiessenPolygons_analysis(point_feature,out_thiessen,'ALL')

# Intersects with the thiessen polygons 
arcpy.analysis.Intersect([out_thiessen, polygon_feature], 'intersect', 'ALL')

# Joins the intersected with the data table
arcpy.management.JoinField('intersect', field_for_join, data_table_polygons, table_field_for_join)
arcpy.management.AddField('intersect', "POP_RATIO", 'DOUBLE')

# Calculates the new field created
with arcpy.da.UpdateCursor('intersect', ["POP_RATIO", 'Shape_Area', str(population_field),str(old_area)]) as cursor:
    for row in cursor:
        row[0] = row[1] * (row[2]/row[3])
        cursor.updateRow(row)

# Dissolve the layer using the names from point feature
arcpy.management.Dissolve('intersect', 'Dissolved', ['Input_FID','NAME'],[["POP_RATIO","SUM"]],"MULTI_PART")

# Adds a new field for percent of market share
arcpy.management.AddField('Dissolved', "Market_Share", 'DOUBLE')

# Calculates the percent field
total_pop = 0
with arcpy.da.SearchCursor('Dissolved', ['SUM_POP_RATIO']) as cursor:
    for row in cursor:
        total_pop = total_pop+row[0]

with arcpy.da.UpdateCursor('Dissolved', ["Market_Share", 'SUM_POP_RATIO']) as cursor:
    for row in cursor:
        row[0] = (row[1]/total_pop)*100
        cursor.updateRow(row)

arcpy.CopyFeatures_management('Dissolved', in_output)

aprx = arcpy.mp.ArcGISProject('current')

layer = aprx.activeMap.addDataFromPath(in_output)
fileName = in_output.split('\\')[-1]
layer = aprx.activeMap.listLayers(fileName[0:fileName.find('.')])[0]

# Create the symbology Graducated color map type or Graduated symbols
symbology = layer.symbology
if type_of_map == 'Graduated Colors':
    symbology.updateRenderer('SimpleRenderer')
    symbology.updateRenderer('GraduatedColorsRenderer')
    symbology.renderer.classificationField = "Market_Sha"
    symbology.renderer.breakCount = int(in_number_of_classes)
    symbology.renderer.colorRamp = aprx.listColorRamps('Greens (Continuous)')[0]
    layer.symbology = symbology
elif type_of_map == 'Graduated Symbols':
    symbology.updateRenderer('GraduatedSymbolsRenderer')
    symbology.renderer.classificationField = 'SUM_POP_RA'
    symbology.renderer.breakCount = int(in_number_of_classes)
    symbology.renderer.minimumSymbolSize = 5
    symbology.renderer.maximumSymbolSize = 20
    layer.symbology = symbology