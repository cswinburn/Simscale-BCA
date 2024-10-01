import simscale_sdk as sim_sdk

class GetSimulationRuns:
    def __init__(self, api_client, project_name, simulation_name):
        """
        Initialize the class with the project name and simulation name.
        """
        self.api_client = api_client
        self.project_name = project_name
        self.simulation_name = simulation_name

        # Define the required API clients
        self.project_api = sim_sdk.ProjectsApi(self.api_client)
        self.simulation_api = sim_sdk.SimulationsApi(self.api_client)
        self.simulation_run_api = sim_sdk.SimulationRunsApi(self.api_client)

    def get_simulation_runs(self):
        """
        Get the list of simulation runs (names and IDs) for a given project and simulation name.
        """
        try:
            # Get the project ID from the project name
            projects = self.project_api.get_projects(limit=1000).to_dict()['embedded']
            project_id = None
            for project in projects:
                if project['name'] == self.project_name:
                    project_id = project['project_id']
                    break  # Stop once we find the project

            if not project_id:
                raise Exception(f"Project with name '{self.project_name}' not found.")

            # Get the simulation ID from the simulation name
            simulations = self.simulation_api.get_simulations(project_id).to_dict()['embedded']
            simulation_id = None
            for simulation in simulations:
                if simulation['name'] == self.simulation_name:
                    simulation_id = simulation['simulation_id']
                    break  # Stop once we find the simulation

            if not simulation_id:
                raise Exception(f"Simulation with name '{self.simulation_name}' not found.")

            # Get all simulation runs for the given simulation ID
            simulation_runs = self.simulation_run_api.get_simulation_runs(project_id, simulation_id).to_dict()['embedded']

            # Extract project names
            sim_run_names = [sim_run['name'] for sim_run in simulation_runs]
        
            return sim_run_names  # Return a list of project names

        except Exception as e:
            print(f"Error retrieving simulation runs: {e}")
            return []
