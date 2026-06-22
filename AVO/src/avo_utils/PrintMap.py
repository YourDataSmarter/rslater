import os
import arcpy
import json
import datetime
import logger as logging
import base64
import gc

VERSION = "2026.06.10.0"
TOOL_NAME = os.path.splitext(os.path.basename(__file__))[0]
TIME_STAMP = datetime.datetime.now().isoformat().replace("-", "").replace(":", "").replace(".", "")

LOG_LEVEL = logging.WARNING

METERSPERACRE = 4046.856
TEMPLATE_DIR = "."
TEMPLATE_DICT = {"stl_contract" : ["stl_contract.pagx",("Lease","RecreationAreaID","RecreationAreaAlias","ContractAcres",["LeaseParcel","Amenity Point"]),False]
                 ,"all_landsale": ["all_landsale.pagx",("Lease","RecreationAreaID","RecreationAreaAlias","ContractAcres",["Amenity Point"]),True]
                 ,"all_permit": ["all_permit.pagx",("Permit Area","PermitAreaId","PermitAreaName","PermitAreaContractAcres",["Access Point", "Public Access Corridor", "Non-Motorized Use"]),True]
                 ,"nhw_bearbait" : ["nhw_bearbait.pagx",("Plot Location","RecreationAreaID","ProductAlias","ContractAcres",[]),False]
                }
OUTPUT_FOLDER = arcpy.env.scratchFolder
LOG_OUTPUT_FOLDER = OUTPUT_FOLDER

def file_to_b64(filepath):
    with open(filepath, 'rb') as f:
        ba = bytearray(f.read())
    return base64.b64encode(ba)

def _get_template(document_type):
    logging.debug("_get_template()")
    template_name = TEMPLATE_DICT[document_type][0]
    template_path = os.path.join(TEMPLATE_DIR,template_name)

    return template_path

