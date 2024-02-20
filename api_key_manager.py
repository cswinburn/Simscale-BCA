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

    
class APIKeyManager:
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
            raise Exception("Cannot get Keys from Environment Variables!")

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
        self._get_variables_from_env()
        
        #BCA change- don't need the below for the moment.
        self.check_api()
        
        #Setup the API configuration (define host and link the associated key)
        configuration = sim_sdk.Configuration()
        configuration.host = self.host
        configuration.debug = True
        configuration.api_key = {self.api_key_header: self.api_key}
        
        #Setup the API client connection 
        self.api_client = sim_sdk.ApiClient(configuration)
        retry_policy = urllib3.Retry(connect=5, read=5, redirect=0, status=5, backoff_factor=0.2)
        self.api_client.rest_client.pool_manager.connection_pool_kw["retries"] = retry_policy

        
       
        
       
        

