import arcpy
import numpy as np


# **************************** Parameters ***************************************

input_layer = arcpy.GetParameterAsText(0)
field_for_analysis = arcpy.GetParameterAsText(1)
type_analysis = arcpy.GetParameterAsText(2)
color_scheme = arcpy.GetParameterAsText(3)
output =  arcpy.GetParameterAsText(4)
map_symbology = "Graduated"

arcpy.AddMessage('''Here are the specified -,
    \tParameter 1: {0}
    \tParameter 2: {1}
    \tParameter 3: {2}
    \tParameter 4: {3}
    \tOutput features: {4}'''\
    .format(input_layer,field_for_analysis,type_analysis,map_symbology,output)
    )


arcpy.AddMessage('''Environments-
    \tWorkspace:{0}
    \tOverwrite:{1}
    \tScratchGDB:{2}
    \tPackageworkspace:{3}'''\
    .format(arcpy.env.workspace,arcpy.env.overwriteOutput,\
        arcpy.env.scratchGDB,arcpy.env.packageWorkspace))

#enviroment
arcpy.env.overwriteOutput = True
arcpy.CopyFeatures_management(input_layer,output)

# ******************* Helper Functions ****************************

def import_column_data(shp_data,column):
    """
    Simple function to import field Columns and convert to an array.

    Parameter 1:

        shp_data (string): Must be a path to a shp file. 

    Parameter 2: 

        column (string): Field name for analysis.

    Return:

        numpy array {Columns = 1, Rows = N} 
    """
    raw_data = []

    with arcpy.da.SearchCursor(shp_data,[f"{column}"]) as search_cursor:
        for row in search_cursor:
            raw_data.append(list(row))   
    return np.array(raw_data)


# function to check for uniquie id value and return the unique id name.
def unique_id(shp_data):

    # Locate all current field names 
    desc = arcpy.Describe(shp_data)
    field_names = [f.name for f in desc.fields]

    unique_name = "fragile_id"

    if unique_name not in field_names:

        arcpy.management.AddField(shp_data,unique_name,"LONG")

        id_num = 1
        with arcpy.da.UpdateCursor(shp_data, [unique_name]) as update_cursor:
            for row in update_cursor:
                row[0] = id_num
                update_cursor.updateRow(row)
                id_num += 1

    return unique_name


# ******************************** Mean Analaysis ************************

# Function to calculate above or bellow the mean.
def mean_analysis(_input_layer,_field_for_analysis,_map_symbology,type_analysis):

    field_values = import_column_data(_input_layer,_field_for_analysis)
    field_mean = round(field_values.mean(),3)
    median = round(np.median(field_values),3)
    analysis_string = None
    

    mean_values = []
    below_mean = 0
    above_mean = 0

    if type_analysis == "above mean":
        analysis_string = f"{_field_for_analysis}_AboveMean"
        # iterate field for analysis and locate all values above the mean.
        with arcpy.da.SearchCursor(
            _input_layer,[f"{unique_id(_input_layer)}",f"{_field_for_analysis}"]) as search_cursor:

            for row in search_cursor:
                
                if row[1] >= field_mean:
                    mean_values.append([row[0],row[1]])
                    above_mean += 1
                    
                else:
                    mean_values.append([row[0],0])
                    below_mean += 1

        total = above_mean + below_mean

        pct_abm = round((above_mean/total),3)
        arcpy.AddMessage('''\n
                            \t***** Mean Analysis *****
                            \tMean: {0}
                            \tMeadian: {1}
                            \tNumber of values above the mean: {2}
                            \tPercent of {3} above the mean: {4}\n\n'''\
                            .format(field_mean,median,above_mean,_field_for_analysis,pct_abm))


    else:

        analysis_string = f"{_field_for_analysis}_BelowMean"
        # iterate field for analysis and locate all values below the mean.
        with arcpy.da.SearchCursor(
            _input_layer,[f"{unique_id(_input_layer)}",f"{_field_for_analysis}"]) as search_cursor:

            for row in search_cursor:
                
                if row[1] <= field_mean:
                    mean_values.append([row[0],row[1]])
                    above_mean += 1
                    
                else:
                    mean_values.append([row[0],0])
                    below_mean += 1


        total = above_mean + below_mean
        pct_bm = round((below_mean/total),3)
        arcpy.AddMessage('''\n
                            \t***** Mean Analysis *****
                            \tMean: {0}
                            \tMeadian: {1}
                            \tNumber of values below the mean: {2}
                            \tPercent of {3} below the mean: {4}\n\n'''\
                            .format(field_mean,median,below_mean,_field_for_analysis,pct_bm))


    # Add new field for analysis type
    arcpy.management.AddField(_input_layer,analysis_string,"FLOAT")

    # iterate new field and insert new mean above or bellow values.
    for row_xy in mean_values:
        
        where_clause = """"{}"={}""".format('fragile_id',row_xy[0])
        
        with arcpy.da.UpdateCursor(_input_layer, ['fragile_id', f'{analysis_string}'],
                                    where_clause=where_clause) as cursor:
            
            for row in cursor:
                row[1] = row_xy[1]
                cursor.updateRow(row)
        
    
    return analysis_string


