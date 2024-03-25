import requests
import os
import time
import json
import openai
from flask import Flask, jsonify, request
from dotenv import load_dotenv
from os import getenv
import google.generativeai as genai
import shutil
import time

app = Flask(__name__)
app.logger.debug('Connection initialized')
load_dotenv()
openai.api_key = getenv("GPT_API_KEY")
genai.configure(api_key=getenv("GEMINI_API_KEY"))
meshApi = "msy_vagZukwm0TmAMBOk9I5gip0C4jNeJlOf7btz"
taskIds = []

envs = ['road', 'rocky_terrain','grass','snow','lava']
statObs = ['log','cactus','stone','dumbbell','traffic_cone','barrier','oak_tree','palm_tree',]
dynaObs = ['bear','car','jeep','zombie','train','tiger','chicken','deer','horse','penguin','space_ship','dog','tank','fairy','dinosarus','robot','train']
sky = ['starry_night_sky','snow_sky',"evening_sky","morning_sky","lava_sky","dark_storm_sky","underwater_supernova_sky","desert_sky","clear_sky","earth_orbit_sky"]

def understanding_concept(concept_info):
  prompt = [f"""
    Please analyze the provided scenario and classify it into four key aspects based on the descriptions given. Use the following categories for your classification: environment or scene type, static obstacle type, dynamic obstacle type, and the most suitable sky (or scenery). 

- For the environment, choose from these options: {envs}. 
- For the static obstacle, select from: {statObs}. 
- For the dynamic obstacle, pick from: {dynaObs}. 
- For the sky or scenery, decide on the best fit from: {sky}. 

Your classification should reflect the scenario’s setting accurately, the main obstacles present, and the sky that best matches the overall ambiance of the scene. 

Provided information:
"{concept_info}"

Format your response as follows: "environment, staticObstacle, DynamicObstacle, sky". If a direct match is not found in the descriptions, select the most fitting option from the provided lists. Avoid responses like null, 'doesn't match', none, or similar. Ensure your answer adheres strictly to the requested format.

    """]
  safety_settings = [
      {
      "category": "HARM_CATEGORY_HARASSMENT",
      "threshold": "BLOCK_MEDIUM_AND_ABOVE"
      },
      {
      "category": "HARM_CATEGORY_HATE_SPEECH",
      "threshold": "BLOCK_MEDIUM_AND_ABOVE"
      },
      {
      "category": "HARM_CATEGORY_SEXUALLY_EXPLICIT",
      "threshold": "BLOCK_MEDIUM_AND_ABOVE"
      },
      {
      "category": "HARM_CATEGORY_DANGEROUS_CONTENT",
      "threshold": "BLOCK_MEDIUM_AND_ABOVE"
      },

  ]
  model = genai.GenerativeModel(model_name="gemini-1.0-pro",
  safety_settings=safety_settings
  )
  response = model.generate_content(prompt)
  generated_text = response.text if response.text else "No content generated."
  print(response.text)
  return generated_text.strip()

def understanding_concept_gpt(concept_info):
  prompt = f"""
    Please analyze the provided scenario and classify it into four key aspects based on the descriptions given. Use the following categories for your classification: environment or scene type, static obstacle type, dynamic obstacle type, and the most suitable sky (or scenery). 

- For the environment, choose from these options: {envs}. 
- For the static obstacle, select from: {statObs}. 
- For the dynamic obstacle, pick from: {dynaObs}. 
- For the sky or scenery, decide on the best fit from: {sky}. 

Your classification should reflect the scenario’s setting accurately, the main obstacles present, and the sky that best matches the overall ambiance of the scene. 

Provided information:
"{concept_info}"

Format your response as follows: "environment, staticObstacle, DynamicObstacle, sky". If a direct match is not found in the descriptions, select the most fitting option from the provided lists. Avoid responses like null, 'doesn't match', none, or similar. Ensure your answer adheres strictly to the requested format.

    """

  response = openai.ChatCompletion.create(
      model="gpt-4",
      messages=[{
          "role":
          "system",
          "content":
          "You are an AI assistant capable of understanding the concept, context, and style for advertisement campaigns. Extract relevant information from the provided input."
      }, {
          "role": "user",
          "content": prompt
      }],
       max_tokens=50
      )
  return response.choices[0].message.content.strip()