def _activate_map(lyt,subjectid,document_type,options):

    subject_layer_name = TEMPLATE_DICT[document_type][1][0]
    subject_id_field = TEMPLATE_DICT[document_type][1][1]
    subject_label_field = TEMPLATE_DICT[document_type][1][2]
    subject_acre_field = TEMPLATE_DICT[document_type][1][3]
    HASCUSTOMSCRIPT = TEMPLATE_DICT[document_type][2]
    
    filter_lyr_names = TEMPLATE_DICT[document_type][1][4]

    start = datetime.datetime.now()
    text_dict = {}
    logging.debug("_activate_map()")
    
    
    mf = lyt.listElements("MapFrame_Element")[0]
    mp = mf.map
    mpSR = mp.spatialReference
    
    logging.debug("\t{}: found map".format(datetime.datetime.now()-start))

    mark = datetime.datetime.now()
    layer_ls = mp.listLayers()
    logging.debug("\t{}: listed map layers".format(datetime.datetime.now()-mark))
    logging.debug("\t\t{}".format([l.name for l in layer_ls]))
    

    mark = datetime.datetime.now()
    q = "{} = '{}'".format(subject_id_field,subjectid)
    logging.debug("\t\tquery definition: {}".format(q))

    subject_lyr = [l for l in layer_ls if l.name == subject_layer_name][0]
    subject_lyr.definitionQuery = q
    logging.debug("\t{}: subject layer query definition applied ".format(datetime.datetime.now()-start))
    
    if len(filter_lyr_names) != 0:
        filter_lyrs = [l for l in layer_ls if l.name in filter_lyr_names]

        for fl in filter_lyrs:
            fl.definitionQuery = q
            logging.debug("\t{}: {} layer query definition applied ".format(datetime.datetime.now()-start, fl.name))

    subject_count = int(arcpy.GetCount_management(subject_lyr)[0])
    logging.debug("\t{}: getcount={}".format(datetime.datetime.now()-start, subject_count))
    
    if subject_count == 0:
        logging.error("ERROR: ID {} Not found in {}.{}".format(subjectid,subject_layer_name,subject_id_field))
        ##Update##
        #del df 
        del mp
        del mf
        del subject_count
        del subject_lyr
        ##Update##
        gc.collect()
        return False
    else:
        logging.debug("\tprocessing subject...")

        #mark = datetime.datetime.now()
        sr = arcpy.SpatialReference(4326)
        with arcpy.da.SearchCursor(subject_lyr,["SHAPE@TRUECENTROID",subject_acre_field,subject_label_field,"SHAPE@"], where_clause=q, spatial_reference = sr) as rows:
            for row in rows:
                lat = row[0][1]
                lng = row[0][0]
                acres = row[1]
                subject_name = row[2]

                logging.debug("\t\tfeature '{}' centroid=( {} , {} )".format(subject_name, lat,lng))
        logging.debug("\t{}: parcel centroid and acres determined".format(datetime.datetime.now()-start))

        f_ext = mf.getLayerExtent(subject_lyr).projectAs(mpSR)
        logging.debug("\t{}: getLayerExtent".format(datetime.datetime.now()-start))
    
        map_title = "{} - {} Map".format(subject_name,document_type.split("_")[0].title())
        text_dict["Map Type"] = map_title

        logging.debug("\t{}: zoomed to layer".format(datetime.datetime.now()-start))

        if HASCUSTOMSCRIPT:
            #Add any custom script for new MXDs here
            if document_type == "all_permit":
                logging.debug("\tUpdating Permit Text...")
                
                subject_layer_name = TEMPLATE_DICT["all_permit"][1][0]
                subject_lyr = [l for l in layer_ls if l.name == subject_layer_name][0]
                
                with arcpy.da.SearchCursor(subject_lyr,["PermitAreaLocation"], where_clause=q) as rows:
                    for row in rows:
                        location_str = row[0]
                        logging.debug("\t\tfeature '{}'".format(location_str))
                        
                text_dict["COUNTY"] = location_str

                logging.debug("\textra permit data acquired.")
            elif document_type == "all_landsale":
                logging.debug("\tfiltering Area Removed by parcel ids...")
                
                parcelid_ls = options["parcel_ids"]
                parcelid_ls_str = "('{}')".format("', '".join(parcelid_ls))

                ###Move these values into config?
                subject_layer_name  = "Area Removed"
                subject_acre_field  = "ContractAcres"
                
                q = "ParcelId in {}".format(parcelid_ls_str)
                logging.debug("\tparcel query definition: {}".format(q))

                subject_lyr = [l for l in layer_ls if l.name == subject_layer_name][0]
                subject_lyr.definitionQuery = q
                
                acres = 0.0
                with arcpy.da.SearchCursor(subject_lyr,[subject_acre_field], where_clause=q) as rows:
                    for row in rows:
                        acres += row[0]
                
                logging.debug("\tremoved acres aggregated : {}".format(arcres))

                p_ext = mf.getLayerExtent(subject_lyr).projectAs(mpSR)
                f_ext = _get_union_extent(f_ext, p_ext)

                logging.debug("\tall land sale custom script complete")

        text_dict["DATE"] = _get_date_string()
        if document_type == "nhw_bearbait": 
            text_dict["ACRES"] = "{}".format(int(round(acres,0)))
        elif document_type == "all_landsale":
            text_dict["ACRES"] = "Removed Acres: {}".format(int(round(acres,0)))
        else:
            text_dict["ACRES"] = "Acres: {}".format(int(round(acres,0)))
        text_dict["PRODUCTNAME"] = subject_name
        
        _update_text_element(lyt,text_dict)
        logging.debug("\t{}: text updated".format(datetime.datetime.now()-start))

        mf.panToExtent(f_ext)
        logging.debug("\t{}: panToExtent".format(datetime.datetime.now()-start))

        c = mf.camera
        if document_type == "all_landsale":
            _adjust_zoom(c,24000.0)
        else:
            _adjust_zoom(c)
        logging.debug("\t{}: zoom adjusted".format(datetime.datetime.now()-start))

        
        ##Update##
        del mp
        del mf
        del subject_count
        del subject_lyr
        gc.collect()
        ##Update##
        logging.debug("\t{}: activate map complete".format(datetime.datetime.now()-start))
    return True