# ******************************** 1 STD  Analysis ******************

def STD1_analysis(_input_layer,_field_for_analysis,_map_symbology,type_analysis):

    analysis_string = None
    field_values = import_column_data(_input_layer,_field_for_analysis)
    field_mean = round(field_values.mean(),3)
    field_1Std = round(field_values.std(),3)
    
    # calculate 1 Std 
    right_tail = field_mean - field_1Std
    left_tail = field_mean + field_1Std

    # List object to collect values
    std_values = []

    # Variables to report in Messages
    within = 0
    outside = 0

    
    analysis_string = f"{_field_for_analysis}_within_1STD"
    # iterate field for analysis and locate all values with in 1 std of the mean.
    with arcpy.da.SearchCursor(
        _input_layer,[f"{unique_id(_input_layer)}",f"{_field_for_analysis}"]) as search_cursor:

        for row in search_cursor:
            
            if row[1] > right_tail and row[1] < left_tail:
                std_values.append([row[0],row[1]])
                within += 1
                
            else:
                std_values.append([row[0],0])
                outside += 1
    
        
    
    # Add new field for analysis type
    arcpy.management.AddField(_input_layer,analysis_string,"FLOAT")

    # iterate new field and insert new mean above or bellow values.
    for row_xy in std_values:
        
        where_clause = """"{}"={}""".format('fragile_id',row_xy[0])
        
        with arcpy.da.UpdateCursor(_input_layer, ['fragile_id', f'{analysis_string}'],
                                    where_clause=where_clause) as cursor:
            
            for row in cursor:
                row[1] = row_xy[1]
                cursor.updateRow(row)

    
    # Messages
    arcpy.AddMessage('''\n
                            \t***** Mean Analysis *****
                            \tMean: {0}
                            \t1 STD: {1}
                            \tRight tail: {2}
                            \tLeft Tail: {3}
                            \tQty within 1 STD: {4}\n\n'''\
                            .format(field_mean, field_1Std, right_tail, left_tail, within))

    
    return analysis_string

# ******************************** Outliers  Analysis ******************