def generate3D(prompts):

  headers = {"Authorization": f"Bearer {meshApi}"}
  for prompt in prompts:
    payload = {
        "object_prompt": f"{prompt}",
        "style_prompt":
        "High Quality cartoon model with no damage and should look new",
        "enable_pbr": True,
        "art_style": "realistic",
        "negative_prompt": "low quality, low resolution, low poly, ugly"
    }

    response = requests.post(
        "https://api.meshy.ai/v1/text-to-3d",
        headers=headers,
        json=payload,
    )
    taskIds.append(response.json())
  return taskIds


def extract3DModels(taskIds):
  headers = {"Authorization": f"Bearer {meshApi}"}
  models = []

  # while(1):
  #   for taskId in taskIds:
  #     response = requests.get(f"https://api.meshy.ai/v1/text-to-3d/{taskId['result']}",
  #                             headers=headers)
  #     print(response.json())
  #     time.sleep(10)
  #     imodel_url!
  while True:
    resp_flag = []
    for taskId in taskIds:
      response = requests.get(f"https://api.meshy.ai/v1/text-to-3d/{taskId['result']}",
                              headers=headers)
      if response.json()['status'].upper() == 'SUCCEEDED':
        resp_flag.append(True)
      else:
        resp_flag.append(False)
    time.sleep(10)
    if all(resp_flag):
      break
  for taskId in taskIds:
    response = requests.get(f"https://api.meshy.ai/v1/text-to-3d/{taskId['result']}",
                            headers=headers)
    models.append(response.json())
  return models


def getRequestStatus(models):
  for i in models:
    print(i['status'] , " ", i['model_url'])



def move_file(source_path, destination_path):

    try:

        shutil.copy(source_path, destination_path)
        print(f"File copy pasted successfully from {source_path} to {destination_path}")
    except FileNotFoundError:
        print(f"The file at {source_path} was not found.")
    except PermissionError:
        print(f"Permission denied: unable to move the file at {source_path}")
    except Exception as e:
        print(f"An error occurred while moving the file: {e}")

@app.route('/')
def server_status():
    return 'Server is up and running✨'

@app.route('/generate/<concept>', methods=['GET'])
def get3DModels(concept):
  concept_info = "A game level where players navigate a post-apocalyptic city with ruined buildings and avoid zombie hordes."
  counter  = 0
  while True:

    # prompts = understanding_concept(concept)
    prompts = understanding_concept_gpt(concept)
    print("Prompt",prompts)

    try:
        environment, staticObstacle, DynamicObstacle,skyScene = prompts.split(',')
        environment = environment.lstrip('"[').rstrip('"')
        staticObstacle = staticObstacle.lstrip(' "').rstrip('"')
        DynamicObstacle = DynamicObstacle.lstrip(' "').rstrip('"]')
        skyScene = skyScene.lstrip(' "').rstrip('"]')
      
        if(environment in envs and staticObstacle in statObs and DynamicObstacle in dynaObs and skyScene in sky ):
           
          print(environment)
          print(staticObstacle)
          print(DynamicObstacle)
          print(skyScene)
          return f"""{environment},{staticObstacle},{DynamicObstacle},{skyScene}"""
        elif counter == 2:
           time.sleep(20)
           counter = 0
        else:
           counter += 1 
           continue
    except Exception as e:
        print(e)
        environment, staticObstacle, DynamicObstacle,skyScene = "road", "barricade", "car",'clear_sky'
        return ''

if __name__ == '__main__':
   app.debug = True
   app.run(port=5000)