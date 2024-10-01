import time   
import simscale_sdk as sim_sdk

class GetSimulations:
    def __init__(self, api_client, project_name):
        
        self.api_client = api_client

        #Define the required API clients for the simulation 
        
        self.storage_api = sim_sdk.StorageApi(self.api_client)
        self.project_api = sim_sdk.ProjectsApi(self.api_client)
        self.project_name = project_name
        self.simulation_api = sim_sdk.SimulationsApi(self.api_client)
        
    def get_simulations(self): #BCA- major changes to this section
            
            '''
            Get geometries for a given SimScale project.

            '''
            
            #Check if the geometry already exists
            project_name = self.project_name

            try:
                projects = self.project_api.get_projects(limit=1000).to_dict()['embedded']
                # Fetch the sims
                project_id = None

                for project in projects:
                    if project['name'] == project_name:
                        project_id = project['project_id']
                        break  # Stop iterating once we find the project

                simulations = self.simulation_api.get_simulations(project_id).to_dict()['embedded']
                #projects = self.project_api.get_projects(limit=1000).to_dict()['embedded']

                
                if not simulations:
                    print("No geometries found.")
                    return []
                
                # Extract project names
                sim_names = [sim['name'] for sim in simulations]
            
                return sim_names  # Return a list of project names
            
            except Exception as e:
                print(f'Error retrieving geometries: {e}')
                return []