def _adjust_zoom(c,zmin=36000.0,zmax=None):
    logging.debug("\t_adjust_zoom()")

    zl = float(c.scale)
    logging.debug("\t\tAdjusting zoom from 1:{}".format(zl))
    
    if zl < zmin:
        zl = zmin
    else:
        r = zl % 6000.0
        zl += (6000.0 - r)
        zl *= 1.25

    if zmax:
        if zl > zmax:
            logging.warning("Area of interest larger than zoom level restrictions permit:\r\n\tSuggested zoom level: {}.".format(zl))

    logging.debug("\t\t to 1:{}".format(zl))
    c.scale = float(zl)

    return True

def _get_union_extent(extent1, extent2):
    """Returns a new arcpy.Extent object that is the union of two extents."""
    x_min = min(extent1.XMin, extent2.XMin)
    y_min = min(extent1.YMin, extent2.YMin)
    x_max = max(extent1.XMax, extent2.XMax)
    y_max = max(extent1.YMax, extent2.YMax)
    
    return arcpy.Extent(x_min, y_min, x_max, y_max)

def _update_text_element(lyt,text_dict):
    for elm in lyt.listElements("TEXT_ELEMENT"):
        for n in text_dict.keys():
                if elm.name == n:
                    try:
                        elm.text = text_dict[n]
                    except:
                        logging.debug("WARNING: TextELEMENT issue")
                        logging.debug(elm.name)
                        logging.debug(text_dict[n])
    return True

def _export_to_file(file_path,lyt,export_format,export_options):
    logging.debug("_export_to_file()")
    logging.debug("\t{}".format(export_format))
    #TODO need to manipulate map document page height

    if export_format== "pdf":
        lyt.exportToPDF(file_path,**export_options)

    elif export_format in ["jpeg","jpg"]:
        lyt.exportToJPEG(file_path,**export_options)

    elif export_format == "png":
        lyt.exportToPNG(file_path,**export_options)

    elif export_format in ["tif", "tiff"]:
        lyt.exportToTIFF(file_path,**export_options)

    return file_path

def _pad_zero(n):
    if n < 10:
        n = "0{}".format(n)
    return n

def _get_date_number():
    this_date = datetime.datetime.now()
    d = _pad_zero(this_date.day)
    m = _pad_zero(this_date.month)
    y = this_date.year
    h = _pad_zero(this_date.hour)
    mm = _pad_zero(this_date.minute)
    s = _pad_zero(this_date.second)

    date_str = "{}{}{}{}{}{}".format(y,m,d,h,mm,s)

    return date_str

def _get_date_string():
    this_date = datetime.datetime.now()
    d = this_date.day
    m = this_date.month
    y = this_date.year

    date_str = r"{}/{}/{}".format(m,d,y)

    return date_str

def _create_output_file(document_type,subjectid,export_format):
    logging.debug("_create_output_file()")
    sufix = _get_date_number()
    prefix = "{}{}".format(subjectid,TEMPLATE_DICT[document_type][0][:-5])
    filetype = ".{}".format(export_format)
    fn = r"{}\{}{}{}".format(OUTPUT_FOLDER,prefix,sufix,filetype)
    unique_name = arcpy.CreateUniqueName(fn)
    return unique_name

