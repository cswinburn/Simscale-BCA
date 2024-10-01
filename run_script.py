from api_key_manager import APIKeyManager
from folder_navigation import FolderNavigation
from get_geometries import GetGeometries
from simulation_setup import SimulationSetup

def main():
    # Step 1: Initialize the API key manager and set up the connection
    api_key_manager = APIKeyManager()
    api_key_manager.set_api_connection()  # This retrieves the API key from env and sets up the API client
    
    # Step 2: Get the API client from the key manager
    api_client = api_key_manager.api_client
    
    # # Step 3: Initialize FolderNavigation with the API client
    # folder_nav = FolderNavigation(api_client)
    
    # # Step 4: Fetch existing projects and print them
    # projects = folder_nav.get_existing_projects()
    
    # # Output the project names
    # print("Projects:", projects)

    
     # Step 3: Initialize FolderNavigation with the API client
    folder_nav = GetGeometries(api_client, project_name = "Milo Test 00")

    #sim_nav = SimulationSetup(api_client, geometry_api, geometry_id, project_id)
    
    # Step 4: Fetch existing projects and print them
    geometries = folder_nav.get_geometries()
    
    # Output the project names
    print("Geometries:", geometries)

    sims = 

if __name__ == "__main__":
    main()
