import time
import isodate

#import pandas as pd #Don't think we need this for now. Doesn't work in Rhino currently.

from simscale_sdk import ApiException \

from simscale_sdk import  HeatTransfer, \
    TopologicalReference, \
    ConstantFunction, DimensionalFunctionTemperature, DimensionalFunctionThermalTransmittance, \
    NoSlipVBC, \
    DimensionalFunctionPower, SolidMaterial, AutomaticMeshSizingSimmetrix
    
import simscale_sdk as sim_sdk

class HeatTransferSimulationSetup:
    def __init__(self, api_client, geometry_api, geometry_id, project_id):

        self.api_client = api_client
        self.geometry_api = geometry_api
        self.geometry_id = geometry_id
        self.project_id = project_id
        self.mesh_operation_api = sim_sdk.MeshOperationsApi(self.api_client)
        self.materials_api = sim_sdk.MaterialsApi(self.api_client)
        self.simulation_api = sim_sdk.SimulationsApi(self.api_client)
        self.simulation_run_api = sim_sdk.SimulationRunsApi(self.api_client)
        self.table_import_api = sim_sdk.TableImportsApi(self.api_client)
        self.reports_api = sim_sdk.ReportsApi(self.api_client) 
        self.wind_api = sim_sdk.WindApi(self.api_client)

        #Geometry Mapping 
        self.single_entity     = {} #for later: separate the faces from volumes 
                                    #and add a validation rule against duplicate 
                                    #assignments for the same entity (materials)
        self.multiple_entities = {}
        
        #Global Simulation Settings
        self.compressible = False
        self.turbulence_model = None
        #self.fluid_model_gravity = None 
        self.solid_model = None
        self.initial_conditions = None 
        
        #Material Variables
        self.fluid_material = []
        self.solid_material = []
        
        #Numerics 
        self.solid_numerics = None
        
        #Boundary Condition Variables 
        self.boundary_conditions = []
        self.velocity_inlet      = []
        self.velocity_outlet     = []
        self.pressure_inlet      = []
        self.pressure_outlet     = []
        self.wall_bc             = []
        self.con_heatflux_bc     = []
        
        #Advanced Concept Variables
        self.advanced_concepts = None
        self.power_sources    = []
        self.porous_media     = []
        self.momentum_sources  = []
        self.thermal_resistance_networks = []
        
        #Simulation Control Variables
        self.simulation_control = None
        self.end_time = None
        self.delta_t  = None
        self.write_control = None 
        self.max_run_time = None 
        self.element_technology = None
        self.processors = None
        
        #Result Control Variables
        self.result_control = None
        self.surface_data = []
        self.volume_data  = []
        self.probe_points  = []
        self.field_calculations = []
        
        #Geometry Primitive Variables 
        self.geometry_primitive_uuid = None
        self.geometry_primitive_uuid_list = []
        
        #Contact Definition
        self.contact_detection = "AUTO"
        self.connection_groups = []
        self.contact_groups = []
        self.bonded_contacts = []
        self.bodies = []
        
        #Mesh Variables
        self.mesh_operation = None 
        self.mesh_operation_id = None
        self.automatic_layer_settings = None
        self.advanced_mesh_settings = None
        self.mesh_refinement = [] 
        self.mesh_id = None
        self.mesh_max_runtime = None

        #Simulation Creation Variables
        self.model = None 
        self.sim_max_run_time = None
        self.simulation_spec = None
        self.simulation_id   = None
        self.simulation_run  = None 
        self.run_id = None
        
        #Simulation Results Download Variables 
        self.simulation_results = None 
        self.probe_point_plot_info = None 
        self.probe_point_plot_data_response = None
        self.solution_info = None
        
        #Get geometry mappings (make sure the exception of those works properly)
    def get_single_entity_name(self, project_id, geometry_id, key ,**kwargs):
        
        entity = self.geometry_api.get_geometry_mappings(project_id, geometry_id, **kwargs)._embedded
        if len(entity) == 1:
            # print(entity[0].name)
            self.single_entity[key] = entity[0].name
            return self.single_entity[key]
        else:
            raise Exception(f"Found {len(self.single_entity[key])} entities instead of 1: {self.single_entity[key]}")

    def get_entity_names(self, project_id, geometry_id, key, number = None ,**kwargs):
        
        entities = self.geometry_api.get_geometry_mappings(project_id, geometry_id, **kwargs)._embedded
    
        if number is None or len(entities) == number:
            # print(len(entities))
            self.multiple_entities[key] = entities[0].name
            return [self.multiple_entities[key] for e in entities]
        else:
            raise Exception(f"Found {len(self.multiple_entities[key])} entities instead of {number}: {self.multiple_entities[key]}")
    
    def get_entity_names_BCA(self, project_id, geometry_id, number = None ,**kwargs):
        
        entities = self.geometry_api.get_geometry_mappings(project_id, geometry_id, **kwargs)._embedded
        return entities
        
        #if number is None or len(entities) == number:
            # print(len(entities))
            #self.multiple_entities[key] = entities[0].name
            
            #return [self.multiple_entities[key] for e in entities]
        #else:
            #raise Exception(f"Found {len(self.multiple_entities[key])} entities instead of {number}: {self.multiple_entities[key]}")
    
 
    
 
    def set_compressible(self, state = False):
        
        self.compressible = state
    
    def set_turbulence_model(self, model = "KOMEGASST"):
        # A choice of either None or KOMEGASST
        self.turbulence_model = model
        
    def set_gravity_direction(self, direction = "z", value = -9.81):
        
        if direction == "x": 
            self.fluid_model_gravity = sim_sdk.FluidModel(
                gravity=sim_sdk.DimensionalVectorAcceleration(
                    value=sim_sdk.DecimalVector(x=value, y=0, z=0),
                    unit="m/s²"))
            
        elif direction == "y": 
            self.fluid_model_gravity = sim_sdk.FluidModel(
                gravity=sim_sdk.DimensionalVectorAcceleration(
                    value=sim_sdk.DecimalVector(x=0, y=value, z=0),
                    unit="m/s²"))
        else:
            self.fluid_model_gravity = sim_sdk.FluidModel(
                gravity=sim_sdk.DimensionalVectorAcceleration(
                    value=sim_sdk.DecimalVector(x=0, y=0, z=value),
                    unit="m/s²"))
    ## NEW addition for HT
    def set_solid_model(self):
        self.solid_model = sim_sdk.SolidModel()
        

            
    def set_initial_conditions(self):
        #Add code to allow setting the initial conditions for any parameter 
        ## self.initial_conditions = sim_sdk.FluidInitialConditions()
        self.initial_conditions = sim_sdk.SolidInitialConditions()
        
    
    # def set_fluid_material_water(self, fluid_name = 'Water' , key = ''):
    
    #     #Add materials
    #     self.fluid_material.append(sim_sdk.IncompressibleMaterial(
    #                                     type="INCOMPRESSIBLE",
    #                                     name= fluid_name,
    #                                     viscosity_model=sim_sdk.NewtonianViscosityModel(
    #                                             type="NEWTONIAN",
    #                                             kinematic_viscosity=sim_sdk.DimensionalKinematicViscosity(
    #                                                     value=9.3379E-7,
    #                                                     unit="m²/s",
    #                                             ),
    #                                     ),
    #                                     density=sim_sdk.DimensionalDensity(
    #                                             value=997.33,
    #                                             unit="kg/m³",
    #                                     ),
    #                                     thermal_expansion_coefficient=sim_sdk.DimensionalThermalExpansionRate(
    #                                             value=2.07E-4,
    #                                             unit="1/K",
    #                                     ),
    #                                     reference_temperature=sim_sdk.DimensionalTemperature(
    #                                             value=298.15,
    #                                             unit="K",
    #                                     ),
    #                                     laminar_prandtl_number=6.5241,
    #                                     turbulent_prandtl_number=0.85,
    #                                     specific_heat=sim_sdk.DimensionalSpecificHeat(
    #                                             value=4180,
    #                                             unit="J/(kg·K)",
    #                                     ),
    #                                     topological_reference=sim_sdk.TopologicalReference(
    #                                             entities=[
    #                                                     self.single_entity[key],
    #                                             ],
    #                                             sets=[],
    #                                     ),
    #                                     built_in_material="builtInWater",
    #                             ),) 

    # def set_fluid_material_air(self, fluid_name = "Air" ,key = ''):
        
    #     self.fluid_material.append(sim_sdk.IncompressibleMaterial(
    #                                     type="INCOMPRESSIBLE",
    #                                     name= fluid_name,
    #                                     viscosity_model=sim_sdk.NewtonianViscosityModel(
    #                                             type="NEWTONIAN",
    #                                             kinematic_viscosity=sim_sdk.DimensionalKinematicViscosity(
    #                                                     value=1.529e-5,
    #                                                     unit="m²/s",
    #                                             ),
    #                                     ),
    #                                     density=sim_sdk.DimensionalDensity(
    #                                             value=1.196,
    #                                             unit="kg/m³",
    #                                     ),
    #                                     thermal_expansion_coefficient=sim_sdk.DimensionalThermalExpansionRate(
    #                                             value=3.43e-3,
    #                                             unit="1/K",
    #                                     ),
    #                                     reference_temperature=sim_sdk.DimensionalTemperature(
    #                                             value=273.1,
    #                                             unit="K",
    #                                     ),
    #                                     laminar_prandtl_number=0.713,
    #                                     turbulent_prandtl_number=0.85,
    #                                     specific_heat=sim_sdk.DimensionalSpecificHeat(
    #                                             value=1004,
    #                                             unit="J/(kg·K)",
    #                                     ),
    #                                     topological_reference=sim_sdk.TopologicalReference(
    #                                             entities=[
    #                                                     self.single_entity[key],
    #                                             ],
    #                                             sets=[],
    #                                     ),
    #                                     built_in_material="builtInWater",
    #                             ),) 
        
    # def add_fluid_material(self, fluid_name = 'Hydrogen' ,key = ''):
        
    #     #for later:Figure out how to add materials directly through the material library
    #     #without having to define the material properties manually
        
    #     # Add a material to the simulation
        
    #     # material_groups = self.materials_api.get_material_groups().embedded
    #     # default_material_group = next((group for group in material_groups if group.group_type == MaterialGroupType.SIMSCALE_DEFAULT), None)
    #     # if not default_material_group:
    #     #     raise Exception(f"Couldn't find default material group in {material_groups}")
        
    #     # default_materials = self.materials_api.get_materials(material_group_id=default_material_group.material_group_id).embedded
    #     # material_air = next((material for material in default_materials if material.name == fluid_name), None)
    #     # if not material_air:
    #     #     raise Exception(f"Couldn't find default Air material in {default_materials}")
        
    #     # material_data = self.materials_api.get_material_data(
    #     #     material_group_id=default_material_group.material_group_id,
    #     #     material_id=material_air.id
    #     # )
    #     # material_update_request = MaterialUpdateRequest(
    #     #     operations=[
    #     #         MaterialUpdateOperation(
    #     #             path="/materials/fluids",
    #     #             material_data=material_data,
    #     #             reference=MaterialUpdateOperationReference(
    #     #                 material_group_id=default_material_group.material_group_id,
    #     #                 material_id=material_air.id
    #     #             )
    #     #         )
    #     #     ]
    #     # )
    #     # self.fluid_material.append( self.simulation_api.update_simulation_materials(self.project_id, self.simulation_id, material_update_request))
    #     pass
    

    # def set_solid_material_wood(self, solid_name = 'Wood' , key = ''):
        
    #     self.solid_material.append(    
    #             sim_sdk.SolidMaterial(
    #                         name="Wood",
    #                         transport=sim_sdk.ConstIsoTransport(
    #                                 type="CONST_ISO",
    #                                 conductivity=sim_sdk.IsotropicConductivity(
    #                                         type="ISOTROPIC",
    #                                         thermal_conductivity=sim_sdk.DimensionalFunctionThermalConductivity(
    #                                                 value=sim_sdk.ConstantFunction(
    #                                                         type="CONSTANT",
    #                                                         value=0.16,
    #                                                 ),
    #                                                 unit="W/(m·K)",
    #                                         ),
    #                                 ),
    #                                 thermo=sim_sdk.HConstThermo(
    #                                         type="HCONST",
    #                                         specific_heat=sim_sdk.DimensionalSpecificHeat(
    #                                                 value=1260,
    #                                                 unit="J/(kg·K)",
    #                                         ),
    #                                         equation_of_state=sim_sdk.RhoConstEquationOfState(
    #                                                 type="RHO_CONST",
    #                                                 density=sim_sdk.DimensionalDensity(
    #                                                         value=500,
    #                                                         unit="kg/m³",
    #                                                 ),
    #                                         ),
    #                                 ),
    #                         ),
    #                         topological_reference=sim_sdk.TopologicalReference(
    #                                 entities=
    #                                 [
    #                                     self.single_entity[key]
    #                                     ], 
    #                                 sets=[],
    #                         ),
    #                         built_in_material="builtInWood",
    #                 ),
    #                 )

    
    #def set_custom_solid_material(self, material_name = '',keys = ''):
    def set_custom_solid_material(self,material_name='',material_conductivity='',keys=''):    #BCA Edit- added material conductivity to be passed here
        self.solid_material.append( SolidMaterial(
                                    name= material_name,

                                    density=sim_sdk.DimensionalFunctionDensity(
                                        value=sim_sdk.ConstantFunction(
                                            type="CONSTANT",
                                            value=1000,
                                        ),
                                        unit="kg/m³",
                                    ),

                                    conductivity=sim_sdk.IsotropicConductivity(
                                        type='ISOTROPIC',
                                        thermal_conductivity=sim_sdk.DimensionalFunctionThermalConductivity(
                                            value=sim_sdk.ConstantFunction(
                                                type="CONSTANT",
                                                value=material_conductivity,
                                            ),
                                            unit="W/(m·K)",
                                        )
                                    ),

                                    
                                    
                                    specific_heat=sim_sdk.DimensionalFunctionSpecificHeat(
                                        value=ConstantFunction(
                                                type="CONSTANT",
                                                value=1,
                                                ),
                                                unit="J/(kg·K)",
                                    ),

                                    topological_reference=sim_sdk.TopologicalReference(
                                            entities=keys,
                                                    #[
                                                      #self.single_entity[key] #BCA comment- does this only do a single entity then?
                                                      #keys
                                                      #],
                                            sets=[],#Better to put the entities into sets first then just use this?
                                    ),
                            ),)
    
    def set_simulation_numerics(self):
        
        self.solid_numerics = sim_sdk.SolidNumerics(
                solver=sim_sdk.MUMPSSolver(
                    type="MUMPS",
                    precision_singularity_detection=8,
                    stop_if_singular=True,
                    matrix_type="AUTOMATIC_DETECTION",
                    memory_percentage_for_pivoting=20,
                    linear_system_relative_residual=0.00001,
                    preprocessing=True,
                    renumbering_method="SCOTCH",
                    postprocessing="ACTIVE",
                    memory_management="AUTOMATIC",
                ),
        )

                 
   # NEW BCA METHOD!!!
    def convective_heat_flux_bc(self, amb_temp='', htc='', name='', faces_to_assign=''):
        self.con_heatflux_bc.append(sim_sdk.ConvectiveHeatFluxBC(
            name=name,
            reference_temperature=sim_sdk.DimensionalFunctionTemperature(
                value=sim_sdk.ConstantFunction(
                    type='CONSTANT',
                    value=amb_temp,
                ),
            ),
            heat_transfer_coefficient=sim_sdk.DimensionalFunctionThermalTransmittance(
                value=sim_sdk.ConstantFunction(
                    type='CONSTANT',
                    value=htc,
                ),
            ),
            topological_reference=sim_sdk.TopologicalReference(entities=faces_to_assign),
        ))

             
    def set_boundary_conditions(self):
        #for later: add a validation against multiple face assignments for a BC
        #for later: think of how you can make this code better looking (one liners?)

        #BCA COMMENT - WE DON'T ANY OF THESE EXCEPT FOR HEATFLUX BC AT BOTTOM
                
        # if len(self.velocity_inlet) >= 1 : 
        #     for v_inlet in self.velocity_inlet :
        #         if v_inlet in self.boundary_conditions:
        #             continue
        #         else:
        #             self.boundary_conditions.append(v_inlet)

        # if len(self.velocity_outlet) >= 1 : 
        #     for v_outlet in self.velocity_outlet: 
        #         if v_outlet in self.boundary_conditions:
        #             continue
        #         else:                
        #             self.boundary_conditions.append(v_outlet)
                
        # if len(self.pressure_inlet) >= 1 : 
        #     for p_inlet in self.pressure_inlet: 
        #         if p_inlet in self.boundary_conditions:
        #             continue
        #         else:                
        #             self.boundary_conditions.append(p_inlet)
                
        # if len(self.pressure_outlet) >= 1 : 
        #     for p_outlet in self.pressure_outlet:
        #         if p_outlet in self.boundary_conditions:
        #             continue
        #         else:                
        #             self.boundary_conditions.append(p_outlet)
                
        # if len(self.wall_bc) >= 1 : 
        #     for wall in self.wall_bc: 
        #         if wall in self.boundary_conditions:
        #             continue
        #         else:                
        #             self.boundary_conditions.append(wall)
        #BCA ADDITION!!!
        if len(self.con_heatflux_bc) >= 1 : 
            for bc in self.con_heatflux_bc: 
                if bc in self.boundary_conditions:
                    continue
                else:                
                    self.boundary_conditions.append(bc)

        
    def set_power_sources(self ,power , name = "power source", method = "ABSOLUTE" , key_list = []):
        #for later: add code to assign bodies that has multiple parts using get entities(for example one assignment for all batteries )
        #for later: think how you can add a validation rule against exact same power source definitions; is this needed?)
        
        bodies_to_assign = []
        for key in key_list: 
            # print(key)
            # print(self.single_entity[key])
            bodies_to_assign.append(self.single_entity[key])
            # print(bodies_to_assign)
            
        if method == "ABSOLUTE":
            self.power_sources.append(
            sim_sdk.AbsolutePowerSource(
                name= name,
                heat_flux=DimensionalFunctionPower(
                    value=sim_sdk.ConstantFunction(value= power), unit="W"), 
                topological_reference=TopologicalReference(entities= bodies_to_assign),
                ),)  
    
        elif method == "SPECIFIC": 
            self.power_sources.append(
            sim_sdk.SpecificPowerSource(
                name= name,
                heat_flux= sim_sdk.DimensionalFunctionVolumetricPower(
                    value=sim_sdk.ConstantFunction(value= power), unit="W/m³"), 
                topological_reference=TopologicalReference(entities= bodies_to_assign),
                ),)  
            
    def set_porous_media(self):
        pass
    
    def set_momentum_sources(self):
        pass
    
    def set_thermal_resistance_network(self):
        pass

    def set_advanced_concepts(self):
        #for later: add a validation against multiple face assignments for a BC
        # (this validation needs to be in the attribute functions e.g set_power_sources)
        
        self.advanced_concepts = sim_sdk.AdvancedConcepts(
            power_sources    = self.power_sources, 
            porous_mediums   = self.porous_media, 
            momentum_sources = self.momentum_sources,
            thermal_resistance_networks = self.thermal_resistance_networks)

    def set_simulation_end_time(self, time = 1000):
        
        self.end_time = sim_sdk.DimensionalTime(value= time, unit="s")
        
    def set_simulation_time_step(self, time_step = 1): 
        
        self.delta_t = sim_sdk.DimensionalTime(value= time_step, unit="s")
        
    def set_simulation_write_controls(self, write_interval = 1000): 
        
        self.write_control = sim_sdk.TimeStepWriteControl(write_interval= write_interval)
    
    def set_simulation_max_run_time(self, max_run_time = 40000):
        
        self.max_run_time = sim_sdk.DimensionalTime(value= max_run_time, unit="s")

    def set_processors(self, num_processors = -1):
        
        self.processors = sim_sdk.ComputingCore(
            num_of_computing_processors= num_processors
        )
    
    def set_simulation_control(self):
        
        self.simulation_control = sim_sdk.SolidSimulationControl(
            
                processors=self.processors,
                max_run_time= self.max_run_time
                )
    
    def set_area_averages(self, name = "Area average", write_interval = 10, key_list = []):
        
        faces_to_assign = []
        for key in key_list: 
            faces_to_assign.append(self.single_entity[key])

        self.surface_data.append(
            sim_sdk.AreaAverageResultControl(
                name = name, 
                write_control = sim_sdk.TimeStepWriteControl(write_interval = write_interval),
                topological_reference = sim_sdk.TopologicalReference(entities = faces_to_assign),))


    def set_area_integrals(self, name = '', write_interval = 10 , faces_to_assign = ''):
        self.surface_data.append(
            sim_sdk.AreaIntegralResultControl(
                name = name, 
                write_control = sim_sdk.TimeStepWriteControl(write_interval = write_interval),
                topological_reference = sim_sdk.TopologicalReference(entities = faces_to_assign),))


    def set_heat_flow_surfaces(self,name='',write_interval=10,faces_to_assign=''):
        self.surface_data.append(
            sim_sdk.HeatFlowCalculationResultControlItem(
                name = name, 
                #write_control = sim_sdk.TimeStepWriteControl(write_interval = write_interval), NOT NEEDED
                topological_reference = sim_sdk.TopologicalReference(entities = faces_to_assign),))


