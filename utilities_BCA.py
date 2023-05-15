# -*- coding: utf-8 -*-
"""
Created on Mon Jan 16 16:21:14 2023

@author: Kdeiri
"""

import os
import time
import zipfile
import pathlib
import isodate
import urllib3
import shutil
import pandas as pd

from simscale_sdk import Configuration, ApiClient, ProjectsApi, StorageApi, GeometryImportsApi, GeometriesApi, \
    MeshOperationsApi, SimulationsApi, SimulationRunsApi, ReportsApi, Project, GeometryImportRequest, ApiException, \
    MaterialsApi, MaterialGroupType, MaterialUpdateRequest, MaterialUpdateOperation, MaterialUpdateOperationReference
from simscale_sdk import ConvectiveHeatTransfer, CoupledConjugateHeatTransfer, FluidModel, DimensionalVectorAcceleration, FluidInitialConditions, \
    AdvancedConcepts, ConvectiveHeatTransferMaterials, CoupledConjugateHeatTransferMaterials, TopologicalReference, \
    FluidNumerics, RelaxationFactor, DimensionalPressure, ResidualControls, Tolerance, \
    FluidSolvers, Schemes, TimeDifferentiationSchemes, GradientSchemes, DivergenceSchemes, LaplacianSchemes, \
    InterpolationSchemes, SurfaceNormalGradientSchemes, VelocityInletBC, FixedValueVBC, DimensionalVectorFunctionSpeed, \
    ComponentVectorFunction, ConstantFunction, FixedValueTBC, DimensionalFunctionTemperature, PressureOutletBC, \
    FixedValuePBC, DimensionalFunctionPressure, WallBC, NoSlipVBC, FluidSimulationControl, DimensionalTime, \
    TimeStepWriteControl, ScotchDecomposeAlgorithm, FluidResultControls, AreaAverageResultControl, \
    ProbePointsResultControl, AbsolutePowerSource, DimensionalFunctionPower, IncompressibleMaterial, NewtonianViscosityModel, DimensionalKinematicViscosity, \
    DimensionalDensity, DimensionalThermalExpansionRate, DimensionalTemperature, DimensionalSpecificHeat, PBICGSolver, DILUPreconditioner, ILUCpPreconditioner, \
    SolidCompressibleMaterial, ConstIsoTransport, IsotropicConductivity, DimensionalFunctionThermalConductivity, \
    DimensionalSpecificHeat, HConstThermo, RhoConstEquationOfState, AutomaticMeshSizingSimmetrix, CrossPlaneOrthotropicConductivity, ConstCrossPlaneOrthotropicTransport

    
from simscale_sdk import GeometryImportRequestLocation, GeometryImportRequestOptions, Point, DimensionalVectorLength, \
    DecimalVector
from simscale_sdk import SimulationSpec, MeshOperation, SimmetrixMeshingFluid, AutomaticLayerOn, SimulationRun
from simscale_sdk import UserInputCameraSettings, ProjectionType, Vector3D, ModelSettings, Part, ScalarField, \
    ScreenshotOutputSettings, Color, ResolutionInfo, ScreenshotReportProperties, ReportRequest
    
import simscale_sdk as sim_sdk


