# -*- coding: utf-8 -*-
"""
Created on Mon Jan 16 16:20:38 2023

@author: Kdeiri
"""

import utilities_BCA as util 
import pathlib
import simscale_sdk as sim_sdk
import pandas as pd 
##################################

run=1 #Use this to control whether to run or not, 1= run

cht = util.ConjugateHeatTransfer()

"""Setup the API connection"""
cht.api_key="08305d1b-3e6c-4626-af25-1dc6bda089ba"
cht.api_url="https://api.simscale.com"
cht.host = cht.api_url + cht.version
cht.set_api_connection()

"""Create Project"""
cht.create_project( name = "CHTv2_Api", description = "test")

#"""Upload Geometry"""
#Provide the name of the files to upload, if it is a directory simply give the name,
#if it is a file then add the file extension to the name ex: example.stl
#name_of_files_to_upload = ["Design_2.x_t"]
# name_of_files_to_upload = ["Design_1.x_t", "Design_2.x_t", "Design_3.x_t" ]
#geometry_path = []
# for i, cad in enumerate(name_of_files_to_upload): 
#geometry_path.append(pathlib.Path().cwd() / "Geometries" / name_of_files_to_upload[0])
#cht.upload_geometry(name_of_files_to_upload[0], geometry_path[0])
cht.upload_geometry('API Test Geometry-Export') # Utilities script checks if this is already on Simscale and if so uses this.

"""Define geometry mappings"""

#Mock materials dictionary from Grasshopper
materials_dic={'Concrete':{'conductivity':2.1,'keys':[]},'Insulation':{'conductivity':0.035,'keys':[]},'Steel':{'conductivity':50,'keys':[]}}


#Step 1 get the solids list.
body_list=cht.get_entity_names_BCA(cht.project_id, cht.geometry_id,  attributes=["ATTRIB_XPARASOLID_NAME"])
#Step 2, go through each solid and find out what it's name is, and id
for body in body_list:
    attribute_dict=body.originate_from
    body_attributes=attribute_dict[0].attribute_list
    for body_attribute in body_attributes:
        if body_attribute.attribute=='ATTRIB_XPARASOLID_NAME':
            body_name=body_attribute.value
            #print(body_name)
            body_id=body.name
            #print(body_id)
            for material in materials_dic:
                #materials_dic[body_name]['keys'].append(body_id) #Testing. Delete this line and uncomment the ones below.
                if material==body_name:
                    materials_dic[body_name]['keys'].append(body_id)

"""Simulation Setup"""
#Global Settings
cht.set_compressible(state = False)
cht.set_turbulence_model(model = "KOMEGASST") #KOMEGASST ; NONE (laminar) BCA COMMENT- what do we need here?
cht.set_gravity_direction(direction = "z", value = -9.81) 
cht.set_initial_conditions()

# #-----------------------------
"""Define Materials"""   
   
for material in materials_dic.keys():
    #print(material)
    #print(materials_dic[material]['conductivity'])
    #print(materials_dic[material]['keys'][0])
    #print(materials_dic[material]['keys'])
    cht.set_custom_solid_material(material_name=material,material_conductivity=materials_dic[material]['conductivity'],keys=materials_dic[material]['keys'])



"""Define Boundary Conditions"""

#Mock boundary condition dictionary from Grasshopper
boundary_conditions_dic={'Horizontal Internal':{'temperature':20,'htc':7.69,'type':'internal','colour':[255, 0, 0],'keys':[]},'Horizontal Down':{'temperature':20,'htc':5.89,'type':'internal','colour':[0, 255, 0],'keys':[]},\
                         'Horizontal Up':{'temperature':20,'type':'internal','htc':10,'colour':[0, 128, 0],'keys':[]},'External':{'temperature':0.001,'htc':25,'type':'external','colour':[0, 0, 255],'keys':[]},\
                         'External Rainscreen':{'temperature':0.001,'htc':7.69,'type':'external','colour':[0, 100, 0],'keys':[]}}

faces_list=cht.get_entity_names_BCA(cht.project_id, cht.geometry_id,  _class = 'face',attributes=["SDL/TYSA_COLOUR"])
#attribute_dict2=geometry_list2[15].originate_from
for item in faces_list:
    attribute_dict2=item.originate_from
    face_colour_str=attribute_dict2[0].attribute_list[0].value   
    #face_colours = [float(ele) for ele in test]
    #BCA: Simscale spits out strings of decimals relating to RGB, format these into lists of RGB numbers.
    face_colour_RGB=face_colour_str.replace("[","")
    #print(test)
    face_colour_RGB=face_colour_RGB.replace("]","")
    #print(test)
    face_colour_RGB = list(face_colour_RGB.split(" "))
    #print(test)
    face_colour_RGB = [float(ele) for ele in face_colour_RGB]
    #print(test)
    face_colour_RGB=[round(ele*255) for ele in face_colour_RGB]
    #print(test)
    for boundary_condition in boundary_conditions_dic.keys():
        #print(boundary_conditions_dic[boundary_condition]['colour'])
        #print(test)
        if face_colour_RGB==boundary_conditions_dic[boundary_condition]['colour']:
            #print("match")
            #print(item.name)
            boundary_conditions_dic[boundary_condition]['keys'].append(item.name)
        #print(materials_dic[material]['conductivity'])

