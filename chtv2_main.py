# -*- coding: utf-8 -*-
"""
Created on Mon Jan 16 16:20:38 2023
@author: Kdeiri
"""

import utilities as util 
import pathlib
import simscale_sdk as sim_sdk
import pandas as pd 
##################################

cht = util.ConjugateHeatTransfer()

"""Setup the API connection"""
cht.set_api_connection()

"""Create Project"""
cht.create_project( name = "CHTv2_Api", description = "test")

"""Upload Geometry"""
#Provide the name of the files to upload, if it is a directory simply give the name,
#if it is a file then add the file extension to the name ex: example.stl
name_of_files_to_upload = ["Design_2.x_t"]
# name_of_files_to_upload = ["Design_1.x_t", "Design_2.x_t", "Design_3.x_t" ]
geometry_path = []
# for i, cad in enumerate(name_of_files_to_upload): 
geometry_path.append(pathlib.Path().cwd() / "Geometries" / name_of_files_to_upload[0])
cht.upload_geometry(name_of_files_to_upload[0], geometry_path[0])

"""Define geometry mappings"""

volume_cad  = {"flow_volume" : "Flow_Volume", "tool_body" : "Tool_Body"}
surface_cad = {"inlet": "NS_Inlet", "outlet": "NS_Outlet", "tool_body_top": "NS_Top", "tool_body_bottom": "NS_Bottom", 
               "tool_body_side1" : "NS_Side1", "tool_body_side2" : "NS_Side2", "tool_body_side3": "NS_Side3", "tool_body_side4": "NS_Side4"}

#Get the entity ID associated with each CAD part 
for key, value in volume_cad.items(): 
    cht.get_single_entity_name(cht.project_id, cht.geometry_id, key = key, attributes=["SDL/TYSA_NAME"], values=[value])
#Get the entity ID associated with each predefined surface
for key, value in surface_cad.items():
    cht.get_single_entity_name(cht.project_id, cht.geometry_id, key = key ,_class = 'face' ,attributes=["SDL/TYSA_NAME"], values=[value])
    
# for key, value in cht.single_entity.items(): 
#     print("{k} : {v}".format(k = key, v = value))


"""Simulation Setup"""
#Global Settings
cht.set_compressible(state = False)
cht.set_turbulence_model(model = "KOMEGASST") #KOMEGASST ; NONE (laminar)
cht.set_gravity_direction(direction = "z", value = -9.81) 
cht.set_initial_conditions()
#-----------------------------
#Define Materials
cht.set_fluid_material_water(fluid_name = 'Water', key = "flow_volume")
# cht.set_fluid_material_air(fluid_name = "Air", key = "flow_volume")
cht.set_solid_material_wood(solid_name = "Wood", key = "tool_body")
#-----------------------------
#Define Boundary Conditions
# cht.pressure_inlet_bc(value = 1, temp = 95 ,name = "Pressure Inlet", unit = 'bar', key = "inlet" )
cht.pressure_outlet_bc(value = 0 ,name = "Pressure Outlet", unit = 'bar', key = "outlet" )

cht.constant_velocity_inlet_bc(speed_x = 1, speed_y = 0, speed_z = 2, temp = 10, key = 'inlet')

cht.external_wall_heat_flux_bc( amb_temp = 20, htc = 10 ,
                               method = "DERIVED"  ,  # DERIVED ; FIXED ; FIXED_POWER
                               name = 'ExternalWalls', 
                               key_list = ["tool_body_top", "tool_body_bottom",
                                           "tool_body_side1", "tool_body_side2",
                                           "tool_body_side3", "tool_body_side4"])

cht.set_boundary_conditions()
# print(len(cht.boundary_conditions))
# print(cht.boundary_conditions)
#-----------------------------
#Define Simulation Numerics
cht.set_simulation_numerics()
#-----------------------------
#Define Advanced Concepts
# cht.set_power_sources(power = 150, name = "power source abs", method = "ABSOLUTE", key_list = ["tool_body"])
# cht.set_power_sources(power = 1000, name = "power source vol", method = "SPECIFIC", key_list = ["flow_volume"])
cht.set_advanced_concepts()
#-----------------------------
#Define Simulation Control Settings
cht.set_simulation_end_time(time = 1000)
cht.set_simulation_time_step(time_step = 1)
cht.set_simulation_write_controls(write_interval = 1000)
cht.set_simulation_max_run_time(max_run_time = 40000)
cht.set_simulation_control()
#-----------------------------
#Define Geometry Primitives
cht.set_single_geometry_primitive_point(name = "test_point", pos_x = 0.0420, pos_y= 0.0438, pos_z = 0)
probe_points_path = pathlib.Path().cwd() / "probe_points" / "probe_list.txt"
cht.set_multiple_geometry_primitive_points(path_to_csv = probe_points_path)
#-----------------------------
#Define Result Controls 
cht.set_area_averages(name = 'inlet-outlet', write_interval = 10, key_list = ["inlet", 'outlet'])
cht.set_area_averages(name = 'tool body', write_interval = 10, key_list = ["tool_body_top", "tool_body_bottom",
                                                                        "tool_body_side1", "tool_body_side2",
                                                                        "tool_body_side3", "tool_body_side4"])
cht.set_area_volumes(name = 'inlet-outlet_vol', write_interval = 10, key_list = ["inlet", 'outlet'])
cht.set_probe_points(name = 'test_probe', source = "single") #single ; multiple
cht.set_probe_points(name = 'multi_test_probe', source = "multiple") #single ; multiple
cht.set_result_control_items()
#-----------------------------
#Contact Detection
cht.set_contact_detection(method = "AUTO")
#-----------------------------
#create simulation
cht.set_simulation_spec( simulation_name = "constant_velocity_vector_test")
#-----------------------------    
#Mesh settings
cht.set_mesh_layer_settings(num_of_layers = 3, total_rel_thickness = 0.4, growth_rate = 1.5)
cht.set_advanced_mesh_settings(small_feature_tolerance = 5E-5, gap_ref_factor = 0.05, gradation_rate = 1.22)
cht.complete_mesh_settings(mesh_name = "Mesh_test", fineness = 0.1, physics_based_meshing = True)
cht.estimate_mesh_operation()
cht.start_meshing_operation(run_state = False)
#-----------------------------    
#Sanity checks
cht.check_simulation_and_mesh_settings()
#-----------------------------
#Start Simulation
# cht.find_simulation(name = "Get_Results")
cht.estimate_simulation(maximum_cpu_consumption_limit = 200)
cht.create_simulation(sim_name = "Results_test")
cht.start_simulation_run(run_state = False)
#-----------------------------
#Download Results
cht.get_simulation_results()
cht.get_probe_point_results(name = "test_probe", field = 'T')
cht.get_probe_point_results(name = "multi_test_probe", field = 'T')
cht.get_surface_data_results(data_type = 'average', name = 'inlet-outlet', field = "T")
cht.get_surface_data_results(data_type = 'average', name = 'inlet-outlet', field = "p")
cht.get_surface_data_results(data_type = 'integral', name = 'inlet-outlet_vol', field = "Uy")
cht.get_simulation_case_files()
