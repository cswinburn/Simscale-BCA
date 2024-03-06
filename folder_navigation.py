import shutil    
import simscale_sdk as sim_sdk

class FolderNavigation:

    def __init__(self, api_client):

        self.api_client = api_client
        #Define the required API clients for the simulation 
        self.project_api = sim_sdk.ProjectsApi(self.api_client)
        #Project Variables 
        self.project_name = ""
        self.project_id   = ""
        
        #Geometry Variables
        self.geometry_name = ""
        self.geometry_id   = ""
        self.geometry_path = ""
        
        
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