#BCA Edit- the below doesnt do anything currently. Is an alternative approach.
    def set_internal_heat_flow_surfaces(self, name = "Internal heat flow",write_interval=10, key_list=[]):
        faces_to_assign=[]
        for key in key_list:
            faces_to_assign.append(self.single_entity[key])
        
        self.surface_data.append(
            sim_sdk.AreaIntegralResultControl(
                name = name, 
                write_control = sim_sdk.TimeStepWriteControl(write_interval = write_interval),
                topological_reference = sim_sdk.TopologicalReference(entities = faces_to_assign),)) #WHat other things need to be added? Heat flow?



    
    def set_probe_points(self, name, source = "single"):
        
        if source == "single":
            
            self.probe_points.append(
                sim_sdk.ProbePointsResultControl(
                    name= name,
                    write_control=sim_sdk.TimeStepWriteControl(write_interval=10),
                    geometry_primitive_uuids=[self.geometry_primitive_uuid],
                ))
        
        elif source == "multiple": 
            
            self.probe_points.append(
                sim_sdk.ProbePointsResultControl(
                    name= name,
                    write_control=sim_sdk.TimeStepWriteControl(write_interval=10),
                    geometry_primitive_uuids= self.geometry_primitive_uuid_list,
                ))
                    
    def set_single_geometry_primitive_point(self, name, pos_x, pos_y, pos_z):
        
        geometry_primitive_point = sim_sdk.Point(
            name= name,
            center=sim_sdk.DimensionalVectorLength(value=sim_sdk.DecimalVector(x=pos_x, y=pos_y, z=pos_z), unit="m"),
        )
        self.geometry_primitive_uuid = self.simulation_api.create_geometry_primitive(
            self.project_id, geometry_primitive_point).geometry_primitive_id
        
        print(f"geometry_primitive_uuid: {self.geometry_primitive_uuid}")
    
    def set_multiple_geometry_primitive_points(self, path_to_csv):
        
        #csv format: Label X Y Z (delimiter is a space)
        
        probe_pd = pd.read_csv( path_to_csv , header = 0, delimiter = ' ') 
        probe_pd.set_index("Label")
        for row in probe_pd.index:
            pos_x = probe_pd['X'][row]
            pos_y = probe_pd['Y'][row]
            pos_z = probe_pd['Z'][row]
            print(pos_x)
            print(pos_y)
            print(pos_z)
        
            geometry_primitive_point = sim_sdk.Point(
                name= "point{}".format(row),
                center=sim_sdk.DimensionalVectorLength(value=sim_sdk.DecimalVector(x=float(pos_x), y=float(pos_y), z=float(pos_z)), unit="m"),
            )
            self.geometry_primitive_uuid_list.append(self.simulation_api.create_geometry_primitive(
                self.project_id, geometry_primitive_point).geometry_primitive_id)
            
        print(f"geometry_primitive_uuid: {self.geometry_primitive_uuid}")
        

    #BCA ADDITIONS!!!        
    def set_field_calculations(self):
        self.field_calculations.append(
        	sim_sdk.HeatFluxResultControlItem(
                heat_flux_type='FIELD', 
        		name='Boundary Condition Heat Flux',
        		)
        	)
        self.field_calculations.append(
        	sim_sdk.TemperatureResultControlItem(
                temperature_type='FIELD', 
        		name='Temperature',
        		)
        	)       
    
    def set_result_control_items(self):
        
       self.result_control = sim_sdk.SolidResultControl(
           area_calculation= self.surface_data, 
           point_data= self.probe_points, 
           solution_fields = self.field_calculations)
        
    def set_contact_detection(self, method = "AUTO"): #IS THIS NEEDED?
        
        self.contact_detection = method

    # def set_connection_groups(self, master, slave, name):
    #     self.master = master
    #     self.slave = slave
    #     self.contact_name = name

    #     # Create the BondedContact instance
    #     bonded_contact = sim_sdk.BondedContact(
    #         name=self.contact_name,
    #         type='BONDED_CONTACT',
    #         position_tolerance=sim_sdk.SetValuePositionTolerance(
    #             type='SET_VALUE',
    #             tolerance=sim_sdk.DimensionalLength(
    #                 value=0.001,
    #                 unit='m'
    #             )
    #         ),
    #         master_topological_reference=sim_sdk.TopologicalReference(entities=self.master),
    #         slave_topological_reference=sim_sdk.TopologicalReference(entities=self.slave)
    #     )
    #     self.bonded_contacts.append(bonded_contact)

    # def collate_contacts(self):
    #     # Create the Contact instance with the new BondedContact
    #     self.connection_groups = sim_sdk.Contact(
    #         type='CONTACT',
    #         connections=[self.bonded_contacts[0]]  # Pass the list of bonded contacts directly
    #     )

    # def set_connection_groups(self, master, slave, name):
    #     self.master = master
    #     self.slave = slave
    #     self.contact_name = name

    #     # Create the BondedContact instance
    #     bonded_contact = sim_sdk.BondedContact(
    #         name=self.contact_name,
    #         type='BONDED_CONTACT',
    #         position_tolerance=sim_sdk.SetValuePositionTolerance(
    #             type='SET_VALUE',
    #             tolerance=sim_sdk.DimensionalLength(
    #                 value=0.001,
    #                 unit='m'
    #             )
    #         ),
    #         master_topological_reference=sim_sdk.TopologicalReference(entities=self.master),
    #         slave_topological_reference=sim_sdk.TopologicalReference(entities=self.slave)
    #     )

    #     # Create the Contact instance with the new BondedContact
    #     contact = sim_sdk.Contact(
    #         type='CONTACT',
    #         connections=[bonded_contact]
    #     )


    #     # Append the new contact to the list
    #     self.connection_groups.append(contact)

    def set_connection_groups(self, master, slave, name):
        # Creates a new BondedContact and appends it to the bonded_contacts list
        bonded_contact = sim_sdk.BondedContact(
            name=name,
            type='BONDED_CONTACT',
            position_tolerance=sim_sdk.SetValuePositionTolerance(
                type='SET_VALUE',
                tolerance=sim_sdk.DimensionalLength(value=0.001, unit='m')
            ),
            master_topological_reference=sim_sdk.TopologicalReference(entities=master),
            slave_topological_reference=sim_sdk.TopologicalReference(entities=slave)
        )
        self.bonded_contacts.append(bonded_contact)

    def finalize_contact_groups(self):
        # Create one Contact object with all the BondedContacts
        contact_group = sim_sdk.Contact(
            type='CONTACT',
            connections=self.bonded_contacts
        )
        # Add this Contact to the connection_groups
        self.connection_groups.append(contact_group)

    def set_simulation_spec(self, simulation_name):
        """Simulation Setup"""
        # create simulation spec first to pass as reference to mesh operation for physics based meshing
        
        #Reset the spec to an intital state to avoid name conflict with the setup of simulations of different CAD
        self.simulation_spec = None 
        self.time_dependency = None
        #self.connection_groups = None
        self.mesh_order = None

        # self.element_technology = sim_sdk.SolidElementTechnology(
        #     element_technology3_d=sim_sdk.ElementTechnology(
        #         definition_method=sim_sdk.AutomaticElementDefinitionMethod(
        #             type='AUTOMATIC'
        #         )
        #     )
        # )

        self.element_technology = sim_sdk.SolidElementTechnology(
            element_technology3_d=sim_sdk.ElementTechnology(
                definition_method=sim_sdk.CustomElementDefinitionMethod(
                    type='CUSTOM',
                    thermal_mesh_element_order='SECOND'
                )
            )
        )
        
        #BCA EDIT- changed to heat transfer:
        #***********GOT TO HERE!!!!!
        self.model = HeatTransfer(
            time_dependency=self.time_dependency,
            connection_groups=self.connection_groups,
            element_technology=self.element_technology,
            model=self.solid_model,
            materials=self.solid_material,
            initial_conditions=self.initial_conditions,
            boundary_conditions=self.boundary_conditions,
            numerics=self.solid_numerics,
            simulation_control=self.simulation_control,
            result_control=self.result_control,
            mesh_order=self.mesh_order,
        )

        self.simulation_spec = sim_sdk.SimulationSpec(name=simulation_name, 
                                                geometry_id=self.geometry_id, 
                                                model=self.model)


        #     is_compressible= self.compressible,
        #     turbulence_model= self.turbulence_model,
        #     model= self.fluid_model_gravity,
        #     initial_conditions= self.initial_conditions,
        #     materials=CoupledConjugateHeatTransferMaterials(
        #         #fluids= self.fluid_material
        #         #,
        #         solids= self.solid_material
        #         ,
        # ),
        #     numerics= self.fluid_numerics,
            
        #     boundary_conditions= self.boundary_conditions,
        #     advanced_concepts= self.advanced_concepts,
        #     simulation_control= self.simulation_control,
        #     result_control= self.result_control,
        #     contact_handling_mode= self.contact_detection
        # )
        

        
    def create_simulation(self):
        self.simulation_id = self.simulation_api.create_simulation(
            self.project_id, 
            self.simulation_spec).simulation_id
        print(f"simulation_id: {self.simulation_id}")
    
    def reset_simulation_spec_components(self):
        
        # To avoid duplicate assignemnts between multiple simulations 
        self.fluid_material      = []
        self.solid_material      = []
        self.boundary_conditions = []
        self.velocity_inlet      = []
        self.velocity_outlet     = []
        self.pressure_inlet      = []
        self.pressure_outlet     = []
        self.wall_bc             = []
        self.power_sources       = []
        self.porous_media        = []
        self.momentum_sources    = []
        self.thermal_resistance_networks = []    
        self.surface_data        = []
        self.probe_points        = []
        self.field_calculations  = []
        self.mesh_refinement     = []        
        
    def set_mesh_layer_settings(self, num_of_layers = 3, total_rel_thickness = 0.4, growth_rate = 1.5):
        
        self.automatic_layer_settings = sim_sdk.AutomaticLayerOn(type="AUTOMATIC_LAYER_ON",
                                                                  		number_of_layers= num_of_layers,
                                                                  		total_relative_thickness= total_rel_thickness,
                                                                  		layer_type= sim_sdk.FractionalHeight2(
                                                                  			type="FRACTIONAL_HEIGHT_2",
                                                                  			growth_rate= growth_rate,)
                                                                          )
        
    def set_advanced_mesh_settings(self, small_feature_tolerance = 5E-5, gap_ref_factor = 0.05, gradation_rate = 1.22): 
        
        self.advanced_mesh_settings = sim_sdk.AdvancedSimmetrixSolidSettings(
                                    small_feature_tolerance= sim_sdk.DimensionalLength(value= small_feature_tolerance,unit="m",),
                                    gap_elements = gap_ref_factor, global_gradation_rate = gradation_rate)
    
    
    def complete_mesh_settings(self, mesh_name ,fineness = 5):
        # Start of mesh operation
        
        self.mesh_operation = self.mesh_operation_api.create_mesh_operation(
            self.project_id,
            sim_sdk.MeshOperation(
                name= mesh_name,
                geometry_id= self.geometry_id,
                model= sim_sdk.SimmetrixMeshingSolid(
                    sizing=AutomaticMeshSizingSimmetrix(type="AUTOMATIC_V9",fineness= fineness),
                    refinements = self.mesh_refinement,
                    advanced_simmetrix_settings = self.advanced_mesh_settings
                 ),
                ),
            )
        
        self.mesh_operation_id = self.mesh_operation.mesh_operation_id
        self.mesh_operation_api.update_mesh_operation( self.project_id, self.mesh_operation_id, self.mesh_operation)

    def set_local_element_size_refinement(self, element_size ,name = '',  key_list = []):
        #for later: add a method to add multiple entity selections automatically using get_entities
        faces_to_assign = []
        for key in key_list: 
            faces_to_assign.append(self.single_entity[key])
        
        self.mesh_refinement.append(   
                        sim_sdk.SimmetrixLocalSizingRefinement(
            			type="SIMMETRIX_LOCAL_SIZING_V10",
            			name= name,
            			max_element_size= sim_sdk.DimensionalLength(
            				value= element_size,
            				unit="m",
            			),
            			topological_reference= sim_sdk.TopologicalReference(
            				entities= faces_to_assign,
            				sets=[],
            			),
            		))
        
    def estimate_mesh_operation(self):
        
        # Estimate Mesh operation
        try:
            mesh_estimation = self.mesh_operation_api.estimate_mesh_operation(self.project_id, self.mesh_operation_id)
            # print(f"Mesh operation estimation: {mesh_estimation}")
            print("*"*10)
            print("Mesh operation estimation:")
            print("Number of cells: {lower} - {upper}. Expected is {avg}\n".format(
                                                               lower =  mesh_estimation.cell_count.interval_min, 
                                                               upper =  mesh_estimation.cell_count.interval_max,
                                                               avg   =  mesh_estimation.cell_count.value))
            
            print("CPU consumption: {lower} - {upper}. Expected is {avg}\n".format(
                                                               lower =  mesh_estimation.compute_resource.interval_min, 
                                                               upper =  mesh_estimation.compute_resource.interval_max,
                                                               avg   =  mesh_estimation.compute_resource.value))
            
            print("Duration: {lower} - {upper}. Expected is {avg}\n".format(
                                                               lower =  mesh_estimation.duration.interval_min.replace('PT',''), 
                                                               upper =  mesh_estimation.duration.interval_max.replace('PT', ''),
                                                               avg   =  mesh_estimation.duration.value.replace('PT','')))          
            print("*"*10)
            
            if mesh_estimation.compute_resource is not None and mesh_estimation.compute_resource.value > 150.0:
                raise Exception("Too expensive", mesh_estimation)
        
            if mesh_estimation.duration is not None:
                self.mesh_max_runtime = isodate.parse_duration(mesh_estimation.duration.interval_max).total_seconds()
                self.mesh_max_runtime = max(3600, self.mesh_max_runtime * 2)
            else:
                self.mesh_max_runtime = 36000
                print(f"Mesh operation estimated duration not available, assuming max runtime of {self.mesh_max_runtime} seconds")
        except ApiException as ae:
            if ae.status == 422:
                self.mesh_max_runtime = 36000
                print(f"Mesh operation estimation not available, assuming max runtime of {self.mesh_max_runtime} seconds")
            else:
                raise ae
                
    def check_simulation_and_mesh_settings(self):
        
        mesh_check = self.mesh_operation_api.check_mesh_operation_setup(self.project_id, self.mesh_operation_id, simulation_id= self.simulation_id)
        warnings = [entry for entry in mesh_check.entries if entry.severity == "WARNING"]
        if warnings: 
            # print(f"Meshing check warnings: {warnings}")
            print("Meshing check warning: {}\n".format(warnings[0].message))
        if len(warnings) > 1 :
            print("*"*10)
            # print(warnings[1].message)
            print("\nSimulation setup check warnings: {}".format(warnings[1].message))
        errors = [entry for entry in mesh_check.entries if entry.severity == "ERROR"]
        if errors:
            raise Exception("Simulation check failed", mesh_check)

    def start_meshing_operation(self, run_state = False):
        #for later: Figure out how to run the mesh operations in parallel without having to wait for each one to finish
        # The problem is related with retreiving the mesh id. It is possible that it is only attainable after the mesh operation is completed - investiagte...
        
        if run_state :
            self.mesh_operation_api.start_mesh_operation(self.project_id, self.mesh_operation_id, simulation_id= self.simulation_id)
        
        else: 
            
            self.mesh_operation_api.start_mesh_operation(self.project_id, self.mesh_operation_id, simulation_id= self.simulation_id)            
            # Wait until the meshing operation is complete
            self.mesh_operation = self.mesh_operation_api.get_mesh_operation(self.project_id, self.mesh_operation_id)
            mesh_operation_start = time.time()
            while self.mesh_operation.status not in ("FINISHED", "CANCELED", "FAILED"):
                if time.time() > mesh_operation_start + self.mesh_max_runtime:
                    raise TimeoutError()
                time.sleep(30)
                self.mesh_operation = self.mesh_operation_api.get_mesh_operation(self.project_id, self.mesh_operation_id)
                print(f"Meshing run status: {self.mesh_operation.status} - {self.mesh_operation.progress}")
            
            self.mesh_operation = self.mesh_operation_api.get_mesh_operation(self.project_id, self.mesh_operation_id)
            # print(f"final mesh_operation: {self.mesh_operation}")
            
            # Get the simulation spec and update it with mesh_id from the previous mesh operation
            self.simulation_spec = self.simulation_api.get_simulation(self.project_id, self.simulation_id)
            self.simulation_spec.mesh_id = self.mesh_operation.mesh_id
            self.simulation_api.update_simulation(self.project_id, self.simulation_id, self.simulation_spec)