class ConjugateHeatTransfer(): 
    
    def __init__(self): 
        
        #API Variables
        self.api_key        = ""
        self.api_url        = ""
        self.api_key_header = "X-API-KEY"
        self.version        = "/v0"
        self.host           = ""
        self.server         = "prod"
        
        #Client Variables
        self.api_client  = None
        self.project_api = None
        self.storage_api = None
        self.geometry_import_api = None
        self.geometry_api = None
        self.materials_api = None 
        self.mesh_operation_api = None 
        self.simulation_api = None
        self.simulation_run_api = None
        self.table_import_api =None
        self.reports_api = None
        
        #Project Variables 
        self.project_name = ""
        self.project_id   = ""
        
        #Geometry Variables
        self.geometry_name = ""
        self.geometry_id   = ""
        self.geometry_path = ""
        
        #Geometry Mapping 
        self.single_entity     = {} #for later: separate the faces from volumes and add a validation rule against duplicate assignments for the same entity (materials)
        self.multiple_entities = {}
        
        #Global Simulation Settings
        self.compressible = False
        self.turbulence_model = None
        self.fluid_model_gravity = None 
        self.initial_conditions = None 
        
        #Material Variables
        self.fluid_material = []
        self.solid_material = []
        
        #Numerics 
        self.fluid_numerics = None
        
        #Boundary Condition Variables 
        self.boundary_conditions = []
        self.velocity_inlet      = []
        self.velocity_outlet     = []
        self.pressure_inlet      = []
        self.pressure_outlet     = []
        self.wall_bc             = []
        
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
        
    def _get_variables_from_env(self):
        
        '''
        looks in your environment and reads the API variables
        
        SimScale API key and URL are read if they are set in the 
        environment as:
            
            SIMSCALE_API_KEY
            SIMSCALE_API_URL

        Returns
        -------
        None.

        '''
        # BCA Comment: How do I get these into my "environment"?
        try:
            self.api_key = os.getenv('SIMSCALE_API_KEY')
            print(self.api_key)
            self.api_url = os.getenv('SIMSCALE_API_URL')
            print(self.api_url)
            self.host = self.api_url + self.version
        except:
            raise Exception("Cannot get Keys from Environment Variables")
        
    def check_api(self):
        '''
        Check API key is set, returns boolean True if not set.
    
        Raises
        ------
        Exception
            If the API key and URL is not set, rasie an exception.
    
        Returns
        -------
        is_not_existent : boolean
            True if not set.
    
        '''
        is_not_existent = not os.getenv("SIMSCALE_API_KEY") or not os.getenv("SIMSCALE_API_URL")
        if is_not_existent:
            raise Exception(
                "Either `SIMSCALE_API_KEY` or `SIMSCALE_API_URL`",
                " environment variable is missing.")
            return is_not_existent
        else:
            print("SimScale API Key and URL found in environment variables.")

    def set_api_connection(self, version=0, server='prod'):
        '''
        Reads API key and URL and returns API clients required.
        
        ----------
        version : int
            Version of SimScale API, at time of writing, only 0 is valid.
            Default is 0.
        
        Returns
        -------
        api_client : object
            An API client that represents the user, and their login 
            credentials.
        api_key_header : object
        api_key : string
            A string that is your API key, read from the environment 
            variables.
        credential : SimscaleCredentials object
            An object contain api keys and credential information
    
        '''
        #Get the API url and key variables from env variables and do a sanity check 
        #self._get_variables_from_env()
        
        #BCA change- don't need the below for the moment.
        #self.check_api()
        
        #Setup the API configuration (define host and link the associated key)
        configuration = sim_sdk.Configuration()
        configuration.host = self.host
        configuration.api_key = {self.api_key_header: self.api_key}
        
        #Setup the API client connection 
        self.api_client = sim_sdk.ApiClient(configuration)
        retry_policy = urllib3.Retry(connect=5, read=5, redirect=0, status=5, backoff_factor=0.2)
        self.api_client.rest_client.pool_manager.connection_pool_kw["retries"] = retry_policy
       
        #Define the required API clients for the simulation 
        self.project_api = sim_sdk.ProjectsApi(self.api_client)
        self.storage_api = sim_sdk.StorageApi(self.api_client)
        self.geometry_import_api = sim_sdk.GeometryImportsApi(self.api_client)
        self.geometry_api = sim_sdk.GeometriesApi(self.api_client)
        self.mesh_operation_api = sim_sdk.MeshOperationsApi(self.api_client)
        self.materials_api = sim_sdk.MaterialsApi(self.api_client)
        self.simulation_api = sim_sdk.SimulationsApi(self.api_client)
        self.simulation_run_api = sim_sdk.SimulationRunsApi(self.api_client)
        self.table_import_api = sim_sdk.TableImportsApi(self.api_client)
        self.reports_api = sim_sdk.ReportsApi(self.api_client) 
        self.wind_api = sim_sdk.WindApi(self.api_client)
        
    def create_project(self, name, description, measurement_system = "SI"):
        '''
        Take a name and description and create a new workbench project

        Parameters
        ----------
        name : str
            A string with the exact name for the new project.
            
        description : str
            A string with the exact description for the new project.

        Returns
        -------
        None.

        '''
        
        try:
            #Check if the project already exists
            projects = self.project_api.get_projects(limit=1000).to_dict()['embedded']
            found = None
            for project in projects:
                if project['name'] == name:
                    found = project
                    print('Project found: \n' + str(found['name']))
                    break
            if found is None:
                raise Exception('could not find project with name: ' + name)
            
            self.project_id = found['project_id']
            self.project_name = name
            print("Cannot create project with the same name, using existing project")
        except:
            #If not then create a new project
            project = sim_sdk.Project(name=name, description=description,
                                      measurement_system = measurement_system)
            project = self.project_api.create_project(project)
            self.project_id = project.project_id
            self.project_name = name        
            
    def zip_cad_for_upload(self, file_name, base_path): 
     
         '''
         Take a list of the CAD file names and their associated path then zips 
         each CAD file separately and submits it for upload 
         
         Note: Have all the CAD files stored in the same directory
         
         Parameters
         ----------
         file_name : list
             A list with the exact names of the CAD files to upload
             
         base_path : Pathlib Path
             path to the directory that contains the CAD files 
     
         Returns
         -------
         geometry_path : path of the zipped file
     
         '''
         geometry_path = []
         
         #Loop over the CAD files needed for upload
         for cad in file_name:
             
             #Get the path of each CAD file
             path = base_path / cad
             
             # The output_filename variable saves the zip file at a desired path; 
             # in this case it is same directory
             output_filename = path
              
             #Retruns a zip file(s) path of the associated CAD, 
             geometry_path.append(shutil.make_archive(output_filename, 'zip', path)) 
     
         return geometry_path
 
    def upload_geometry(self, name, path=None, units="m", _format="PARASOLID"):
        
        '''
        Upload a geometry to the SimScale platform to a preassigned project.
        
        Parameters
        ----------
        name : str
            The name given to the geometry.
            
        path : pathlib.Path, optional
            The path to a geometry to upload. 
            
        units : str, optional
            the unit in which to upload the geometry to SimScale.
            
            The default is "m".
            
        _format : str, optional
            The file format. 
            
            The default is "STL".
            
        facet_split : bool, optional
            Decide on weather to split facet geometry (such as .stl file 
            types). We prefer not to do this for API use.
            
            The default is False.
    
        Raises
        ------
        TimeoutError
            DESCRIPTION.
    
        Returns
        -------
        None.
    
        '''
        self.geometry_name = name
        
        #Check if the geometry already exists
        try:
            project_id = self.project_id
            geometry_api = self.geometry_api
        
            geometries = geometry_api.get_geometries(project_id).to_dict()['embedded']
            found = None
            for geometry in geometries:
                if geometry['name'] == name:
                    found = geometry
                    print('Geometry found: \n' + str(found['name']))
                    break
                        
            if found is None:
                raise Exception('could not find geometry with id: ' + name)
                
            self.geometry_name = found
            self.geometry_id = found["geometry_id"]
            print("Cannot upload geometry with the same name, using existing geometry")
    
        except:
            
            self.geometry_path = path
    
            storage = self.storage_api.create_storage()
            with open(self.geometry_path, 'rb') as file:
                self.api_client.rest_client.PUT(url=storage.url, headers={'Content-Type': 'application/octet-stream'},
                                                body=file.read())
            self.storage_id = storage.storage_id
    
            geometry_import = sim_sdk.GeometryImportRequest(
                name=name,
                location=sim_sdk.GeometryImportRequestLocation(self.storage_id),
                format=_format,
                input_unit=units,
                options=sim_sdk.GeometryImportRequestOptions(facet_split= False, sewing=False, improve=True,
                                                         optimize_for_lbm_solver=False),
            )
    
            geometry_import = self.geometry_import_api.import_geometry(self.project_id, geometry_import)
            geometry_import_id = geometry_import.geometry_import_id
    
            geometry_import_start = time.time()
            while geometry_import.status not in ('FINISHED', 'CANCELED', 'FAILED'):
                # adjust timeout for larger geometries
                if time.time() > geometry_import_start + 900:
                    raise TimeoutError()
                time.sleep(10)
                geometry_import = self.geometry_import_api.get_geometry_import(self.project_id, geometry_import_id)
                print(f'Geometry import status: {geometry_import.status}')
            self.geometry_id = geometry_import.geometry_id


    # def get_geometry_BCA(self): #Get list of geometry on simscale.
    #     #Check if the geometry already exists
    #     try:
    #         project_id = self.project_id
    #         geometry_api = self.geometry_api
        
    #         geometries = geometry_api.get_geometries(project_id).to_dict()['embedded']
    #         found = None
    #         for geometry in geometries:
    #             if geometry['name'] == name:
    #                 found = geometry
    #                 print('Geometry found: \n' + str(found['name']))
    #                 break
                        
    #         if found is None:
    #             raise Exception('could not find geometry with id: ' + name)
                
    #         self.geometry_name = found
    #         self.geometry_id = found["geometry_id"]
    #         print("Cannot upload geometry with the same name, using existing geometry")    



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
                    unit="m"))
            
        elif direction == "y": 
            self.fluid_model_gravity = sim_sdk.FluidModel(
                gravity=sim_sdk.DimensionalVectorAcceleration(
                    value=sim_sdk.DecimalVector(x=0, y=value, z=0),
                    unit="m"))
        else:
            self.fluid_model_gravity = sim_sdk.FluidModel(
                gravity=sim_sdk.DimensionalVectorAcceleration(
                    value=sim_sdk.DecimalVector(x=0, y=0, z=value),
                    unit="m"))
            
    def set_initial_conditions(self):
        #Add code to allow setting the initial conditions for any parameter 
        self.initial_conditions = sim_sdk.FluidInitialConditions()
        
    
    def set_fluid_material_water(self, fluid_name = 'Water' , key = ''):
    
        #Add materials
        self.fluid_material.append(sim_sdk.IncompressibleMaterial(
                                        type="INCOMPRESSIBLE",
                                        name= fluid_name,
                                        viscosity_model=sim_sdk.NewtonianViscosityModel(
                                                type="NEWTONIAN",
                                                kinematic_viscosity=sim_sdk.DimensionalKinematicViscosity(
                                                        value=9.3379E-7,
                                                        unit="m²/s",
                                                ),
                                        ),
                                        density=sim_sdk.DimensionalDensity(
                                                value=997.33,
                                                unit="kg/m³",
                                        ),
                                        thermal_expansion_coefficient=sim_sdk.DimensionalThermalExpansionRate(
                                                value=2.07E-4,
                                                unit="1/K",
                                        ),
                                        reference_temperature=sim_sdk.DimensionalTemperature(
                                                value=298.15,
                                                unit="K",
                                        ),
                                        laminar_prandtl_number=6.5241,
                                        turbulent_prandtl_number=0.85,
                                        specific_heat=sim_sdk.DimensionalSpecificHeat(
                                                value=4180,
                                                unit="J/(kg·K)",
                                        ),
                                        topological_reference=sim_sdk.TopologicalReference(
                                                entities=[
                                                        self.single_entity[key],
                                                ],
                                                sets=[],
                                        ),
                                        built_in_material="builtInWater",
                                ),) 

    def set_fluid_material_air(self, fluid_name = "Air" ,key = ''):
        
        self.fluid_material.append(sim_sdk.IncompressibleMaterial(
                                        type="INCOMPRESSIBLE",
                                        name= fluid_name,
                                        viscosity_model=sim_sdk.NewtonianViscosityModel(
                                                type="NEWTONIAN",
                                                kinematic_viscosity=sim_sdk.DimensionalKinematicViscosity(
                                                        value=1.529e-5,
                                                        unit="m²/s",
                                                ),
                                        ),
                                        density=sim_sdk.DimensionalDensity(
                                                value=1.196,
                                                unit="kg/m³",
                                        ),
                                        thermal_expansion_coefficient=sim_sdk.DimensionalThermalExpansionRate(
                                                value=3.43e-3,
                                                unit="1/K",
                                        ),
                                        reference_temperature=sim_sdk.DimensionalTemperature(
                                                value=273.1,
                                                unit="K",
                                        ),
                                        laminar_prandtl_number=0.713,
                                        turbulent_prandtl_number=0.85,
                                        specific_heat=sim_sdk.DimensionalSpecificHeat(
                                                value=1004,
                                                unit="J/(kg·K)",
                                        ),
                                        topological_reference=sim_sdk.TopologicalReference(
                                                entities=[
                                                        self.single_entity[key],
                                                ],
                                                sets=[],
                                        ),
                                        built_in_material="builtInWater",
                                ),) 
        
    def add_fluid_material(self, fluid_name = 'Hydrogen' ,key = ''):
        
        #for later:Figure out how to add materials directly through the material library
        #without having to define the material properties manually
        
        # Add a material to the simulation
        
        # material_groups = self.materials_api.get_material_groups().embedded
        # default_material_group = next((group for group in material_groups if group.group_type == MaterialGroupType.SIMSCALE_DEFAULT), None)
        # if not default_material_group:
        #     raise Exception(f"Couldn't find default material group in {material_groups}")
        
        # default_materials = self.materials_api.get_materials(material_group_id=default_material_group.material_group_id).embedded
        # material_air = next((material for material in default_materials if material.name == fluid_name), None)
        # if not material_air:
        #     raise Exception(f"Couldn't find default Air material in {default_materials}")
        
        # material_data = self.materials_api.get_material_data(
        #     material_group_id=default_material_group.material_group_id,
        #     material_id=material_air.id
        # )
        # material_update_request = MaterialUpdateRequest(
        #     operations=[
        #         MaterialUpdateOperation(
        #             path="/materials/fluids",
        #             material_data=material_data,
        #             reference=MaterialUpdateOperationReference(
        #                 material_group_id=default_material_group.material_group_id,
        #                 material_id=material_air.id
        #             )
        #         )
        #     ]
        # )
        # self.fluid_material.append( self.simulation_api.update_simulation_materials(self.project_id, self.simulation_id, material_update_request))
        pass
    

    def set_solid_material_wood(self, solid_name = 'Wood' , key = ''):
        
        self.solid_material.append(    
                    sim_sdk.SolidCompressibleMaterial(
                            name="Wood",
                            transport=sim_sdk.ConstIsoTransport(
                                    type="CONST_ISO",
                                    conductivity=sim_sdk.IsotropicConductivity(
                                            type="ISOTROPIC",
                                            thermal_conductivity=sim_sdk.DimensionalFunctionThermalConductivity(
                                                    value=sim_sdk.ConstantFunction(
                                                            type="CONSTANT",
                                                            value=0.16,
                                                    ),
                                                    unit="W/(m·K)",
                                            ),
                                    ),
                                    thermo=sim_sdk.HConstThermo(
                                            type="HCONST",
                                            specific_heat=sim_sdk.DimensionalSpecificHeat(
                                                    value=1260,
                                                    unit="J/(kg·K)",
                                            ),
                                            equation_of_state=sim_sdk.RhoConstEquationOfState(
                                                    type="RHO_CONST",
                                                    density=sim_sdk.DimensionalDensity(
                                                            value=500,
                                                            unit="kg/m³",
                                                    ),
                                            ),
                                    ),
                            ),
                            topological_reference=sim_sdk.TopologicalReference(
                                    entities=
                                    [
                                        self.single_entity[key]
                                        ], 
                                    sets=[],
                            ),
                            built_in_material="builtInWood",
                    ),
                    )

    
    #def set_custom_solid_material(self, material_name = '',key = ''):
    def set_custom_solid_material(self,material_name='',material_conductivity='',key=''):    #BCA Edit- added material conductivity to be passed here
        self.solid_material.append( SolidCompressibleMaterial(
                                    name= material_name,
                                    transport=sim_sdk.ConstCrossPlaneOrthotropicTransport(
                                            type='CONST_CROSS_PLANE_ORTHO',
                                            conductivity=sim_sdk.CrossPlaneOrthotropicConductivity(
                                                    type="CROSS_PLANE_ORTHOTROPIC",
                                                    in_plane_conductivity=sim_sdk.DimensionalFunctionThermalConductivity(
                                                            value=sim_sdk.ConstantFunction(
                                                                    type="CONSTANT",
                                                                    value=material_conductivity, #BCA Edit!
                                                            ),
                                                            unit="W/(m·K)",
                                                    ),
                                                    cross_plane_conductivity=sim_sdk.DimensionalFunctionThermalConductivity(
                                                            value=sim_sdk.ConstantFunction(
                                                                    type="CONSTANT",
                                                                    value=material_conductivity,#BCA Edit!
                                                            ),
                                                            unit="W/(m·K)",
                                                    ),
                                            ),
                                            
                                            thermo=sim_sdk.HConstThermo(
                                                    type="HCONST",
                                                    specific_heat=sim_sdk.DimensionalSpecificHeat(
                                                            value=1027,
                                                            unit="J/(kg·K)",
                                                    ),
                                                    equation_of_state=sim_sdk.RhoConstEquationOfState(
                                                            type="RHO_CONST",
                                                            density=sim_sdk.DimensionalDensity(
                                                                    value=2560,
                                                                    unit="kg/m³",
                                                            ),
                                                    ),
                                            ),
                                    ),
                                    topological_reference=sim_sdk.TopologicalReference(
                                            entities=
                                                    [
                                                      #self.single_entity[key] #BCA comment- does this only do a single entity then?
                                                      key
                                                      ],
                                            sets=[],#Better to put the entities into sets first then just use this?
                                    ),
                                    #built_in_material="builtInAluminium",
                            ),)
    
    def set_simulation_numerics(self):
        
        self.fluid_numerics = sim_sdk.FluidNumerics(
                relaxation_type="MANUAL",
                relaxation_factor=sim_sdk.RelaxationFactor(
                        pressure_rgh_field=0.7,
                        velocity_equation=0.3,
                        temperature_equation=0.8,
                ),
                num_non_orthogonal_correctors=1,
                solvers=sim_sdk.FluidSolvers(
                        velocity_solver=sim_sdk.PBICGSolver(
                                type="PBICG",
                                absolute_tolerance=1.0E-15,
                                relative_tolerance=0.01,
                                preconditioner=sim_sdk.DILUPreconditioner(
                                        type="DILU",
                                ),
                        ),
                        temperature_solver=sim_sdk.PBICGSolver(
                                type="PBICG",
                                absolute_tolerance=1.0E-15,
                                relative_tolerance=0.01,
                                preconditioner=sim_sdk.ILUCpPreconditioner(
                                        type="ILUCP",
                                        fill_in_level=1,
                                ),
                        ),
                        pressure_rgh_solver=sim_sdk.ILUCpPreconditioner(
                                type="GAMG",
                                #absolute_tolerance=1.0E-15,
                                #relative_tolerance=0.01,
                                # smoother="GAUSSSEIDEL",
                                # num_pre_sweeps=1,
                                # num_post_sweeps=1,
                                # cache_agglomeration_on=True,
                                # num_cells_coarsest_level=100,
                                # num_merge_levels=1,
                        ),
                ),
                schemes=sim_sdk.Schemes(
                        second_order_convection=False,
                ),

            )
    
    def constant_velocity_inlet_bc(self, speed_x, speed_y, speed_z, temp,  name = "velocity inlet", key = ' '):
        
        self.velocity_inlet.append(
                sim_sdk.VelocityInletBC(
                name= name,
                velocity= sim_sdk.FixedValueVBC(
                value= sim_sdk.DimensionalVectorFunctionSpeed(
                    value= sim_sdk.ComponentVectorFunction(
                        x= sim_sdk.ConstantFunction(value= speed_x), 
                        y= sim_sdk.ConstantFunction(value=speed_y),
                        z= sim_sdk.ConstantFunction(value= speed_z)
                        )
                    )
                ),                
            temperature= sim_sdk.FixedValueTBC(
                value=DimensionalFunctionTemperature(value=sim_sdk.ConstantFunction(value= temp), unit="°C")
            ),        
            topological_reference=TopologicalReference(entities=[self.single_entity[key]]),
            ))


    def flow_rate_velocity_inlet():
        pass 
    


    def pressure_inlet_bc(self, value, temp ,name = "Pressure inlet" , unit = 'pa', key = ''):
        
        self.pressure_inlet.append(sim_sdk.PressureInletBC(
            name= name,
            gauge_pressure_rgh= sim_sdk.TotalPBC(
                type = "TOTAL_PRESSURE", total_pressure = sim_sdk.DimensionalFunctionPressure(value = sim_sdk.ConstantFunction(value= value), unit = unit))
            ,            
            temperature= sim_sdk.FixedValueTBC(
                value=DimensionalFunctionTemperature(value=sim_sdk.ConstantFunction(value= temp), unit="°C")
            ),
            topological_reference=TopologicalReference(entities=[self.single_entity[key]]),
        ))   
        
    def pressure_outlet_bc(self, value = 0 ,name = "Pressure outlet" , unit = 'pa', key = ''):
        
        self.pressure_outlet.append(sim_sdk.PressureOutletBC(
            name= name,
            gauge_pressure_rgh= sim_sdk.FixedValuePBC(
                value= sim_sdk.DimensionalFunctionPressure(value= sim_sdk.ConstantFunction(value= value ), unit= unit)
            ),
            topological_reference=sim_sdk.TopologicalReference(entities=[self.single_entity[key]]),
        ))
                
    def no_slip_fixed_temp_wall_bc(self, temp, name = "Fixed Temp" ,key_list = []):
         
        faces_to_assign = []
        for key in key_list: 
            # print(key)
            # print(self.single_entity[key])
            faces_to_assign.append(self.single_entity[key])
            # print(faces_to_assign)

        self.wall_bc.append(           
            sim_sdk.WallBC(
                    name= name,
                    velocity=sim_sdk.NoSlipVBC(),
                    temperature=sim_sdk.FixedValueTBC(
                        value=sim_sdk.DimensionalFunctionTemperature(value=sim_sdk.ConstantFunction(value=temp), unit="°C")
                    ),
                    topological_reference=sim_sdk.TopologicalReference(entities = faces_to_assign),
                ))

        
    def external_wall_heat_flux_bc(self, amb_temp = None , htc = None , heat_flux = None,
                                   power = None , method = "DERIVED" ,
                                   name = "stuff_of_the_heat_flux" ,
                                   key_list = []):
         
        faces_to_assign = []
        for key in key_list: 
            # print(key)
            # print(self.single_entity[key])
            faces_to_assign.append(self.single_entity[key])
            # print(faces_to_assign)
        
        if method == "DERIVED":
            #for later: add code that allows incorportaing wall thermals into the simulation
            if amb_temp and htc != None: 
                self.wall_bc.append(           
                    sim_sdk.WallBC(
                            name= name,
                            velocity=NoSlipVBC(),
                            temperature=sim_sdk.ExternalWallHeatFluxTBC(
                                heat_flux = sim_sdk.DerivedHeatFlux( 
                                    type = "DERIVED",
                                    heat_transfer_coefficient = sim_sdk.DimensionalThermalTransmittance(value = htc, unit = 'W/(K·m²)'), 
                                    ambient_temperature = sim_sdk.DimensionalTemperature(value= amb_temp, unit="°C"), 
                                    additional_heat_flux = None, 
                                    wall_thermal = None)
                            ),
                            topological_reference=TopologicalReference(entities = faces_to_assign),
                        ))
            else: 
               raise Exception("Provide the ambient temperature and heat transfer coefficient values")
                
        elif method == "FIXED":
            if heat_flux != None:
                self.wall_bc.append(           
                    sim_sdk.WallBC(
                            name= name,
                            velocity=NoSlipVBC(),
                            temperature=sim_sdk.ExternalWallHeatFluxTBC(
                                heat_flux = sim_sdk.FixedHeatFlux( 
                                    type = "FIXED",
                                    value = sim_sdk.DimensionalHeatFlux(value = heat_flux, unit = "W/m²" ))
                            ),
                            topological_reference=TopologicalReference(entities = faces_to_assign),
                        ))
            else: 
                raise Exception("Provide the heat flux value")
                
        elif method == "FIXED_POWER":
            if power != None: 
                self.wall_bc.append(           
                    sim_sdk.WallBC(
                            name= name,
                            velocity=NoSlipVBC(),
                            temperature=sim_sdk.ExternalWallHeatFluxTBC(
                                heat_flux = sim_sdk.FixedPowerHeatFlux( 
                                    type = "FIXED_POWER",
                                    value = sim_sdk.DimensionalPower(value = power, unit = "W" ))
                            ),
                            topological_reference=TopologicalReference(entities = faces_to_assign),
                        ))
            else: 
                raise Exception("Provide the power value")
                
    def set_boundary_conditions(self):
        #for later: add a validation against multiple face assignments for a BC
        #for later: think of how you can make this code better looking (one liners?)
                
        if len(self.velocity_inlet) >= 1 : 
            for v_inlet in self.velocity_inlet :
                if v_inlet in self.boundary_conditions:
                    continue
                else:
                    self.boundary_conditions.append(v_inlet)

        if len(self.velocity_outlet) >= 1 : 
            for v_outlet in self.velocity_outlet: 
                if v_outlet in self.boundary_conditions:
                    continue
                else:                
                    self.boundary_conditions.append(v_outlet)
                
        if len(self.pressure_inlet) >= 1 : 
            for p_inlet in self.pressure_inlet: 
                if p_inlet in self.boundary_conditions:
                    continue
                else:                
                    self.boundary_conditions.append(p_inlet)
                
        if len(self.pressure_outlet) >= 1 : 
            for p_outlet in self.pressure_outlet:
                if p_outlet in self.boundary_conditions:
                    continue
                else:                
                    self.boundary_conditions.append(p_outlet)
                
        if len(self.wall_bc) >= 1 : 
            for wall in self.wall_bc: 
                if wall in self.boundary_conditions:
                    continue
                else:                
                    self.boundary_conditions.append(wall)
      
        
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
    
    def set_simulation_control(self):
        
        self.simulation_control = sim_sdk.FluidSimulationControl(
            
                end_time= self.end_time,
                delta_t=  self.delta_t,
                write_control= self.write_control,
                max_run_time= self.max_run_time,
                decompose_algorithm=sim_sdk.ScotchDecomposeAlgorithm(),)
    
    def set_area_averages(self, name = "Area average", write_interval = 10, key_list = []):
        
        faces_to_assign = []
        for key in key_list: 
            faces_to_assign.append(self.single_entity[key])

        self.surface_data.append(
            sim_sdk.AreaAverageResultControl(
                name = name, 
                write_control = sim_sdk.TimeStepWriteControl(write_interval = write_interval),
                topological_reference = sim_sdk.TopologicalReference(entities = faces_to_assign),))


    def set_area_volumes(self, name = "Volume average", write_interval = 10 , key_list = []):
        
        faces_to_assign = []
        for key in key_list: 
            faces_to_assign.append(self.single_entity[key])

        self.surface_data.append(
            sim_sdk.AreaIntegralResultControl(
                name = name, 
                write_control = sim_sdk.TimeStepWriteControl(write_interval = write_interval),
                topological_reference = sim_sdk.TopologicalReference(entities = faces_to_assign),))

