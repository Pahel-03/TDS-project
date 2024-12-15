# /// script
# requires-python = ">=3.11"
# dependencies = [
#   "httpx",
#   "pandas",
#   "matplotlib",
#   "tabulate",
#   "openai",
#   "requests",
#   "seaborn",
#   "scikit-learn",
#   "numpy"
# ]
# ///

import sys
import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import subprocess
import openai
import requests
import re
import seaborn as sns
import base64
import json
from sklearn.preprocessing import LabelEncoder
from sklearn.decomposition import PCA
from sklearn.cluster import KMeans

#Assign value to API_KEY
API_KEY=os.environ["AIPROXY_TOKEN"]
#Extract filename from stdin
filename=sys.argv[1]

# Load the CSV file
def load_data(name):
    ldata = pd.read_csv(name,encoding_errors="replace")
    return ldata

data=load_data(filename)

# Descriptive Statistics of the data
def make_decriptive_stats(data):
    summary=data.describe(include="all").to_markdown()
    return(summary)


# Drop rows with any null values
def drop_null_rows(data):
    df_dropped_rows = data.dropna()
    return df_dropped_rows

# Correlation map of numerical columns
def make_correl_map(data):
    categorical_columns_with_bool = data.select_dtypes(include=['object', 'category', 'bool']).columns
    num_data=data.drop(categorical_columns_with_bool,axis=1)
    correlation_matrix_data=num_data.corr()
    return correlation_matrix_data.to_json()

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

