import arcpy


#########################   Input   ###################################
in_features_point = arcpy.GetParameterAsText(0)
in_features_polygon = arcpy.GetParameterAsText(1)
in_field_join_features = arcpy.GetParameterAsText(2)
in_field_oldarea = arcpy.GetParameterAsText(3)
in_table_population = arcpy.GetParameterAsText(4)
in_table_field_join = arcpy.GetParameterAsText(5)
in_table_field_population = arcpy.GetParameterAsText(6)
in_num_classes = int(arcpy.GetParameterAsText(7))

out_features_marketshare = arcpy.GetParameterAsText(8)
in_map_type = arcpy.GetParameterAsText(9) # (arcpy.GetParameterAsText(9) == "Graduated Colors")


############################ Settings #################################

arcpy.env.overwriteOutput = True

############################# Messages #################################


arcpy.AddMessage('''Here are the specified -
    \tParmeter 1: {0}
    \tParmeter 2: {1}
    \tParmeter 3: {2}
    \tParmeter 4: {3}
    \tParmeter 5: {4}
    \tParmeter 6: {5}
    \tParmeter 7: {6}
    \tNumber of Classes 8: {7}
    \tOutput features 9: {8}
    \tMap Type: {9}'''\
    .format(in_features_point,in_features_polygon,in_field_join_features,in_field_oldarea,in_table_population,in_table_field_join,in_table_field_population,in_num_classes,out_features_marketshare,in_map_type)
    )

# Enviroment
out_features_buffer = arcpy.env.scratchGDB + '/lib_MarketShare'

# set input and output variables
in_features = in_features_point
out_features = 'thiessen'
out_fields = 'ALL'

# run the tool
t_polygons = arcpy.CreateThiessenPolygons_analysis(in_features, out_features, out_fields)


# Intersect features 
feature_Intersect_list = [t_polygons,in_features_polygon]

arcpy.analysis.Intersect(feature_Intersect_list, out_features_marketshare)


# Join Features
out_join_features = "intersect_pop_join"
arcpy.JoinField_management(out_features_marketshare, in_field_join_features,in_table_population,in_table_field_join,in_table_field_population)

cursor = arcpy.da.SearchCursor(out_features_marketshare,["Shape_Area","Area","P001001"])

total_service = 0
for row in cursor:    
    pop = row[0]/row[1]*row[2]    
    total_service += pop

cursor = arcpy.da.SearchCursor(in_table_population, [in_table_field_population])
total_pop = 0
cursor.reset()

for row in cursor:
    total_pop += row[0]

arcpy.AddMessage("Total Pop: {total_pop}")










lyr0 = out_features_marketshare


layerName = (out_features_marketshare.split("\\")[-1])  
layerName = layerName[0:layerName.find('.')]

layer = aprx.activeMap.listLayers(layerName)[0]

layer.name = f"{layer.name}_PropSymbols"



symbology = layer.symbology
symbology.updateRenderer('GraduatedSymbolsRenderer')
symbology.renderer.classificationField = in_field_numerical
symbology.renderer.breakCount = in_num_classes
symbology.renderer.minimumSymbolSize = 5
symbology.renderer.maximumSymbolSize = 20

layer.symbology = symbology



labelNums = []
for brk in symbology.renderer.classBreaks:
    number0 = brk.label.split("-")[0]
    number1 = brk.label.split("-")[1]
    labelNums.append(int(number0))
    labelNums.append(int(number1))


color = [randrange(0,255),randrange(0,255),randrange(0,255)] + [100]
labelQuantile = int(max(labelNums) / in_num_classes)

labelNums2 = []
for num in range(0,in_num_classes + 1):
    labelNums2.append(num * labelQuantile)

i = 0

if in_boolean_user_friendly is True:  
    for brk in symbology.renderer.classBreaks:

        if i == 0:
            temp = labelNums2[1]
            brk.upperBound = temp
            brk.label = f"Less than {temp}"
            brk.symbol.color = {'RGB': color }
            i = i+1
        
        else:
            brk.upperBound = labelNums2[i]
            temp = f"{labelNums2[i-1]} - {labelNums2[i]}"
            brk.label = temp
            brk.symbol.color = {'RGB': color }
    
        i = i + 1

else:

    for brk in symbology.renderer.classBreaks:

            temp = labelNums2[i+1]
            brk.upperBound = temp
            brk.label = temp
            brk.symbol.color = {'RGB': color }
            i = i + 1

        
layer.symbology = symbology