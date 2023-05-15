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

#volume_cad  = {"flow_volume" : "Flow_Volume", "tool_body" : "Tool_Body"}
#surface_cad = {"inlet": "NS_Inlet", "outlet": "NS_Outlet", "tool_body_top": "NS_Top", "tool_body_bottom": "NS_Bottom", 
#               "tool_body_side1" : "NS_Side1", "tool_body_side2" : "NS_Side2", "tool_body_side3": "NS_Side3", "tool_body_side4": "NS_Side4"}

#Get the entity ID associated with each CAD part 
#for key, value in volume_cad.items(): 
#    cht.get_single_entity_name(cht.project_id, cht.geometry_id, key = key, attributes=["SDL/TYSA_NAME"], values=[value])
#Get the entity ID associated with each predefined surface
#for key, value in surface_cad.items():
#    cht.get_single_entity_name(cht.project_id, cht.geometry_id, key = key ,_class = 'face' ,attributes=["SDL/TYSA_NAME"], values=[value])
#list_of_surfaces=cht.get_single_entity_name(project_id, geometry_id, key, kwargs)

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
            print(body_name)
            body_id=body.name
            print(body_id)
            for material in materials_dic:
                if material==body_name:
                    materials_dic[body_name]['keys'].append(body_id)

for material in materials_dic.keys():
    print(material)
    print(materials_dic[material]['conductivity'])    
    cht.set_custom_solid_material(material_name=material,material_conductivity=materials_dic[material]['conductivity'],key=materials_dic[material]['keys'])
# BCA- material set up
# materials={'Insulation':0.035,'Steel':50,'Concrete':2.1}
# for j, k in materials.items():
#     print(j,"->", k) #Prints the key and value for each material 
#     cht.set_custom_solid_material(material_name=j,material_conductivity=k,key='')



#BCA: this line should return geometry info including the face colour
# #geometry_list=cht.get_entity_names_BCA(cht.project_id, cht.geometry_id, attributes=["SDL/TYSA_COLOUR"])
# solids_list=cht.get_entity_names_BCA(cht.project_id, cht.geometry_id,  attributes=["ATTRIB_XPARASOLID_NAME"])
# attribute_dict=solids_list[2].originate_from
# #print(attribute_dict)
# body_attributes=attribute_dict[0].attribute_list
# #print(x)
# #y=x[2].value
# #print(y)

# for body_attribute in body_attributes:
#     if body_attribute.attribute=='ATTRIB_XPARASOLID_NAME':
#         body_name=body_attribute.value
#         print(body_name)
# #BCA- change the SDL/TYSA_NAME to match the ATTRIB_XPARASOLID_NAME name. Does this work? Doesn't seem to change Simscale.
# for body_attribute in body_attributes:
#     if body_attribute.attribute!='ATTRIB_XPARASOLID_NAME':
#         body_attribute.value=body_name

# print(body_attributes)





faces_list=cht.get_entity_names_BCA(cht.project_id, cht.geometry_id,  _class = 'face',attributes=["SDL/TYSA_COLOUR"])
#attribute_dict2=geometry_list2[15].originate_from
for item in faces_list:
    attribute_dict2=item.originate_from
    face_colour_str=attribute_dict2[0].attribute_list[0].value   
    #face_colours = [float(ele) for ele in test]
    #BCA: Simscale spits out strings of decimals relating to RGB, format these into lists of RGB numbers.
    test=face_colour_str.replace("[","")
    #print(test)
    test=test.replace("]","")
    #print(test)
    test = list(test.split(" "))
    #print(test)
    test = [float(ele) for ele in test]
    #print(test)
    test=[round(ele*255) for ele in test]
    print(test)
    




  

# for key, value in cht.single_entity.items(): 
#     print("{k} : {v}".format(k = key, v = value))

# """Simulation Setup"""
#Global Settings
cht.set_compressible(state = False)
cht.set_turbulence_model(model = "KOMEGASST") #KOMEGASST ; NONE (laminar) BCA COMMENT- what do we need here?
cht.set_gravity_direction(direction = "z", value = -9.81) 
cht.set_initial_conditions()

# #-----------------------------
# #Define Materials   
   
# cht.set_fluid_material_water(fluid_name = 'Water', key = "flow_volume") #BCA: Delete this?
# # cht.set_fluid_material_air(fluid_name = "Air", key = "flow_volume") #BCA: Delete this?
# cht.set_solid_material_wood(solid_name = "Wood", key = "tool_body") #BCA: Delete this?
# #BCA added the following: (WHATS THE KEY ABOUT?)
#cht.set_custom_solid_material(solid_name="insulation",key="insulation",material_conductivity=0.035) #See the utilities script- how do I use the API methods to pass materials and add them?




# #BCA- material set up
# materials={'insulation':0.035,'steel':50,'bread':0.5}
# for j, k in materials.items():
#     print(j,"->", k) #Prints the key and value for each material 
# #   cht.set_custom_solid_material(solid_name="insulation",key="insulation",material_conductivity=0.035)