#BCA Edit
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
        
        
    def set_field_calculations(self):
        pass
    
    def set_result_control_items(self):
        
        self.result_control = sim_sdk.FluidResultControls(
            surface_data = self.surface_data, 
            probe_points = self.probe_points, 
            field_calculations = self.field_calculations)
        
    def set_contact_detection(self, method = "AUTO"):
        
        self.contact_detection = method
    

    def set_simulation_spec(self, simulation_name):
        """Simulation Setup"""
        # create simulation spec first to pass as reference to mesh operation for physics based meshing
        
        #Reset the spec to an intital state to avoid name conflict with the setup of simulations of different CAD
        self.simulation_spec = None 
        
        model = CoupledConjugateHeatTransfer(
            is_compressible= self.compressible,
            turbulence_model= self.turbulence_model,
            model= self.fluid_model_gravity,
            initial_conditions= self.initial_conditions,
            materials=CoupledConjugateHeatTransferMaterials(
                #fluids= self.fluid_material
                #,
                solids= self.solid_material
                ,
        ),
            numerics= self.fluid_numerics,
            
            #boundary_conditions= self.boundary_conditions
            #,
            #advanced_concepts= self.advanced_concepts
            #,
            #simulation_control= self.simulation_control
            #,
            #result_control= self.result_control 
            #,
            contact_handling_mode= self.contact_detection
        )
        
        self.simulation_spec = sim_sdk.SimulationSpec(name= simulation_name, geometry_id= self.geometry_id, model=model)
        self.simulation_id = self.simulation_api.create_simulation(self.project_id, self.simulation_spec).simulation_id
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
        
        self.advanced_mesh_settings = sim_sdk.AdvancedSimmetrixFluidSettings(
                                    small_feature_tolerance= sim_sdk.DimensionalLength(value= small_feature_tolerance,unit="m",),
                                    gap_elements = gap_ref_factor, global_gradation_rate = gradation_rate)
    
    
    def complete_mesh_settings(self, mesh_name ,fineness = 5, physics_based_meshing = True):
        # Start of mesh operation
        
        self.mesh_operation = self.mesh_operation_api.create_mesh_operation(
            self.project_id,
            sim_sdk.MeshOperation(
                name= mesh_name,
                geometry_id= self.geometry_id,
                model= sim_sdk.SimmetrixMeshingFluid(
                    physics_based_meshing= physics_based_meshing, hex_core = True, 
                    sizing=AutomaticMeshSizingSimmetrix(type="AUTOMATIC_V9",fineness= fineness),
                    refinements = self.mesh_refinement,
                    automatic_layer_settings= self.automatic_layer_settings,
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


    def estimate_simulation(self, maximum_cpu_consumption_limit = 200):
        
        try:
            estimation = self.simulation_api.estimate_simulation_setup(self.project_id, self.simulation_id)
            # print(f"Simulation estimation: {estimation}")
            
            print("*"*10)
            print("CPU consumption: {lower} - {upper}. Expected is {avg}\n".format(
                                                               lower =  estimation.compute_resource.interval_min, 
                                                               upper =  estimation.compute_resource.interval_max,
                                                               avg   =  estimation.compute_resource.value))
            
            print("Duration: {lower} - {upper}. Expected is {avg}\n".format(
                                                               lower =  estimation.duration.interval_min.replace('PT',''), 
                                                               upper =  estimation.duration.interval_max.replace('PT', ''),
                                                               avg   =  estimation.duration.value.replace('PT','')))          
            print("*"*10)
            
            if estimation.compute_resource is not None and estimation.compute_resource.value > maximum_cpu_consumption_limit:
                raise Exception("Too expensive", estimation)
        
            if estimation.duration is not None:
                self.sim_max_run_time = isodate.parse_duration(estimation.duration.interval_max).total_seconds()
                self.sim_max_run_time = max(3600, self.sim_max_run_time * 2)
            else:
                self.sim_max_run_time = 36000
                print(f"Simulation estimated duration not available, assuming max runtime of {self.sim_max_run_time} seconds")
        except ApiException as ae:
            if ae.status == 422:
                self.sim_max_run_time = 36000
                print(f"Simulation estimation not available, assuming max runtime of {self.sim_max_run_time} seconds")
            else:
                raise ae
        
    def create_simulation(self, sim_name ):
        
        self.simulation_run = sim_sdk.SimulationRun(name= sim_name)
        self.simulation_run = self.simulation_run_api.create_simulation_run(self.project_id, self.simulation_id, self.simulation_run)
        self.run_id = self.simulation_run.run_id
        print(f"runId: {self.run_id}")
        
        # Read simulation run and update with the deserialized model
        self.simulation_run = self.simulation_run_api.get_simulation_run(self.project_id, self.simulation_id, self.run_id)
        self.simulation_run_api.update_simulation_run(self.project_id, self.simulation_id, self.run_id, self.simulation_run)

    def start_simulation_run(self, run_state = True): 
        
        #Run simulation and don't wait until results are finished 
        if run_state : 
            # Start simulation run 
            self.simulation_run_api.start_simulation_run(self.project_id, self.simulation_id, self.run_id)
            self.simulation_run = self.simulation_run_api.get_simulation_run(self.project_id, self.simulation_id, self.run_id)
            
        #Run simulation and wait until results are finished 
        else: 
            self.simulation_run_api.start_simulation_run(self.project_id, self.simulation_id, self.run_id)
            self.simulation_run = self.simulation_run_api.get_simulation_run(self.project_id, self.simulation_id, self.run_id)
            simulation_run_start = time.time()
            while self.simulation_run.status not in ("FINISHED", "CANCELED", "FAILED"):
                if time.time() > simulation_run_start + self.sim_max_run_time:
                    raise TimeoutError()
                time.sleep(30)
                self.simulation_run = self.simulation_run_api.get_simulation_run(self.project_id, self.simulation_id, self.run_id)
                print(f"Simulation run status: {self.simulation_run.status} - {self.simulation_run.progress}")
            

    def get_simulation_results(self): 
        #for later: add functions that allows retreiving the project, simulation and run id of any project
        self.simulation_results = self.simulation_run_api.get_simulation_run_results(self.project_id, self.simulation_id, self.run_id)
        print(f"results: {self.simulation_results}")

    def get_probe_point_results(self, name, field = 'T', dir_name = "probe_point_results/"):
        #for later: add code that will run a validation if the probe points don't all have a field 
        # catch the error and move on. Do not terminate the script
        # and r.name == name
        self.probe_point_plot_info = [r for r in self.simulation_results._embedded if (r.category == "PROBE_POINT_PLOT" and r.name == name and r.quantity == field)][0]
        print(self.probe_point_plot_info)
        
        self.probe_point_plot_data_response = self.api_client.rest_client.GET(
            url= self.probe_point_plot_info.download.url, headers={self.api_key_header: self.api_key}, _preload_content=False
        )
        probe_point_plot_data_csv = self.probe_point_plot_data_response.data.decode("utf-8")
        print(f"Probe point plot data as CSV: {probe_point_plot_data_csv}")
        
        # Write probe points to CSV file
        probe_results_path = pathlib.Path(dir_name)
        try:
            #check if the directory already exists if not create a new one and store in it 
            probe_results_path.mkdir(parents = True, exist_ok = False)
            print("D")
            write_to = probe_results_path / "{}.csv".format(name)
            with open(write_to, "w") as file:
                file.write(probe_point_plot_data_csv)
        except: 
            #write to the already existing directory 
            probe_results_path.mkdir(parents = True, exist_ok = True)
            write_to = probe_results_path / "{}.csv".format(name)
            with open(write_to, "w") as file:
                file.write(probe_point_plot_data_csv)
    
    def get_surface_data_results(self, name, data_type = "average" , field = 'T', dir_name = "surface_data_results"): 
        #fields: 'Ux', 'Uy', 'Uz', 'p', 'k', 'T'
        
        if data_type == 'average': 
            area_average_result = [r for r in self.simulation_results._embedded if (r.category == "AREA_AVERAGE" and r.name == name and r.quantity == field)][0]
        
        else: 
            area_average_result = [r for r in self.simulation_results._embedded if (r.category == "AREA_INTEGRAL" and r.name == name and r.quantity == field)][0]
   
        area_average_result_response = self.api_client.rest_client.GET(
            url= area_average_result.download.url, headers={self.api_key_header: self.api_key}, _preload_content=False
        )
        area_average_results_csv = area_average_result_response.data.decode("utf-8")
        print(f"Area average result as CSV: {area_average_results_csv}")

        # Write area averages to CSV file
        area_average_result_path = pathlib.Path(dir_name)
        try:
            #check if the directory already exists if not create a new one and store in it 
            area_average_result_path.mkdir(parents = True, exist_ok = False)
            print("D")
            write_to = area_average_result_path / "{n}_{f}.csv".format(n = name, f = field)
            with open(write_to, "w") as file:
                file.write(area_average_results_csv)
        except: 
            #write to the already existing directory 
            area_average_result_path.mkdir(parents = True, exist_ok = True)
            write_to = area_average_result_path / "{n}_{f}.csv".format(n = name, f = field)
            with open(write_to, "w") as file:
                file.write(area_average_results_csv)
                
    def get_simulation_case_files(self): 
        
        self.solution_info = [r for r in self.simulation_results._embedded if r.category == "SOLUTION"][0]
        solution_response = self.api_client.rest_client.GET(
            url=self.solution_info.download.url, headers={self.api_key_header: self.api_key}, _preload_content=False)
        with open("case_file_solution.zip", "wb") as file:
               file.write(solution_response.data)
        zip = zipfile.ZipFile("case_file_solution.zip")
        print(f"Averaged solution ZIP file content: {zip.namelist()}")
    
    def get_simulation_report(self, part_id = "region1"):
        
        # Generating simulation run report
        camera_settings = sim_sdk.UserInputCameraSettings(
            projection_type= sim_sdk.ProjectionType.ORTHOGONAL,
            up= sim_sdk.Vector3D(0.5, 0.3, 0.2),
            eye= sim_sdk.Vector3D(0.0, 5.0, 10.0),
            center= sim_sdk.Vector3D(10.0, 12.0, 1.0),
            front_plane_frustum_height=0.5,
        )
        # "Temperature", component="X", data_type="CELL"
        model_settings = sim_sdk.ModelSettings(
            parts=[Part(part_identifier= part_id, solid_color=Color(0.8, 0.2, 0.4))],
            scalar_field=sim_sdk.ScalarField(field_name= "Velocity", component="X", data_type="CELL"),
        )
        output_settings = sim_sdk.ScreenshotOutputSettings(name="Output 1", format="PNG", resolution=ResolutionInfo(800, 800),
                                                   frame_index=0)
        report_properties = sim_sdk.ScreenshotReportProperties(
            model_settings=model_settings,
            filters=None,
            camera_settings=camera_settings,
            output_settings=output_settings,
        )
        report_request = sim_sdk.ReportRequest(name="Report 1", description="Simulation report", result_ids=[self.solution_info.result_id],
                                       report_properties=report_properties)
        
        create_report_response = self.reports_api.create_report(self.project_id, report_request)
        report_id = create_report_response.report_id
        
        # Start report job
        print(f"Starting report with ID {report_id}")
        report_job = self.reports_api.start_report_job(self.project_id, report_id)
        
        report = self.reports_api.get_report(self.project_id, report_id)
        
        while report.status not in ("FINISHED", "CANCELED", "FAILED"):
            time.sleep(30)
            report = self.reports_api.get_report(self.project_id, report_id)
        
        print(f"Report finished with status {report.status}")
        
        if report.status == "FINISHED":
            # Download the report
            print("Downloading report result")
            report_response = self.api_client.rest_client.GET(
                url=report.download.url,
                headers={self.api_key_header: self.api_key},
                _preload_content=False,
            )
        
            file_name = f"report.{report.download.format}"
            with open(file_name, "wb") as file:
                file.write(report_response.data)
                print(f"Finished downloading report with name {file_name}")
        elif report.status == "FAILED":
            raise Exception("Report generation failed", report.failure_reason)

    # def find_project(self, name):
    #     '''
    #     Take a project Name, return a project
    
    #     Parameters
    #     ----------
    #     name : string
    #         The exact name of the project, best copied from the SimScale
    #         UI.
    #     project_api : object
    #         An API object that can be used for querying and creating
    #         SimScale projects.
    
    #     Raises
    #     ------
    #     Exception
    #         Raise exception if the name matches no project in the clients*
    #         account.
    
    #         *client is created using the users API key, see create_client.
    #     Returns
    #     -------
    #     found : object
    #         A simulation object that was matched by the provided name.
    
    #     '''
    #     project_api = self.project_api
    
    #     projects = project_api.get_projects(limit=1000).to_dict()['embedded']
    #     found = None
    #     for project in projects:
    #         if project['name'] == name:
    #             found = project
    #             print('Project found: \n' + str(found['name']))
    #             break
    #     if found is None:
    #         raise Exception('could not find project with name: ' + name)
    
    #     self.project_id = found['project_id']
    #     self.project = name


    def find_simulation(self, name):
        
        '''
        Take a Simulation Name, return a simulation
    
        Parameters
        ----------
        name : string
            The exact name of the simulation, best copied from the SimScale 
            UI.
        project_id : object
            the ID of the project that you are searching, Simulations are 
            child objects of projects.
        simulation_api : object
            An API object that can be used for querying and creating 
            SimScale simulations..
    
        Raises
        ------
        Exception
            Raise exception if the name matches no simulation in the 
            project.
    
        Returns
        -------
        found : object
            A simulation object that was matched by the provided name.
    
        '''
        project_id = self.project_id
        simulation_api = self.simulation_api
    
        simulations = simulation_api.get_simulations(project_id).to_dict()['embedded']
        found = None
        for simulation in simulations:
            if simulation['name'] == name:
                found = simulation
                print('Simulation found: \n' + str(found['name']))
                break
        if found is None:
            raise Exception('could not find simulation with id: ' + name)
        self.simulation = found
        self.simulation_id = found["simulation_id"]
    
    
    # def find_geometry(self, name):
    #     '''
    #     Take a Simulation Name, return a simulation
    
    #     Parameters
    #     ----------
    #     name : string
    #         The exact name of the simulation, best copied from the SimScale
    #         UI.
    #     project_id : object
    #         the ID of the project that you are searching, Simulations are
    #         child objects of projects.
    #     simulation_api : object
    #         An API object that can be used for querying and creating
    #         SimScale simulations..
    
    #     Raises
    #     ------
    #     Exception
    #         Raise exception if the name matches no simulation in the
    #         project.
    
    #     Returns
    #     -------
    #     found : object
    #         A simulation object that was matched by the provided name.
    
    #     '''
    #     project_id = self.project_id
    #     geometry_api = self.geometry_api
    
    #     geometries = geometry_api.get_geometries(project_id).to_dict()['embedded']
    #     found = None
    #     for geometry in geometries:
    #         if geometry['name'] == name:
    #             found = geometry
    #             print('Geometry found: \n' + str(found['name']))
    #             break
    #     if found is None:
    #         raise Exception('could not find geometry with id: ' + name)
    #     self.geometry = found
    #     self.geometry_id = found["geometry_id"]
    
    
    def find_run(self, name):
        '''
        Take, name, parent simulation and parent project, return run.
    
        Parameters
        ----------
        name : string
            The exact name of the simulation run, best copied from the 
            SimScale UI.
        project_id : object
        simulation_id : object
        simulation_run_api : object
            An API object that can be used for querying and creating and 
            downloading SimScale simulation runs.
    
        Raises
        ------
        Exception
            Raise exception if the name matches no run in the parent 
            simulation.
    
        Returns
        -------
        found : TYPE
            DESCRIPTION.
    
        '''
        project_id = self.project_id
        simulation_id = self.simulation_id
        simulation_run_api = self.simulation_run_api
    
        runs = simulation_run_api.get_simulation_runs(
            project_id, simulation_id).to_dict()['embedded']
    
        found = None
        for run in runs:
            if run['name'] == name:
                found = run
                print('Run found: \n' + str(found['name']))
                break
        if found is None:
            raise Exception('could not find simulation with id: ' + name)
        self.run = found
        self.run_id = found["run_id"]