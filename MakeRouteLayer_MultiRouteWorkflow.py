# Emily Pitman
# UWT - MSGT Capstone
# Name: MakeRouteLayer_MultiRouteWorkflow.py
# Description: Calculate the origin-destination routes for a set of riders and
#              save the outputs to feature classes.
# Requirements: Network Analyst Extension

# Import system modules
import arcpy
from arcpy import env
import pandas as pd
import csv
import datetime

field_names = ['ObjectID', 'ParentGlobalID', 'x', 'y']

try:
    # Check out the Network Analyst extension license
    arcpy.CheckOutExtension("Network")

    # Set environment settings
    env.workspace = r"C:/Data/PierceTransit.gdb"
    env.overwriteOutput = True

    # Access Survey123 results (previously downloaded from ArcGIS Online)
    # Separate values to individual Origin and Destination CSV files
    results = csv.reader(open("OD_2017results.csv", 'rb'), delimiter=',')
    for rows in results:
        for row[0] in rows:
            if row[0] % 2 != 0:    ## Odd values represent the first location collected in pair (origin)
              o = open("origin_locations.csv", 'wb')
                writer1 = csv.DictWriter(o, fieldnames=field_names, extrasaction='ignore')
                writer1.writeheader()
                writer1.writerow()
        else:      # Even (Destination) values could be calculated using (if i % 2 == 0)
            d = open("destination_locations.csv", 'wb')
            writer2 = csv.DictWriter(d, fieldnames=field_names, extrasaction='ignore')
            writer2.writeheader()
            writer2.writerow()

    print "Origin and destination points placed in separate CSV files."

    # Create ORIGIN location points in ArcGIS
    in_table = "origin_locations.csv"
    x_coords = "x"
    y_coords = "y"
    out_layer = "origin_pts"
    saved_layer = "origin_pts.lyr"
    spatialref = arcpy.SpatialReference(4326)
    out_file = "C://Data/Shapefiles/origin_pts.shp"

    # Convert from CSV to Feature Class
    arcpy.management.MakeXYEventLayer(in_table, x_coords, y_coords, out_layer, spatialref)
    arcpy.management.SaveToLayerFile(out_layer, saved_layer)
    arcpy.management.CopyFeatures(saved_layer, out_file)
    arcpy.conversion.FeatureClassToGeodatabase(out_file, "PierceTransit.gdb")

    print "Origin Feature Class element created."

    # Create DESTINATION location points in ArcGIS
    in_table = "destination_locations.csv"
    x_coords = "x"
    y_coords = "y"
    out_layer = "destin_pts"
    saved_layer = "destin_pts.lyr"
    spatialref = arcpy.SpatialReference(4326)
    out_file = "C://Data/Shapefiles/destin_pts.shp"

    # Convert from CSV to Feature Class
    arcpy.management.MakeXYEventLayer(in_table, x_coords, y_coords, out_layer, spatialref)
    arcpy.management.SaveToLayerFile(out_layer, saved_layer)
    arcpy.management.CopyFeatures(saved_layer, out_file)
    arcpy.conversion.FeatureClassToGeodatabase(out_file, "PierceTransit.gdb")

    print "Destination Feature Class element created."

    # Iterate through origin-destination pairs to create route layers
    # Set local variables
    inNetworkDataset = "Transit/Transit_ND"
    inStops_O = "origin_pts"
    inStops_D = "destin_pts"
    outNALayerName = "RoutesTraveled"
    outRoutesFC = "Analysis/outRoutes"
    impedanceAttribute = "TravelTime"

    #Set the time of day for the analysis to 8AM on a generic Monday
    start_time = datetime.datetime(2017, 1, 1, 8, 0, 0)

    # Create a new Route layer.  Optimize on TravelTime_UsingTransit, but compute the
    # distance traveled by accumulating the Feet attribute.
    outRouteResultObject = arcpy.na.MakeRouteLayer(inNetworkDataset, outNALayerName,
                                         impedanceAttribute,
                                         accumulate_attribute_name=["Feet"],
                                         hierarchy="NO_HIERARCHY",
                                         start_date_time=start_time)

    # Get the layer object from the result object. The route layer can now be
    # referenced using the layer object.
    outNALayer = outRouteResultObject.getOutput(0)

    # Get the names of all the sublayers within the route layer.
    subLayerNames = arcpy.na.GetNAClassNames(outNALayer)
    # Store the layer names that we will use later
    stopsLayerName = subLayerNames["Stops"]
    routesLayerName = subLayerNames["Routes"]

    # Before loading the riders' start and end locations as route stops, set
    # up field mapping.  Map the "ParentGlobalID" field from the input data to
    # the RouteName property in the Stops sublayer, which ensures that each
    # unique ParentGlobalID will be placed in a separate route.  Matching
    # ParentGlobalIDs from inStops_Origin and inStops_Destination will end up in
    # the same route.
    fieldMappings = arcpy.na.NAClassFieldMappings(outNALayer, stopsLayerName)
    fieldMappings["RouteName"].mappedFieldName = "ParentGlobalID"

    # Add the riders' start and end locations as Stops. The same field mapping
    # works for both input feature classes because they both have a field called
    #"ParentGlobalID"
    arcpy.na.AddLocations(outNALayer, stopsLayerName, inStops_O,
                        fieldMappings, "",
                        exclude_restricted_elements = "EXCLUDE")
    arcpy.na.AddLocations(outNALayer, stopsLayerName, inStops_D,
                        fieldMappings, "",
                        exclude_restricted_elements = "EXCLUDE")

    # Solve the route layer.
    arcpy.na.Solve(outNALayer)

    # Get the output Routes sublayer and save it to a feature class
    RoutesSubLayer = arcpy.mapping.ListLayers(outNALayer, routesLayerName)[0]
    arcpy.management.CopyFeatures(RoutesSubLayer, outRoutesFC)


    print "Route layers created and stored in geodatabase."
    print "Script completed successfully."


# Catch errors.
except IOError as e:
    print "I/O error({0}): {1}".format(e.errno, e.strerror)
except ValueError:
    print "Value error:", sys.exc_info()[0]
    raise
except:
    print "Unexpected error:", sys.exc_info()[0]
    raise
