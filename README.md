# Simscale-BCA Setup Guide

This guide will walk you through the steps to get the project set up on your machine.

## Prerequisites
Before you begin, ensure you have the following installed on your system:

#### Rhino >= 8

#### Python >=3.6: 

#### Git: 
Required to clone the repository. Ensure Git is installed and accessible from your command line.

## Installation Instructions
Follow these steps to install the Simscale-BCA project:

### Step 1: Clone the Repository
Open command prompt and run the following command (making sure to replace USERNAME with your actual Username):

cd C:\Users\USERNAME\\.rhinocode\py39-rh8\lib\site-packages

Then run

git clone https://github.com/cswinburn/Simscale-BCA.git simscale_BCA


## Step 2: Install Dependencies

##### From the same command line window run the following command: 
cd simscale_BCA

##### Followed by:
python install_deps.py

This will install the dependencies to the correct location so python3 inside Rhino8 grasshopper has access to these modules.

## Step 3: Set API key locally on your PC
Type 'Edit system environment variables in windows search' open this then navigate to  Environment Variables > System variables > New 
and add the following two system variables: 
1) Variable: SIMSCALE_API_KEY, Key: XXX (replace with your actual API key provided by Simscale)
   
2) Variable: SIMSCALE_API_URL, Key: https://api.simscale.com

Click Save and close window.

## Usage
After installing the Simscale-BCA project and its dependencies, you can now open Rhino8 and use it as intended for your specific purposes. 
## Troubleshooting
Python or Git Not Found: If the command prompt returns errors indicating that Python or Git is not recognized, ensure both are correctly installed and their executable paths are added to your system's environment variables.