def outliers_analysis(_input_layer,_field_for_analysis,_map_symbology,type_analysis):

    analysis_string = None
    field_values = import_column_data(_input_layer,_field_for_analysis)
    Q3, Q1 = np.percentile(field_values, [75 ,25])

    high_outlier_range = Q3 + (1.5 * (Q3 - Q1))
    low_outlier_range = Q3 - (1.5 * (Q3 - Q1))

    outlier_values = []
    high_outliers = 0 
    low_outliers = 0
    not_outlier = 0
    IQR_outliers = 0
    outlier_ids = []
 
    # analysis_string = f"{_field_for_analysis}_outliers"

    # iterate field for analysis and locate all values with in 1 std of the mean.
    with arcpy.da.SearchCursor(
        _input_layer,[f"{unique_id(_input_layer)}",f"{_field_for_analysis}"]) as search_cursor:
        
        if type_analysis == "High Outliers":
            analysis_string = f"{_field_for_analysis}_HighOutlierValues"

            for row in search_cursor:
                
                if row[1] >= high_outlier_range:
                    outlier_values.append([row[0],row[1]])
                    outlier_ids.append(row[0])
                    high_outliers += 1
                    
                else:
                    outlier_values.append([row[0],0])
                    not_outlier += 1

        elif type_analysis == "Low Outliers":
            analysis_string = f"{_field_for_analysis}_LowOutlierValues"

            for row in search_cursor:

                if row[1] <= low_outlier_range:
                    outlier_values.append([row[0],row[1]])
                    outlier_ids.append(row[0])
                    low_outliers += 1
                    
                else:
                    outlier_values.append([row[0],0])
                    not_outlier += 1

        elif type_analysis == "IQR":
            analysis_string = f"{_field_for_analysis}_WithinIQR"

            for row in search_cursor:

                if row[1] < high_outlier_range and row[1] > low_outlier_range:
                    outlier_values.append([row[0],row[1]])
                    outlier_ids.append(row[0])
                    IQR_outliers += 1
                    
                else:
                    outlier_values.append([row[0],0])
                    not_outlier += 1

        else:

            analysis_string = f"{_field_for_analysis}_OutlierValues"

            for row in search_cursor:
                
                if row[1] >= high_outlier_range:
                    outlier_values.append([row[0],row[1]])
                    outlier_ids.append(row[0])
                    high_outliers += 1
                
                elif row[1] <= low_outlier_range:
                    outlier_values.append([row[0],row[1]])
                    outlier_ids.append(row[0])
                    low_outliers += 1
                    
                else:
                    outlier_values.append([row[0],0])
                    not_outlier += 1
    
    # Add new field for analysis type
    arcpy.management.AddField(_input_layer,analysis_string,"FLOAT")

    # iterate new field and insert new mean above or bellow values.
    for row_xy in outlier_values:
        
        where_clause = """"{}"={}""".format('fragile_id',row_xy[0])
        
        with arcpy.da.UpdateCursor(_input_layer, ['fragile_id', f'{analysis_string}'],
                                    where_clause=where_clause) as cursor:
            
            for row in cursor:
                row[1] = row_xy[1]
                cursor.updateRow(row)


    # Todo Add Messages

    
    return analysis_string


# ************************* Code inits here ********************


fieldname = None

if type_analysis == "above mean" or  type_analysis == "below mean":

    fieldname = mean_analysis(output,field_for_analysis,map_symbology,type_analysis)

elif type_analysis == "1-STD":

    fieldname = STD1_analysis(output,field_for_analysis,map_symbology,type_analysis)

else:
    fieldname = outliers_analysis(output,field_for_analysis,map_symbology,type_analysis)


aprx = arcpy.mp.ArcGISProject('CURRENT')
lyr0 = aprx.activeMap.addDataFromPath(output)
fileName = output.split('\\')[-1]
layer = aprx.activeMap.listLayers(lyr0)[0]





# Create the symbology Graducated color map type or Graduated symbols
symbology = layer.symbology
if map_symbology == 'Graduated':
    symbology.updateRenderer('SimpleRenderer')
    symbology.updateRenderer('GraduatedColorsRenderer')
    symbology.renderer.classificationField = fieldname
    # symbology.renderer.breakCount = int(3)

    # Force Discreate Color Scheme
    if type_analysis == "IQR":
        symbology.renderer.colorRamp = aprx.listColorRamps()[0]
    
    else:
        # User Color Scheme 
        symbology.renderer.colorRamp = aprx.listColorRamps(color_scheme)[0]
        
    layer.symbology = symbology








