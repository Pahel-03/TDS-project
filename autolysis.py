# /// script
# requires-python = ">=3.11"
# dependencies = [
#   "httpx",
#   "pandas",
#   "matplotlib",
#   "tabulate",
#   "openai",
#   "requests",
#   "seaborn"
# ]
# ///

import sys
import os
import pandas as pd
import matplotlib.pyplot as plt
import subprocess
import openai
import requests
import re
import seaborn as sns
import base64
import json

#Assign value to API_KEY
API_KEY="eyJhbGciOiJIUzI1NiJ9.eyJlbWFpbCI6IjIyZjMwMDA4NTNAZHMuc3R1ZHkuaWl0bS5hYy5pbiJ9.dfSdl8fjbiEzHKYuy7Ut9jbUYqpJjDY5zRfyFJzAHeQ"

#Extract filename from stdin
filename=sys.argv[1]

# Load the CSV file
def load_data(name):
    ldata = pd.read_csv(name,encoding_errors="replace")
    return ldata

data=load_data(filename)

# Descriptive Statistics of the data
analysis_results = []
charts = []
summary = data.describe(include="all").to_markdown()
analysis_results.append("### Dataset Summary")
analysis_results.append(summary)
cols=data.columns
categorical_columns_with_bool = data.select_dtypes(include=['object', 'category', 'bool']).columns
numerical_columns = data.select_dtypes(include=['number']).columns

# Drop rows with any null values
df_dropped_rows = data.dropna()
null_rows=len(df_dropped_rows)

#data with only numerical columns
num_data=data.drop(categorical_columns_with_bool,axis=1)

# Correlation map of numerical columns
correlation_matrix_data=num_data.corr()

#Call AI to generate a correlation heatmap
def heatmap_code(statistics):
    response = requests.post(
            "http://aiproxy.sanand.workers.dev/openai/v1/chat/completions",
            headers={"Authorization": f"Bearer {API_KEY}"},
            json={
                "model": "gpt-4o-mini",
                "messages": [
                    {"role": "system", "content": '''Write python code to generate a correlation heatmap with appropriate colouring and labels with
                     correlation matrix named 'correlation_data matrix.
                     I also need you to save the plotted figure locally in current directory.
                     Do not use plt.show'''},
                    {"role": "user", "content": statistics}
                ]
            }
        )
    datar=response.json()
    choices_content = [choice['message']['content'] for choice in datar.get('choices', [])]
    sresp=""
    # Print the extracted content
    for index, content in enumerate(choices_content):
        sresp+=(f"\n{content}\n")
    return sresp,datar

# feature importance analysis-do pca

#cluster analysis-- Make a function

#AI call for Data description
first_row_of_data=data.iloc[0].to_json()
def describe_data(first_row):
    response = requests.post(
            "http://aiproxy.sanand.workers.dev/openai/v1/chat/completions",
            headers={"Authorization": f"Bearer {API_KEY}"},
            json={
                "model": "gpt-4o-mini",
                "messages": [
                    {"role": "system", "content": '''There is first row of a dataset given.
                        try describing what each clumn entails in an engaging way without talking much about the values of the first row.'''},
                    {"role": "user", "content": first_row}
                ]
            }
        )
    datar=response.json()
    choices_content = [choice['message']['content'] for choice in datar.get('choices', [])]
    sresp=""
    # Print the extracted content
    for index, content in enumerate(choices_content):
        sresp+=(f"\n{content}\n")
    return sresp,datar

#AI call for basic summary based on decsriptive statistics
def basic_desc(statistics):
    response = requests.post(
            "http://aiproxy.sanand.workers.dev/openai/v1/chat/completions",
            headers={"Authorization": f"Bearer {API_KEY}"},
            json={
                "model": "gpt-4o-mini",
                "messages": [
                    {"role": "system", "content": "Give me a summary of my data based on the provided statistics. Make your responses sound engaging."},
                    {"role": "user", "content": statistics}
                ]
            }
        )
    datar=response.json()
    choices_content = [choice['message']['content'] for choice in datar.get('choices', [])]
    sresp=""
    # Print the extracted content
    for index, content in enumerate(choices_content):
        sresp+=(f"\n{content}\n")
    return sresp,datar

