import time   
import simscale_sdk as sim_sdk

class GetGeometries:
    def __init__(self, api_client, project_name):
        
        self.api_client = api_client

        #Define the required API clients for the simulation 
        
        self.storage_api = sim_sdk.StorageApi(self.api_client)
        self.geometry_import_api = sim_sdk.GeometryImportsApi(self.api_client)
        self.geometry_api = sim_sdk.GeometriesApi(self.api_client)
        self.project_api = sim_sdk.ProjectsApi(self.api_client)
        self.project_name = project_name
        
    def get_geometries(self): #BCA- major changes to this section
            
            '''
            Get geometries for a given SimScale project.

            '''
            
            #Check if the geometry already exists
            geometry_api = self.geometry_api
            project_name = self.project_name

            try:
                # Fetch the projects
                projects = self.project_api.get_projects(limit=1000).to_dict()['embedded']
                project_id = None

                for project in projects:
                    if project['name'] == project_name:
                        project_id = project['project_id']
                        break  # Stop iterating once we find the project

                geometries = geometry_api.get_geometries(project_id).to_dict()['embedded']
                
                if not geometries:
                    print("No geometries found.")
                    return []
                
                # Extract project names
                geometry_names = [geometry['name'] for geometry in geometries]
            
                return geometry_names  # Return a list of project names
            
            except Exception as e:
                print(f'Error retrieving geometries: {e}')
                return []

