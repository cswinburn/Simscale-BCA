
import pathlib
import time
import zipfile
import csv
from io import StringIO
import simscale_sdk as sim_sdk

class PostProcess:
    def __init__(self, api_client, project_name, sim_name, run_name, api_key, api_key_header):
        """
        Initialize PostProcess class with project, simulation, and run names.
        Fetches project_id, simulation_id, and run_id based on the names provided.
        """
        self.api_key = api_key
        self.api_key_header = api_key_header
        self.api_client = api_client

        self.simulation_run_api = sim_sdk.SimulationRunsApi(self.api_client)
        self.simulation_run = None
        self.simulation_runs = None
        self.project_api = sim_sdk.ProjectsApi(self.api_client)
        self.simulation_api = sim_sdk.SimulationsApi(self.api_client)
        
        # Set project, simulation, and run names
        self.project_name = project_name
        self.sim_name = sim_name
        self.run_name = run_name
        
        # Fetch project_id, simulation_id, and run_id
        self.project_id = self.get_project_id(self.project_name)
        self.simulation_id = self.get_simulation_id(self.sim_name)
        self.run_id = self.get_run_id(self.run_name)

    def get_project_id(self, project_name):
        """
        Fetch project_id based on project name.
        """
        projects = self.project_api.get_projects(limit=1000).to_dict()['embedded']
        for project in projects:
            if project['name'] == project_name:
                print(f"Project found: {project['name']} with ID: {project['project_id']}")
                return project['project_id']
        raise Exception(f'Project with name "{project_name}" not found.')
    
    def get_simulation_id(self, sim_name):
        """
        Fetch simulation_id based on simulation name.
        """
        simulations = self.simulation_api.get_simulations(self.project_id).to_dict()['embedded']
        for simulation in simulations:
            if simulation['name'] == sim_name:
                print(f"Simulation found: {simulation['name']} with ID: {simulation['simulation_id']}")
                return simulation['simulation_id']
        raise Exception(f'Simulation with name "{sim_name}" not found.')
    
    def get_run_id(self, run_name):
        """
        Fetch run_id based on simulation run name.
        """
        self.simulation_runs = self.simulation_run_api.get_simulation_runs(self.project_id, self.simulation_id).to_dict()['embedded']
        for simulation_run in self.simulation_runs:
            if simulation_run['name'] == run_name:
                print(f"Simulation run found: {simulation_run['name']} with ID: {simulation_run['run_id']}")
                return simulation_run['run_id']
        raise Exception(f'Simulation run with name "{run_name}" not found.')

    def get_simulation_results(self): 
        """
        Fetch simulation results for the run.
        """
        self.simulation_results = self.simulation_run_api.get_simulation_run_results(self.project_id, self.simulation_id, self.run_id)
        print(f"Simulation results fetched for project ID: {self.project_id}, simulation ID: {self.simulation_id}, run ID: {self.run_id}")

    def get_probe_point_results(self, name, field = 'T', dir_name = "probe_point_results/"):
        #for later: add code that will run a validation if the probe points don't all have a field 
        # catch the error and move on. Do not terminate the script
        # and r.name == name
        self.probe_point_plot_info = [r for r in self.simulation_results._embedded if (r.category == "PROBE_POINT_PLOT" and r.name == name and r.quantity == field)][0]
        print(self.probe_point_plot_info)
        
        self.probe_point_plot_data_response = self.api_client.rest_client.GET(
            url= self.probe_point_plot_info.download.url, headers={self.api_key_header: self.api_key}, _preload_content=False
        )
        probe_point_plot_data_csv = self.probe_point_plot_data_response.data.decode("utf-8")
        print(f"Probe point plot data as CSV: {probe_point_plot_data_csv}")
        
        # Write probe points to CSV file
        probe_results_path = pathlib.Path(dir_name)
        try:
            #check if the directory already exists if not create a new one and store in it 
            probe_results_path.mkdir(parents = True, exist_ok = False)
            print("D")
            write_to = probe_results_path / "{}.csv".format(name)
            with open(write_to, "w") as file:
                file.write(probe_point_plot_data_csv)
        except: 
            #write to the already existing directory 
            probe_results_path.mkdir(parents = True, exist_ok = True)
            write_to = probe_results_path / "{}.csv".format(name)
            with open(write_to, "w") as file:
                file.write(probe_point_plot_data_csv)
    
    def get_surface_data_results(self, name, data_type = "average" , field = 'T', dir_name = "surface_data_results"): 
        #fields: 'Ux', 'Uy', 'Uz', 'p', 'k', 'T','wallHeatFlux'
        
        if data_type == 'average': 
            area_average_result = [r for r in self.simulation_results._embedded if (r.category == "AREA_AVERAGE" and r.name == name and r.quantity == field)][0]
        
        else: 
            area_average_result = [r for r in self.simulation_results._embedded if (r.category == "AREA_INTEGRAL" and r.name == name and r.quantity == field)][0]
   
        area_average_result_response = self.api_client.rest_client.GET(
            url= area_average_result.download.url, headers={self.api_key_header: self.api_key}, _preload_content=False
        )
        area_average_results_csv = area_average_result_response.data.decode("utf-8")
        #print(f"Area average result as CSV: {area_average_results_csv}")

        # Path object for the directory
        home_dir = pathlib.Path.home()
        area_average_result_path = home_dir / dir_name

        # Check if the directory does not exist
        if not area_average_result_path.exists():
            # Try to create the directory
            try:
                area_average_result_path.mkdir(parents=True, exist_ok=True)
                print("Directory created:", area_average_result_path)
            except PermissionError as e:
                print(f"Permission error when creating directory: {e}")
                return None

        # The directory either existed already or was successfully created, proceed with file writing
        write_to = area_average_result_path / f"{name}_{field}.csv"
        try:
            with open(write_to, "w") as file:
                file.write(area_average_results_csv)
            print("File written:", write_to)
        except Exception as e:
            print(f"Error writing CSV file: {e}")
            return None

        return area_average_results_csv

        
    def get_simulation_case_files(self): 
        
        self.solution_info = [r for r in self.simulation_results._embedded if r.category == "SOLUTION"][0]
        solution_response = self.api_client.rest_client.GET(
            url=self.solution_info.download.url, headers={self.api_key_header: self.api_key}, _preload_content=False)
        with open("case_file_solution.zip", "wb") as file:
               file.write(solution_response.data)
        zip = zipfile.ZipFile("case_file_solution.zip")
        print(f"Averaged solution ZIP file content: {zip.namelist()}")
    
    def get_simulation_report(self, part_id = "region1"):
        self.reports_api = sim_sdk.ReportsApi(self.api_client) 
        self.solution_info = [r for r in self.simulation_results._embedded if r.category == "SOLUTION"][0]

        home_dir = pathlib.Path.home()
        
        # Generating simulation run report
        camera_settings = sim_sdk.UserInputCameraSettings(
            projection_type= sim_sdk.ProjectionType.ORTHOGONAL,
            up= sim_sdk.Vector3D(0.5, 0.3, 0.2),
            eye= sim_sdk.Vector3D(0.0, 5.0, 10.0),
            center= sim_sdk.Vector3D(10.0, 12.0, 1.0),
            front_plane_frustum_height=0.5,
        )
        # "Temperature", component="X", data_type="CELL"
        model_settings = sim_sdk.ModelSettings(
            parts=[sim_sdk.Part(part_identifier= part_id, solid_color=sim_sdk.Color(0.8, 0.2, 0.4))],
            #scalar_field=sim_sdk.ScalarField(field_name= "Velocity", component="X", data_type="CELL"),
        )
        output_settings = sim_sdk.ScreenshotOutputSettings(name="Output 1", format="PNG", resolution=sim_sdk.ResolutionInfo(800, 800),
                                                   frame_index=0)
        report_properties = sim_sdk.ScreenshotReportProperties(
            model_settings=model_settings,
            filters=None,
            camera_settings=camera_settings,
            output_settings=output_settings,
        )
        report_request = sim_sdk.ReportRequest(name="Report 1", description="Simulation report", result_ids=[self.solution_info.result_id],
                                       report_properties=report_properties)
        
        create_report_response = self.reports_api.create_report(self.project_id, report_request)
        report_id = create_report_response.report_id
        
        # Start report job
        print(f"Starting report with ID {report_id}")
        report_job = self.reports_api.start_report_job(self.project_id, report_id)
        
        report = self.reports_api.get_report(self.project_id, report_id)
        
        while report.status not in ("FINISHED", "CANCELED", "FAILED"):
            time.sleep(30)
            report = self.reports_api.get_report(self.project_id, report_id)
        
        print(f"Report finished with status {report.status}")
        
        if report.status == "FINISHED":
            # Download the report
            print("Downloading report result")
            report_response = self.api_client.rest_client.GET(
                url=report.download.url,
                headers={self.api_key_header: self.api_key},
                _preload_content=False,
            )
        
            file_name = home_dir / f"report.{report.download.format}"
            with open(file_name, "wb") as file:
                file.write(report_response.data)
                print(f"Finished downloading report with name {file_name}")
        elif report.status == "FAILED":
            raise Exception("Report generation failed", report.failure_reason)

    # Function to read CSV data from a string and convert it into a list of dictionaries
    def read_csv_data(self, csv_string):
        data = StringIO(csv_string)
        reader = csv.DictReader(data)
        return [row for row in reader]

    # Function to calculate sum of all columns except the first one (time column) and add it as a new column
    def process_data(self, data):
        processed_data = []
        for row in data:
            row_data = list(row.values())
            time = row_data[0]
            values = list(map(float, row_data[1:]))
            sum_values = sum(values)
            processed_data.append(row_data + [sum_values])
        return processed_data

    # Function to write the processed data to a CSV file
    def write_to_csv(self, file_name, data, headers):
        # Path object for the directory
        home_dir = pathlib.Path.home()
        file_path = home_dir / file_name
        with open(file_path, mode='w', newline='') as file:
            writer = csv.writer(file)
            writer.writerow(headers)
            writer.writerows(data)

    def combine_data(self, internal_data, external_data):
        combined_data = []
        # Assuming both datasets are of the same length and ordered by time
        for internal_row, external_row in zip(internal_data, external_data):
            # Assuming the first element is the time which should be identical in both rows
            time = internal_row[0]
            internal_sum = internal_row[-1]  # The sum is the last element in the processed data
            external_sum = external_row[-1]
            combined_data.append([time, internal_sum, external_sum])
        return combined_data
    
    def get_simulation_run_spec(self):
        """
        Fetch the simulation run spec and return it as a dictionary.
        """
        try:
            # Fetch the simulation run spec
            run_spec = self.simulation_run_api.get_simulation_run_spec(self.project_id, self.simulation_id, self.run_id)
            
            # Convert the run spec to a dictionary
            run_spec_dict = run_spec.to_dict()
            
            return run_spec_dict  # Return the run spec as a dictionary
        
        except Exception as e:
            print(f"Error retrieving simulation run spec: {e}")
            return None