def _get_export_options(options):
    logging.debug("_get_export_options")

    SUPPORTED_EXPORT_FORMATS = ["pdf","jpg","jpeg","png","tiff","tif"]

    if "format" in options.keys():
        export_format = options["format"].lower()
    else:
        export_format = "pdf"
    if export_format not in SUPPORTED_EXPORT_FORMATS:
        logging.warning("WARNING: {} not a supported export format.\r\n\t{}\r\nExporting to PDF instead".format(export_format,SUPPORTED_EXPORT_FORMATS))
        export_format = "pdf"

    export_options = {}

    if "export_options" in options.keys():
        user_export_options =  options["export_options"]
        known_unknowns = { u : user_export_options[u] for u in set(user_export_options) - set(export_options)}
        if bool(known_unknowns):
            for k in known_unknowns.keys():
                logging.warning("WARNING: unknown export option '{}'".format(k))

        user_updates = set(user_export_options).intersection(export_options)

        export_options.update((k,user_export_options[k]) for k in user_updates)

    return export_format, export_options

def main(subjectid, document_type, options):
    logging.debug("main()")
    start = datetime.datetime.now()
    
    export_format, export_options = _get_export_options(options)

    template_path = _get_template(document_type)
    logging.debug("\ttemplate file: {}".format(template_path))
    logging.debug("{}: inputs parsed:".format(datetime.datetime.now()-start))

    lyt = arcpy.mp.ConvertLayoutFileToLayout(template_path)
    logging.debug("{}: templated opened".format(datetime.datetime.now()-start))

    success = _activate_map(lyt,subjectid,document_type,options)
    logging.debug("{}: map & layout conifgured: {}".format(datetime.datetime.now()-start, success))

    if success:
        file_path = _create_output_file(document_type,subjectid,export_format)
        logging.debug("{}: output name set: {}".format(datetime.datetime.now()-start, file_path))

        the_print = _export_to_file(file_path,lyt,export_format,export_options)
        logging.debug("{}: map exported to file".format(datetime.datetime.now()-start))
        
        b64 = file_to_b64(the_print)
        logging.debug("{}: base64 generated".format(datetime.datetime.now()-start))

        if options.get('cleanup', True):
            os.remove(the_print)
        del lyt
        del the_print

        if (options.get('logB64')):
            logging.debug("\tout_map: {}".format(str(out_map)))

        logging.debug("{}: cleanup complete".format(datetime.datetime.now()-start))

        return b64
    else:
        return ""

if __name__ == '__main__':

    # get tool parameters
    in_id = arcpy.GetParameterAsText(0)
    
    in_document_type = arcpy.GetParameterAsText(1)
    in_document_type = in_document_type.lower()
    
    in_template_folder = arcpy.GetParameterAsText(2)
    if in_template_folder and os.path.exists(in_template_folder):
        TEMPLATE_DIR = in_template_folder
    else:
        arcpy.AddError("Invalid templates dir")
        sys.exit()
    
    in_out_folder = arcpy.GetParameterAsText(3)
    if in_out_folder and os.path.exists(in_out_folder):
        OUTPUT_FOLDER = in_out_folder
    
    in_log_folder = arcpy.GetParameterAsText(4)
    if in_log_folder and os.path.exists(in_log_folder):
        LOG_OUTPUT_FOLDER = in_log_folder

    in_options = arcpy.GetParameterAsText(5)
    options = json.loads(in_options)
    
    # setup logger
    log_level = options.get("logLevel", LOG_LEVEL)
    log_file =  os.path.join(LOG_OUTPUT_FOLDER, "{}_{}.log".format(TOOL_NAME, TIME_STAMP))
    logging.basicConfig(filename=log_file,level=log_level)

    # log the tool name and version
    logging.info("{} VERSION: {}".format(TOOL_NAME, VERSION))
    logging.debug("\tlog file: {}".format(log_file))

    
    # debug log parameters
    logging.debug("\tin_id: {}".format(str(in_id)))
    # debug log parameters
    logging.debug("\tin_document_type: {}".format(str(in_document_type)))
    # run the main function
    out_map = main(in_id, in_document_type, options)

    # set results to toolbox
    arcpy.SetParameter(6, out_map)