#AI call for visualising analysis done
def further_analysis(statistics):
    response = requests.post(
            "http://aiproxy.sanand.workers.dev/openai/v1/chat/completions",
            headers={"Authorization": f"Bearer {API_KEY}"},
            json={
                "model": "gpt-4o-mini",
                "messages": [
                    {"role": "system", "content": '''Visualise given decsriptive statistics using python approriately identifying numerical and categorical varianbles.
                     I have all the required libraries installed with matplotlib.pyplot as plt and seaborn as sns.
                     I also need you to save the plotted figures locally in current directory .Avoid making boxplots and heatmaps.
                     Do not plot the figures that will be difficult to interpret.
                     Properly label and colourize all plots.Do not use plt.show.
                     My python dataframe is called 'data' so cater the code for it.'''},
                    {"role": "user", "content": statistics}
                ]
            }
        )
    datar=response.json()
    choices_content = [choice['message']['content'] for choice in datar.get('choices', [])]

    sresp=""
    # Print the extracted content
    for index, content in enumerate(choices_content):
        sresp+=(f"\n{content}\n")
    return sresp,datar

#Extract python code from gpt reponse
def extract_python_code(json_data):
    # Traverse the JSON to find the 'content' key
    content = json_data.get("choices", [{}])[0].get("message", {}).get("content", "")
    
    # Use regex to extract Python code blocks from the content
    code_blocks = re.findall(r"```python(.*?)```", content, re.DOTALL)
    
    # Combine all code blocks if multiple exist
    extracted_code = "\n\n".join(code_blocks).strip()
    
    return extracted_code

#Execute extracted code from gpt response
def execute_extracted_code(code):
    """
    Execute Python code provided as a string.
    
    Args:
        code (str): Python code to execute.
    """
    try:
        exec(code)
    except Exception as e:
        print(f"Error during code execution: {e}")

def image_process(base64_imgs):
    response = requests.post(
            "http://aiproxy.sanand.workers.dev/openai/v1/chat/completions",
            headers={"Authorization": f"Bearer {API_KEY}"},
            json={
                "model": "gpt-4o-mini",
                "messages": [
                    {"role": "system", "content": "Given are Base64 encoded graphs based on some data in json form analyse them in an engaging way"},
                    {"role": "user", "content": base64_imgs}
                ]
            }
        )
    datar=response.json()
    choices_content = [choice['message']['content'] for choice in datar.get('choices', [])]
    sresp=""
    # Print the extracted content
    for index, content in enumerate(choices_content):
        sresp+=(f"\n{content}\n")
    return sresp,datar

#Run analysis functions on dataset
summary_response,token_1=basic_desc(summary)
analyse_response,token_2=further_analysis(summary)
code_1=extract_python_code(token_2)
execute_extracted_code(code_1)
heatmap_mat_code,token_3=heatmap_code(correlation_matrix_data.to_json())
code_2=extract_python_code(token_3)
execute_extracted_code(code_2)
first_row_response,token_4=describe_data(first_row_of_data)

# GET IMAGE PATH AND CONVERSION FOR VISION ANLYSIS
current_directory = os.getcwd()
files_in_directory = os.listdir(current_directory)
png_files = [file for file in files_in_directory if file.endswith('.png')]
def encode_image_to_base64(image_path):
    with open(image_path, "rb") as image_file:
        # Read the image file and encode it to base64
        encoded_string = base64.b64encode(image_file.read()).decode('utf-8')
    return encoded_string
images_base64 = {os.path.basename(file): encode_image_to_base64(os.path.join(current_directory, file)) for file in png_files}

image_response,token_5=image_process(images_base64)
image_json_object = json.dumps(images_base64, indent = 4)
# Generate README.md

with open("README.md", "w") as f:
    f.write("\n\n## Basic description of data ##\n\n")
    f.write(str(first_row_response))
    # f.write("\n\n#Tokens used are given below\n")
    # f.write(str(token_4['usage']))
    f.write("\n\n## Basic analysis of data ##\n\n")
    f.write(str(summary_response))
    # f.write("\n\n#Tokens used are given below\n")
    # f.write(str(token_1['usage']))
    # f.write("\n\n#What analysis can be conducted[REMOVE]")
    # f.write(str(analyse_response))
    # f.write("\n\n#Tokens used are given below\n")
    # f.write(str(token_2['usage']))
    f.write("\n\n## Basic analysis of images ##\n\n")
    f.write(str(image_response))
    f.write("\n\n#Tokens used are given below\n")
    f.write(str(token_5))
    # f.write("\n\n## Visualizations\n")
    # f.write(str(heatmap_mat_code))

# print(image_json_object)
print("Analysis complete. See README.md for details.")


