import time
import isodate
from simscale_sdk import ApiException
import simscale_sdk as sim_sdk

from simscale_sdk import AutomaticMeshSizingSimmetrix

class RunSimulation:
    def __init__(self, project_name, api_client, simulation_run_name):
        """
        Initialize the RunSimulation class with project_name, api_client, and simulation_run_name.
        The simulation_run_api and simulation_api will be instantiated inside the class.
        This constructor will also fetch the project_id based on the project_name.
        """
        self.project_name = project_name
        self.api_client = api_client
        self.simulation_run_name = simulation_run_name
        self.geometry_id = None
        self.sim_max_run_time = None

        # Instantiate APIs inside the class
        self.project_api = sim_sdk.ProjectsApi(api_client)
        self.simulation_run_api = sim_sdk.SimulationRunsApi(api_client)
        self.simulation_api = sim_sdk.SimulationsApi(api_client)
        self.mesh_operation_api = sim_sdk.MeshOperationsApi(api_client)

        # Fetch the project_id using the project name
        self.project_id = self.get_project_id_from_name()

        self.mesh_refinement = [] 

    def get_project_id_from_name(self):
        """
        Fetch the project ID based on the provided project name.
        """
        try:
            projects = self.project_api.get_projects(limit=1000).to_dict()['embedded']
            for project in projects:
                if project['name'] == self.project_name:
                    print(f"Project found: {project['name']}, ID: {project['project_id']}")
                    return project['project_id']
            raise Exception(f"Project with name '{self.project_name}' not found.")
        except ApiException as e:
            print(f"Exception when fetching projects: {e}")
            raise

    def find_simulation(self, name):
        """
        Find the simulation by name.
        """
        try:
            simulations = self.simulation_api.get_simulations(self.project_id).to_dict()['embedded']
            found = None
            for simulation in simulations:
                if simulation['name'] == name:
                    found = simulation
                    print(f'Simulation found: {found["name"]}')
                    break
            if found is None:
                raise Exception(f"Could not find simulation with name: {name}")
            self.simulation = found
            self.simulation_id = found["simulation_id"]
        except ApiException as e:
            print(f"Exception when fetching simulations: {e}")
            raise

    def estimate_simulation(self, maximum_cpu_consumption_limit=200):
        """
        Estimate the simulation setup.
        """
        try:
            estimation = self.simulation_api.estimate_simulation_setup(self.project_id, self.simulation_id)
            print("*" * 10)
            print("CPU consumption: {lower} - {upper}. Expected is {avg}".format(
                lower=estimation.compute_resource.interval_min,
                upper=estimation.compute_resource.interval_max,
                avg=estimation.compute_resource.value
            ))

            print("Duration: {lower} - {upper}. Expected is {avg}".format(
                lower=estimation.duration.interval_min.replace('PT', ''),
                upper=estimation.duration.interval_max.replace('PT', ''),
                avg=estimation.duration.value.replace('PT', '')))
            print("*" * 10)

            if estimation.compute_resource and estimation.compute_resource.value > maximum_cpu_consumption_limit:
                raise Exception("Too expensive", estimation)

            if estimation.duration:
                self.sim_max_run_time = isodate.parse_duration(estimation.duration.interval_max).total_seconds()
                self.sim_max_run_time = max(3600, self.sim_max_run_time * 2)
            else:
                self.sim_max_run_time = 36000
                print(f"Simulation estimated duration not available, assuming max runtime of {self.sim_max_run_time} seconds")
        except ApiException as e:
            print(f"Exception when estimating simulation: {e}")
            raise

    def create_simulation_run(self):
        """
        Create a new simulation run with the given simulation run name.
        """
        try:
            self.simulation_run = sim_sdk.SimulationRun(name=self.simulation_run_name)
            self.simulation_run = self.simulation_run_api.create_simulation_run(self.project_id, self.simulation_id, self.simulation_run)
            self.run_id = self.simulation_run.run_id
            print(f"Simulation run ID: {self.run_id}")
        except ApiException as e:
            print(f"Exception when creating simulation run: {e}")
            raise

    def start_simulation_run(self, wait_for_results=True):
        """
        Start the simulation run and optionally wait for the results to complete.
        """
        try:
            self.simulation_run_api.start_simulation_run(self.project_id, self.simulation_id, self.run_id)
            if wait_for_results:
                simulation_run_start = time.time()
                self.simulation_run = self.simulation_run_api.get_simulation_run(self.project_id, self.simulation_id, self.run_id)

                while self.simulation_run.status not in ("FINISHED", "CANCELED", "FAILED"):
                    if time.time() > simulation_run_start + self.max_run_time:
                        raise TimeoutError("Simulation took too long to finish.")
                    time.sleep(30)
                    self.simulation_run = self.simulation_run_api.get_simulation_run(self.project_id, self.simulation_id, self.run_id)
                    print(f"Simulation run status: {self.simulation_run.status} - {self.simulation_run.progress}")
        except ApiException as e:
            print(f"Exception when starting simulation run: {e}")
            raise


    def set_mesh_layer_settings(self, num_of_layers=3, total_rel_thickness=0.4, growth_rate=1.5):
        """
        Set the mesh layer settings.
        """
        self.automatic_layer_settings = sim_sdk.AutomaticLayerOn(
            type="AUTOMATIC_LAYER_ON",
            number_of_layers=num_of_layers,
            total_relative_thickness=total_rel_thickness,
            layer_type=sim_sdk.FractionalHeight2(type="FRACTIONAL_HEIGHT_2", growth_rate=growth_rate)
        )

    def set_advanced_mesh_settings(self, small_feature_tolerance=5E-5, gap_ref_factor=0.05, gradation_rate=1.22):
        """
        Set advanced mesh settings.
        """
        self.advanced_mesh_settings = sim_sdk.AdvancedSimmetrixFluidSettings(
            small_feature_tolerance=sim_sdk.DimensionalLength(value=small_feature_tolerance, unit="m"),
            gap_elements=gap_ref_factor, global_gradation_rate=gradation_rate
        )

    def complete_mesh_settings(self, mesh_name, fineness=5, physics_based_meshing=True):
        """
        Complete mesh settings and create mesh operation.
        """
        geometry_idx = self.simulation_api.get_simulation(self.project_id, self.simulation_id)
        self.geometry_id = geometry_idx.geometry_id
        print('!!!printing geometry id:')
        print(self.geometry_id)
        self.mesh_operation = self.mesh_operation_api.create_mesh_operation(
            self.project_id,
            sim_sdk.MeshOperation(
                name=mesh_name,
                geometry_id=self.geometry_id,
                model=sim_sdk.SimmetrixMeshingFluid(
                    physics_based_meshing=physics_based_meshing,
                    hex_core=True,
                    sizing=AutomaticMeshSizingSimmetrix(type="AUTOMATIC_V9", fineness=fineness),
                    refinements=self.mesh_refinement,
                    automatic_layer_settings=self.automatic_layer_settings,
                    advanced_simmetrix_settings=self.advanced_mesh_settings
                ),
            ),
        )
        self.mesh_operation_id = self.mesh_operation.mesh_operation_id
        self.mesh_operation_api.update_mesh_operation(self.project_id, self.mesh_operation_id, self.mesh_operation)


    def estimate_mesh_operation(self):
        """
        Estimate the mesh operation.
        """
        try:
            mesh_estimation = self.mesh_operation_api.estimate_mesh_operation(self.project_id, self.mesh_operation_id)
            print("*" * 10)
            print("Mesh operation estimation:")
            print("Number of cells: {lower} - {upper}. Expected is {avg}".format(
                lower=mesh_estimation.cell_count.interval_min,
                upper=mesh_estimation.cell_count.interval_max,
                avg=mesh_estimation.cell_count.value
            ))

            print("CPU consumption: {lower} - {upper}. Expected is {avg}".format(
                lower=mesh_estimation.compute_resource.interval_min,
                upper=mesh_estimation.compute_resource.interval_max,
                avg=mesh_estimation.compute_resource.value
            ))

            print("Duration: {lower} - {upper}. Expected is {avg}".format(
                lower=mesh_estimation.duration.interval_min.replace('PT', ''),
                upper=mesh_estimation.duration.interval_max.replace('PT', ''),
                avg=mesh_estimation.duration.value.replace('PT', '')))
            print("*" * 10)

            if mesh_estimation.compute_resource and mesh_estimation.compute_resource.value > 150.0:
                raise Exception("Too expensive", mesh_estimation)

            if mesh_estimation.duration:
                self.mesh_max_runtime = isodate.parse_duration(mesh_estimation.duration.interval_max).total_seconds()
                self.mesh_max_runtime = max(3600, self.mesh_max_runtime * 2)
            else:
                self.mesh_max_runtime = 36000
                print(f"Mesh operation estimated duration not available, assuming max runtime of {self.mesh_max_runtime} seconds")
        except ApiException as e:
            if e.status == 422:
                self.mesh_max_runtime = 36000
                print(f"Mesh operation estimation not available, assuming max runtime of {self.mesh_max_runtime} seconds")
            else:
                raise e

    def start_meshing_operation(self, run_state=False):
        """
        Start the meshing operation and wait until it is finished.
        """
        try:
            if run_state:
                self.mesh_operation_api.start_mesh_operation(self.project_id, self.mesh_operation_id, simulation_id=self.simulation_id)
            else:
                self.mesh_operation_api.start_mesh_operation(self.project_id, self.mesh_operation_id, simulation_id=self.simulation_id)
                mesh_operation_start = time.time()
                self.mesh_operation = self.mesh_operation_api.get_mesh_operation(self.project_id, self.mesh_operation_id)

                while self.mesh_operation.status not in ("FINISHED", "CANCELED", "FAILED"):
                    if time.time() > mesh_operation_start + self.mesh_max_runtime:
                        raise TimeoutError("Meshing took too long to finish.")
                    time.sleep(30)
                    self.mesh_operation = self.mesh_operation_api.get_mesh_operation(self.project_id, self.mesh_operation_id)
                    print(f"Meshing run status: {self.mesh_operation.status} - {self.mesh_operation.progress}")
                
                self.simulation_spec = self.simulation_api.get_simulation(self.project_id, self.simulation_id)
                self.simulation_spec.mesh_id = self.mesh_operation.mesh_id
                self.simulation_api.update_simulation(self.project_id, self.simulation_id, self.simulation_spec)
        except ApiException as e:
            print(f"Exception when starting meshing operation: {e}")
            raise


    def set_simulation_max_run_time(self, max_run_time=40000):
        """
        Set the maximum run time for the simulation in seconds.
        """
        # Convert max_run_time to a float representing the number of seconds
        self.max_run_time = float(max_run_time)


    def check_simulation_and_mesh_settings(self):
        """
        Check the simulation and mesh settings for warnings or errors.
        """
        try:
            mesh_check = self.mesh_operation_api.check_mesh_operation_setup(
                self.project_id, self.mesh_operation_id, simulation_id=self.simulation_id
            )
            warnings = [entry for entry in mesh_check.entries if entry.severity == "WARNING"]
            if warnings:
                print(f"Meshing check warning: {warnings[0].message}")

            if len(warnings) > 1:
                print("*" * 10)
                print(f"Simulation setup check warnings: {warnings[1].message}")

            errors = [entry for entry in mesh_check.entries if entry.severity == "ERROR"]
            if errors:
                raise Exception("Simulation check failed", mesh_check)
        except ApiException as e:
            print(f"Exception when checking simulation and mesh settings: {e}")
            raise