#cht.set_custom_solid_material(material_name="Insulation",material_conductivity=0.035)
# BCA- material set up
# materials={'Insulation':0.035,'Steel':50,'Concrete':2.1}
# for j, k in materials.items():
#     print(j,"->", k) #Prints the key and value for each material 
#     cht.set_custom_solid_material(material_name=j,material_conductivity=k,key='')

# #-----------------------------
# #Define Boundary Conditions
# #BCA: This looks a bit easier than materials?

# #BCA Edit: these lines could be used to take a dictionary from a json and push each boundary condition through
# boundary_conditions={'horizonal_int':{'temperature':20,'htc':7.69},'upward_int':{'temperature':20,'htc':10},'downward_int':{'temperature':20,'htc':10}}
# for i in boundary_conditions:
#     print(i)
#     for j, k in boundary_conditions[i].items():
#         print(j,"->", k)

# # cht.pressure_inlet_bc(value = 1, temp = 95 ,name = "Pressure Inlet", unit = 'bar', key = "inlet" )
# cht.pressure_outlet_bc(value = 0 ,name = "Pressure Outlet", unit = 'bar', key = "outlet" )

# cht.constant_velocity_inlet_bc(speed_x = 1, speed_y = 0, speed_z = 2, temp = 10, key = 'inlet')

# cht.external_wall_heat_flux_bc( amb_temp = 20, htc = 10 ,
#                                method = "DERIVED"  ,  # DERIVED ; FIXED ; FIXED_POWER
#                                name = 'ExternalWalls', 
#                                key_list = ["tool_body_top", "tool_body_bottom",
#                                            "tool_body_side1", "tool_body_side2",
#                                            "tool_body_side3", "tool_body_side4"])

cht.set_boundary_conditions()
# # print(len(cht.boundary_conditions))
# # print(cht.boundary_conditions)
# #-----------------------------
# #Define Simulation Numerics
cht.set_simulation_numerics()
# #-----------------------------
# #Define Advanced Concepts
# # cht.set_power_sources(power = 150, name = "power source abs", method = "ABSOLUTE", key_list = ["tool_body"])
# # cht.set_power_sources(power = 1000, name = "power source vol", method = "SPECIFIC", key_list = ["flow_volume"])
cht.set_advanced_concepts()
# #-----------------------------
# #Define Simulation Control Settings
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
# #Define Result Controls 
# cht.set_area_averages(name = 'inlet-outlet', write_interval = 10, key_list = ["inlet", 'outlet'])
# cht.set_area_averages(name = 'tool body', write_interval = 10, key_list = ["tool_body_top", "tool_body_bottom",
#                                                                         "tool_body_side1", "tool_body_side2",
#                                                                         "tool_body_side3", "tool_body_side4"])
# cht.set_area_volumes(name = 'inlet-outlet_vol', write_interval = 10, key_list = ["inlet", 'outlet'])

# #BCA edit:
# cht.set_internal_heat_flow_surfaces() #Needs to add the surfaces and the type ie heat flow integral.
# #cht.set_external_heat_flow_surfaces() #As above

# cht.set_probe_points(name = 'test_probe', source = "single") #single ; multiple
# cht.set_probe_points(name = 'multi_test_probe', source = "multiple") #single ; multiple
cht.set_result_control_items()
# #-----------------------------
# #Contact Detection
cht.set_contact_detection(method = "AUTO")
# #-----------------------------
# #create simulation
cht.set_simulation_spec( simulation_name = "BCA_API_Test")
# #-----------------------------    
# #Mesh settings
# cht.set_mesh_layer_settings(num_of_layers = 3, total_rel_thickness = 0.4, growth_rate = 1.5)
# cht.set_advanced_mesh_settings(small_feature_tolerance = 5E-5, gap_ref_factor = 0.05, gradation_rate = 1.22)
# cht.complete_mesh_settings(mesh_name = "Mesh_test", fineness = 0.1, physics_based_meshing = True)
# cht.estimate_mesh_operation()
# cht.start_meshing_operation(run_state = False)
# #-----------------------------    
# #Sanity checks
# cht.check_simulation_and_mesh_settings()
# #-----------------------------
# #Start Simulation
# # cht.find_simulation(name = "Get_Results")
# cht.estimate_simulation(maximum_cpu_consumption_limit = 200)
# cht.create_simulation(sim_name = "Results_test")
# cht.start_simulation_run(run_state = False)
# #-----------------------------
# #Download Results
# cht.get_simulation_results()
# cht.get_probe_point_results(name = "test_probe", field = 'T')
# cht.get_probe_point_results(name = "multi_test_probe", field = 'T')
# cht.get_surface_data_results(data_type = 'average', name = 'inlet-outlet', field = "T")
# cht.get_surface_data_results(data_type = 'average', name = 'inlet-outlet', field = "p")
# cht.get_surface_data_results(data_type = 'integral', name = 'inlet-outlet_vol', field = "Uy")
# cht.get_simulation_case_files()