cht.set_boundary_conditions()
# # print(len(cht.boundary_conditions))
# # print(cht.boundary_conditions)
# #-----------------------------
"""Define Simulation Numerics"""

cht.set_simulation_numerics()
# #-----------------------------
"""Define Advanced Concepts"""
# # cht.set_power_sources(power = 150, name = "power source abs", method = "ABSOLUTE", key_list = ["tool_body"])
# # cht.set_power_sources(power = 1000, name = "power source vol", method = "SPECIFIC", key_list = ["flow_volume"])
cht.set_advanced_concepts()

# #-----------------------------

"""Define Simulation Control Settings"""
cht.set_simulation_end_time(time = 1000)
cht.set_simulation_time_step(time_step = 1)
cht.set_simulation_write_controls(write_interval = 1000)
cht.set_simulation_max_run_time(max_run_time = 40000)
cht.set_simulation_control()
# #-----------------------------
# #Define Geometry Primitives
# cht.set_single_geometry_primitive_point(name = "test_point", pos_x = 0.0420, pos_y= 0.0438, pos_z = 0)
# probe_points_path = pathlib.Path().cwd() / "probe_points" / "probe_list.txt"
# cht.set_multiple_geometry_primitive_points(path_to_csv = probe_points_path)



# #-----------------------------
"""Define Result Controls""" 

# #Set the internal and external measurement surfaces for heat flow.

ht_surfaces_internal=[]
ht_surfaces_external=[]

for boundary_condition in boundary_conditions_dic.keys():
    #print(boundary_conditions_dic[boundary_condition]['temperature'])
    #print(boundary_conditions_dic[boundary_condition]['htc'])
    cht.external_wall_heat_flux_bc(amb_temp = boundary_conditions_dic[boundary_condition]['temperature'], htc = boundary_conditions_dic[boundary_condition]['htc'], name = boundary_condition, faces_to_assign=boundary_conditions_dic[boundary_condition]['keys'])
    if boundary_conditions_dic[boundary_condition]['type']=='internal':
        ht_surfaces_internal=ht_surfaces_internal+boundary_conditions_dic[boundary_condition]['keys']
    if boundary_conditions_dic[boundary_condition]['type']=='external':
        ht_surfaces_external=ht_surfaces_external+boundary_conditions_dic[boundary_condition]['keys']


cht.set_area_integrals(name = 'Internal', write_interval = 10, faces_to_assign = ht_surfaces_internal)
cht.set_area_integrals(name = 'External', write_interval = 10, faces_to_assign = ht_surfaces_external)       
       
# #Alternative approach as below. Better?
# cht.set_internal_heat_flow_surfaces() #Needs to add the surfaces and the type ie heat flow integral.
# #cht.set_external_heat_flow_surfaces() #As above

# cht.set_probe_points(name = 'test_probe', source = "single") #single ; multiple
# cht.set_probe_points(name = 'multi_test_probe', source = "multiple") #single ; multiple

cht.set_field_calculations() #Adds the heat flux field calc to the sim
cht.set_result_control_items() #Sets up the result control

# #-----------------------------
"""Contact Detection"""

cht.set_contact_detection(method = "AUTO")

# #-----------------------------
"""Create simulation"""

cht.set_simulation_spec( simulation_name = "BCA_API_Test")
#print(cht.model)
if run==1:
    cht.create_simulation()
    
# #-----------------------------    
"""Mesh settings"""
cht.set_mesh_layer_settings(num_of_layers = 3, total_rel_thickness = 0.4, growth_rate = 1.5)
cht.set_advanced_mesh_settings(small_feature_tolerance = 5E-5, gap_ref_factor = 0.05, gradation_rate = 1.22)
cht.complete_mesh_settings(mesh_name = "Mesh_test", fineness = 0.1, physics_based_meshing = True)
# cht.estimate_mesh_operation()
# cht.start_meshing_operation(run_state = False)
# #-----------------------------    
# #Sanity checks
# cht.check_simulation_and_mesh_settings()

# #-----------------------------
"""Start Simulation"""
# # cht.find_simulation(name = "Get_Results")
# cht.estimate_simulation(maximum_cpu_consumption_limit = 200)
# cht.create_simulation(sim_name = "Results_test")
# cht.start_simulation_run(run_state = False)
# #-----------------------------

"""Download Results"""
# cht.get_simulation_results()
# cht.get_probe_point_results(name = "test_probe", field = 'T')
# cht.get_probe_point_results(name = "multi_test_probe", field = 'T')
# cht.get_surface_data_results(data_type = 'average', name = 'inlet-outlet', field = "T")
# cht.get_surface_data_results(data_type = 'average', name = 'inlet-outlet', field = "p")
# cht.get_surface_data_results(data_type = 'integral', name = 'inlet-outlet_vol', field = "Uy")
# cht.get_simulation_case_files()

