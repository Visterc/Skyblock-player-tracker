import requests
import json
import asyncio
import datetime
import discord
from discord import app_commands
from dotenv import load_dotenv
import os
load_dotenv()
token= os.getenv('token')
Hkey= os.getenv('Hkey')


intents = discord.Intents.default()# tells discord which permission your bot wants to receive
client = discord.Client(intents=intents,allowed_mentions=discord.AllowedMentions(everyone=True))# creates the actual bot and permissions
tree = app_commands.CommandTree(client)# container that holds all the slash commmands

numberC = 0
loop1 = False
tracker_task = None #stores the running task


@tree.command(name="track", description="Check if the player is online") #register it as a command the "name" is what the user types and "description" is what shows in the commands
@app_commands.describe(username="Player Ign") # adds a description to the username argument that discord shows

async def track(interaction: discord.Interaction, username: str): # runs this function when someone types /track "username: str" is the part that captures aka the ign
       global tracker_task
       
       #gets the username uuid
       minecraft_request = requests.get(f"https://api.mojang.com/users/profiles/minecraft/{username}")
       if minecraft_request.status_code != 200:
            await interaction.response.send_message("Couldnt find the minecraft username")
            loop1 = False
            return
       
       uuid = minecraft_request.json()['id']
       channel = interaction.channel

       if tracker_task and not tracker_task.done():
             tracker_task.cancel()
             await interaction.response.send_message(f"Stopped last tracker, now tracking **{username}**")
       else:
             await interaction.response.send_message(f"Started to track **{username}**")

       tracker_task = asyncio.create_task(tracker_loop(channel, username, uuid))


async def tracker_loop(channel, username, uuid):
      global numberC
      numberC = 0
      
      while True:
            numberC +=1

            try:
                 hypixel_request = requests.get(
                  f"https://api.hypixel.net/v2/status?key={Hkey}&uuid={uuid}",
                  timeout=10)
                 filter_data = hypixel_request.json()

                 #this had help with ai because i didnt know what the issue was and it was the 4th time seeing similar error, basically is also a error part but this time on hypixel side API
                 if not filter_data.get('session'):
                        error_cause = filter_data.get('cause', 'Unknown error')
                        print(f"Hypixel API error: {error_cause}")
                        await channel.send(f"Hypixel API error: '{error_cause}' , stopping the tracker")
                        break
                  
            
                 if 'session' not in filter_data:
                        await channel.send("Unexpected response, retrying next check in 5 minutes")
                        await asyncio.sleep(300)
                        continue

                 now = datetime.datetime.now()

                 #check if online or not 
                 if filter_data['session']['online'] == False:
                        data = {
                              "content" : f"player: {username} is offline",
                        }
                        
                 else:
                        data = {
                              "content" : f"player: {username} is online @everyone",
                        }

                 #sends the check message
                 embed = discord.Embed(
                        title=f"time of checks: {now.strftime('%H:%M:%S')}",
                        description=F"Checks: Checks: {numberC}\nonline: {filter_data['session']['online']}"
                  )
                 
                 await channel.send(content=data["content"], embed=embed) # no idea i think

            #errors part
            except requests.exceptions.RequestException as e:
                  print(f"Request error: {e}")
                  await channel.send(f"network error happend, retrying in 5 minutes..")
            
            except Exception as e:
                  print(f"Unexpected error: {e}")
                  await channel.send(f"unexpected error: {e}, retrying in 5 minutes ")

            await asyncio.sleep(300) # uses asyncio instead of time.sleep because time.sleep would only freeze the bot (ig?) 



@tree.command(name="stop", description="Stop the tracker loop") # stop command 
#interaction to stop commmand
async def stop(interaction: discord.Interaction):
      global tracker_task
      if not tracker_task or tracker_task.done():
            await interaction.response.send_message("The tracker is not running")
            return
      
      tracker_task.cancel()
      tracker_task = None
      await interaction.response.send_message("Tracker stopped")

#bot start stuff 
@client.event
async def on_ready():
       await tree.sync()
       print(f"logged in as {client.user} tracking command is ready")

client.run(token)