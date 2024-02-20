import os
import time
import zipfile
import pathlib
import isodate
import urllib3
import shutil
#import pandas as pd #Don't think we need this for now. Doesn't work in Rhino currently.

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


class RunSimulation:
    def __init__(self, simulation_run_api, project_id, simulation_api):
         
        self.simulation_run_api = simulation_run_api
        self.project_id = project_id
        self.simulation_api = simulation_api
          
         
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
        

    def create_simulation_run(self, sim_name ):
        self.simulation_run = sim_sdk.SimulationRun(name= sim_name)
        self.simulation_run = self.simulation_run_api.create_simulation_run(self.project_id, self.simulation_id, self.simulation_run) #ERROR HERE
        self.run_id = self.simulation_run.run_id
        print(f"runId: {self.run_id}")
        
        # Read simulation run and update with the deserialized model
        self.simulation_run = self.simulation_run_api.get_simulation_run(self.project_id, self.simulation_id, self.run_id)
        self.simulation_run_api.update_simulation_run(self.project_id, self.simulation_id, self.run_id, self.simulation_run)

    def start_simulation_run(self, wait_for_results = True): 
            
            '''
            submit the simulation to solve
            
            Parameters
            ----------
            
            wait_for_results: boolean  
            
                if True - then the simulation run is put on queue and the process 
                waits until the simulation results are obtained before moving on 
                
                this can be helpful if you want to download the results or process them 
                automatically in the same script, which means that you would need 
                to get the results first 
            
            Returns
            -------
            None. 
            
            '''            
            #Run simulation and don't wait until results are finished 
            if not wait_for_results : 
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

    