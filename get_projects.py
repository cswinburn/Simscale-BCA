import simscale_sdk as sim_sdk

class GetProjects:

    def __init__(self, api_client):
        self.api_client = api_client
        # Define the required API clients for the simulation
        self.project_api = sim_sdk.ProjectsApi(self.api_client)
        
    def get_existing_projects(self):
        '''
        Retrieve and return a list of existing projects.

        Returns
        -------
        list : A list of project names.
        '''
        
        try:
            # Fetch the projects
            projects_response = self.project_api.get_projects(limit=1000)
            projects = projects_response.to_dict().get('embedded', [])
            
            if not projects:
                print("No projects found.")
                return []
            
            # Extract project names
            project_names = [project['name'] for project in projects]
        
            return project_names  # Return a list of project names
            
        except Exception as e:
            print(f'Error retrieving projects: {e}')
            return []

# Example usage of the FolderNavigation class
if __name__ == "__main__":
    # You should replace `api_client` with your actual client initialization code
    api_client = sim_sdk.ApiClient()  # Initialize with proper config and auth
    folder_nav = FolderNavigation(api_client)

    # Call the get_existing_projects method and print the result
    result = folder_nav.get_existing_projects()
    print("Existing project names:", result)