#correaltion Analysis using ai-using vision capabilities
def correl_analysis(correl_mat):
    response = requests.post(
            "http://aiproxy.sanand.workers.dev/openai/v1/chat/completions",
            headers={"Authorization": f"Bearer {API_KEY}"},
            json={
                "model": "gpt-4o-mini",
                "messages": [
                    {"role": "system", "content": '''Provide a correlation analysis based on the following correlation matrix and how it can be used for analysing data'''},
                    {"role": "user", "content": correl_mat}
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

#Generate Feature importance output
def give_feature_importances(data):
    categorical_columns = data.select_dtypes(include=['object']).columns
    for col in categorical_columns:
        le = LabelEncoder()
        data[col] = le.fit_transform(data[col])
    pca = PCA()
    pca.fit(data)
    loadings = pca.components_
    feature_importance = pd.Series(np.abs(loadings).sum(axis=0), index=data.columns)
    ranked_features = feature_importance.sort_values(ascending=False)
    response = requests.post(
            "http://aiproxy.sanand.workers.dev/openai/v1/chat/completions",
            headers={"Authorization": f"Bearer {API_KEY}"},
            json={
                "model": "gpt-4o-mini",
                "messages": [
                    {"role": "system", "content": f'''U have been provided with feature ranking for a dataset analyse it 
                     and its probable implcations in analysing that data.'''},
                    {"role": "user", "content": ranked_features.to_json()}
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
                    Descibe what each column represents without any mention of the values given.'''},
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

# redudant features / elimination - openai function calling
def is_it_redundant(first_row):
    response = requests.post(
            "http://aiproxy.sanand.workers.dev/openai/v1/chat/completions",
            headers={"Authorization": f"Bearer {API_KEY}"},
            json={
                "model": "gpt-4o-mini",
                "messages": [
                    {"role": "system", "content": '''Identify any redundant columns in the provided first row of the dataset.
                     Respond with a Yes followed by column names to be dropped in a python list else repond with a No followed by an empty list'''},
                    {"role": "user", "content": first_row}
                ],
                # "functions":function_descriptions # specify the function call
            }
        )
    datar=response.json()
    choices_content = [choice['message']['content'] for choice in datar.get('choices', [])]
    sresp=""
    # Print the extracted content
    for index, content in enumerate(choices_content):
        sresp+=(f"\n{content}\n")
    return sresp,datar

def drop_red_cols(resp,drop_it):
# Split the matched strings by comma to get column names
    column_names = []
    if resp=='Yes':
        matches = re.findall(r"'(.*?)'", drop_it)
# Split the matched strings by comma to get column names
        column_names = [name.strip() for name in matches]
        redun_resp=f'There are some redundant columns in our dataset which we eliminate more specifically : {drop_it}'
    else:
        redun_resp="The dataset is a well defined one with no redundant columns."
    return redun_resp,column_names

def create_red_explain(statement):    
    function_descriptions = [
    {
        "name": "drop_red_cols",
        "description": "Drop Redundant columns",
        "parameters": {
            "type": "object",
            "properties": {
                "resp": {
                    "type": "string",
                    "description": "if data has redundant columns or not eg: Yes or No",
                },
                "drop_it": {
                    "type": "string",
                    "description": "The columns to be dropped eg:['date','id','time_id'] or []",
                },
            },
            "required": ["resp", "drop_it"],
        },
    }
]

    response = requests.post(
            "http://aiproxy.sanand.workers.dev/openai/v1/chat/completions",
            headers={"Authorization": f"Bearer {API_KEY}"},
            json={
                "model": "gpt-4o-mini",
                "messages": [
                    {"role": "system", "content": '''Identify the yes or no response and python list'''},
                    {"role": "user", "content": statement}
                ],
                "functions":function_descriptions ,
                "function_call":"auto"# specify the function call
            }
        )
    datar=response.json()
    message = datar['choices'][0]['message']
    if 'function_call' in message:
        function_call=message['function_call']
        arguments = json.loads(function_call['arguments'])  # Parse the arguments as JSON
        resp_redun,drop_l=drop_red_cols(arguments['resp'],arguments['drop_it'])
    # print(arguments)
    else:
        datar=None
        resp_redun,drop_l=drop_red_cols("No",[])
    return resp_redun,datar,drop_l

#drop redundant columns
def drop_cols(datan,drop):
    if drop==[]:
        return datan
    else:
        datan=datan.drop(drop,axis=1)
        return datan

#AI call for basic summary based on decsriptive statistics
def basic_desc(statistics):
    response = requests.post(
            "http://aiproxy.sanand.workers.dev/openai/v1/chat/completions",
            headers={"Authorization": f"Bearer {API_KEY}"},
            json={
                "model": "gpt-4o-mini",
                "messages": [
                    {"role": "system", "content": "Give me a summary of my data based on the provided descriptive statistics."},
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
                     Only plot 5 most important charts.
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
    try:
        exec(code)
    except Exception as e:
        print(f"Error during code execution: {e}")

def image_process(image_url):
    # Function to encode the image
    def encode_image(image_path):
        with open(image_path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode('utf-8')

    # Getting the base64 string
    base64_image = encode_image(image_url)
    response = requests.post(
            "http://aiproxy.sanand.workers.dev/openai/v1/chat/completions",
            headers={"Authorization": f"Bearer {API_KEY}"},
            json={
                "model": "gpt-4o-mini",
                "messages": [
                    {"role": "system", "content": '''Analyse the image provided for data insights and talk about real life implications from our analysis.'''},
                    { "role":"user","content": [{"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base64_image}","detail": "low"}}]}
                    ]
                    }
                    )
    datar=response.json()
    choices_content = [choice['message']['content'] for choice in datar.get('choices', [])]
    sresp=""
    # Print the extracted content
    for index, content in enumerate(choices_content):
        sresp+=(f"\n{content}\n")
    return sresp,datar,image_url

#Run analysis functions on dataset

first_row_response,token_4=describe_data(first_row_of_data)
redundant_response,token_5=is_it_redundant(first_row_of_data)   
# print(redundant_response)
is_it,lists,drop_list=create_red_explain(redundant_response)
data=drop_cols(data,drop_list)
data=data.dropna()
correl_response,token_8=correl_analysis(make_correl_map(data))
feature_imp,token_9=give_feature_importances(data)
summary_response,token_1=basic_desc(make_decriptive_stats(data))
analyse_response,token_2=further_analysis(make_decriptive_stats(data))
code_1=extract_python_code(token_2)
execute_extracted_code(code_1)
heatmap_mat_code,token_3=heatmap_code(make_correl_map(data))
code_2=extract_python_code(token_3)
execute_extracted_code(code_2)

# GET IMAGE PATH 
current_directory = "./" 

# List to store URLs of PNG files
png_urls = []

# Loop through all files in the current directory
for filename in os.listdir(current_directory):
    if filename.endswith(".png"):
        file_path = os.path.join(current_directory, filename)
        # Construct the URL for each PNG file
        url = os.path.relpath(file_path, "./").replace("\\", "/")
        png_urls.append(url)

image_text,image_tokens,order_titles=[],[],[]
for url in png_urls:
    image_resp,img_token,title=image_process(url)
    image_text.append(image_resp)
    image_tokens.append(img_token)
    order_titles.append(title)


with open("README.md", "w") as f:
    f.write("## An introduction to the data ##\n\n")
    f.write(str(first_row_response))
    f.write("\n\n## Asking ai to indentify redundant columns in our dataset ##\n\n")
    f.write(str(is_it))
    f.write("\n\n##  Descriptive Statistics of the dataset ##\n")
    f.write(str(make_decriptive_stats(data)))
    f.write("\n\n## Understanding Descriptive Statistics ##\n")
    f.write(str(summary_response))
    f.write("\n\n## How important are our columns - Feature importance Analysis based on PCA ##\n\n")
    f.write(str(feature_imp))
    f.write("\n## How are our columns related to each other? - Correlation Analysis ##\n")
    f.write(str(correl_response))
    f.write("\n\n## What do the charts entail about our columns? - Using vision capabilities to analyse them ##\n\n")
    for i in range(len(image_text)):
        f.write(f'## {order_titles[i]} ##\n')
        f.write(str(image_text[i])+'\n\n')

print("Analysis complete. See README.md for details.")

