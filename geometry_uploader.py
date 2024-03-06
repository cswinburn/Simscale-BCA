import time   
import simscale_sdk as sim_sdk

class GeometryUploader:
    def __init__(self, api_client, project_id):
        
        self.api_client = api_client
        self.project_id = project_id

        #Define the required API clients for the simulation 
        
        self.storage_api = sim_sdk.StorageApi(self.api_client)
        self.geometry_import_api = sim_sdk.GeometryImportsApi(self.api_client)
        self.geometry_api = sim_sdk.GeometriesApi(self.api_client)
        
    def upload_geometry(self, name, path=None, units="m", _format="STEP"): #BCA- major changes to this section
            
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
            project_id = self.project_id
            geometry_api = self.geometry_api
        
            geometries = geometry_api.get_geometries(project_id).to_dict()['embedded']
            found = None
            for geometry in geometries:
                if geometry['name'] == name:
                    found = geometry
                    print('Geometry found: \n' + str(found['name']))
                    name=name + '1' #Add a 1 to show it is a new geometry (needs a better way)
                    break
                        
            #if found is None:
            #    raise Exception('could not find geometry with id: ' + name)
                
            #self.geometry_name = found
            #self.geometry_id = found["geometry_id"]
            #print("Cannot upload geometry with the same name, using existing geometry")
                
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
                                                        optimize_for_lbm_solver=False), #BCA should facet split be true?
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