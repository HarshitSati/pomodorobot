from platform import platform
import discord
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from pytz import utc
from datetime import datetime, timedelta

from discord.ext import commands
bot = commands.Bot(intents=discord.Intents.all(), command_prefix='ps!')

USER_LIST={}
VC_LIST= set() #if a person leaves or joins the VC during or at start of pomo

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user} (ID: {bot.user.id})")
    print("------")
    global VC_LIST
    
    workspace = 1022156035823251541  #tortoise workspace  VC ID
    workspace_channel = bot.get_channel(1022156035823251541)
    VC_LIST.update(set([x.id for x in workspace_channel.members]))

@bot.slash_command()
async def hello(interaction: discord.Interaction):
    """Says hello!"""
    await interaction.response.send_message(f'Hi, {interaction.user.mention}')


@bot.slash_command(guild_ids=[1022156035823251536])
async def hello_num(interaction: discord.Interaction, num: int):
    """Says hello!"""
    await interaction.response.send_message(f'Hi, {interaction.user.mention}. Your number is {num}.')

pomo_data={}
complete_pomo={}
notif_channel = bot.get_channel(1041715750047596574) #unified channel to send notifs


scheduler = AsyncIOScheduler(timezone=utc)
scheduler.start()

@bot.slash_command(guild_ids=[1022156035823251536])
@discord.option("pomo_time", description="Time of each pomodoro (in mins); default is 25mins")
@discord.option("number_of_pomos", description="Number of pomos, default is 2")
@discord.option("break_time", description="Time for each break, default is 5mins")
async def pomo(interaction: discord.Interaction, pomo_time:int=25, number_of_pomos:int=2, break_time:int=5):
    """main pomodoro setup"""
    #has user joined VC?
    #Task running once a minute
    #List of users in VC
    #USER_LIST

    member = interaction.user 

    r_pomo_time=0 #recorded pomo time
    r_number_of_pomos=0 #recorded number of pomos

    complete_pomo[member.id]={"R_pomo_time": r_pomo_time, "R_number_of_pomos": r_number_of_pomos} #to store local member pomo info

    elapsed_time=0
    number_of_breaks= number_of_pomos-1
    total_time= pomo_time*number_of_pomos+break_time*number_of_breaks
    total_pomo_time= number_of_pomos*pomo_time

    pomo_data[member.id] = {"pomo_time": pomo_time, "number_of_pomos":number_of_pomos, "number_of_breaks": number_of_breaks,
                          "break_time":break_time, "total_pomo_time": total_pomo_time, "total_time":total_time,
                          'elapsed_time': elapsed_time, 'pomo_active': False, 'job': None, 'run_time': None, 'breaks_left': number_of_breaks, "break_status": False}
    

    await interaction.response.send_message("Join the VC to start the pomo!!")
    await pomo_logic(member, pomo_data[member.id])


def finish_pomo(member, pomo_data):
    print(f"Finished pomo for member {member}")
    print(f"Your total pomo time is {pomo_data['total_pomo_time']}")

# If user in VC, reschedules and starts job immediately
# else, sets variable in pomo_data to True, which is checked in pomo_logic next time user joins VC
# which then calls reschedule_job again
def reschedule_job(pomo_data,time_paused):
    print("Job rescheduled")
    current_time = datetime.utcnow()
    break_time = current_time - time_paused
    previous_run_time = pomo_data['run_time']
    new_run_time = previous_run_time+break_time
    pomo_data['run_time'] = new_run_time
    pomo_data['job'].reschedule("date", run_date = pomo_data['run_time'])
    pomo_data['breaks_left'] -= 1 
    print(f"main job: {pomo_data['job']}")
    create_secondary_task(pomo_data)

    
def create_break_job(pomo_data):
    print("Break job created")
    pomo_data['job'].pause()
    time_paused = datetime.utcnow()
    break_job = scheduler.add_job(reschedule_job, "date", 
                run_date = datetime.utcnow()+timedelta(seconds=pomo_data['break_time']), args=[pomo_data, time_paused])
    
    print(f"break job {break_job}")


@bot.slash_command(guild_ids=[1022156035823251536])
@discord.option("status", description="Shows the status of all current jobs")
async def task_status(interaction: discord.Interaction):
    """Checks status of all jobs!"""
    for job in scheduler.get_jobs():
        print(job)



# Creates secondary task that runs for the time of one pomo, when complete, calls a function that pauses the task
# and creates a new task that lasts for the time period of one break_time, as long as there is more than one break left.
def create_secondary_task(pomo_data):
    if pomo_data['breaks_left'] > 0:
        print("Secondary task created")
        secondary_task = scheduler.add_job(create_break_job, "date", run_date= datetime.utcnow()+
                          timedelta(seconds=pomo_data['pomo_time']), args=[pomo_data])

        print(f"secondary task: {secondary_task}")
        # create task

async def pomo_logic(member, pomo_data):
    """mail logic for the bot wohhoo"""
    if pomo_check(member.id):
        print(pomo_data)
        if not pomo_data['pomo_active']:
            pomo_data['pomo_active'] = True
            await notif_channel.send("Pomodoro started! :)")
            pomo_data['run_time'] = datetime.utcnow() + timedelta(seconds=pomo_data["total_pomo_time"])
            pomo_data['job'] = scheduler.add_job(
                finish_pomo, "date",
                run_date=pomo_data['run_time'],
                args=[member, pomo_data]
            )
            create_secondary_task(pomo_data)

            
        
        

def pomo_check(member_id):
    """Flag to check if the person is still in VC
       returns: Boolean
    """
    if member_id in pomo_data and member_id in VC_LIST: # Check if user currently in VC
        return True
    return False


@bot.event #VC events #leaving or joining a VC alert
async def on_voice_state_update(member, before, after):
    """Logic for if the person has left or joined the VC
        Supports:  pomo_check
        Updates: VC_LIST to have the IDs of the people in the workspace VC """

    joined_voice_channel = None
    if before.channel is None and after.channel is not None:
        joined_voice_channel = True
    else:
        joined_voice_channel = False

    workspace_channel = bot.get_channel(1022156035823251541)#tortoise workspace  VC ID

    if joined_voice_channel and after.channel == workspace_channel:  #joining new vc
        VC_LIST.add(member.id)
    elif before.channel is workspace_channel and after.channel is None: # leaving vc
        VC_LIST.remove(member.id)
    elif before.channel is not None and after.channel ==workspace_channel: # hopping to workspacce from a VC
        VC_LIST.add(member.id)
    elif before.channel is workspace_channel and after.channel !=workspace_channel: # hopping from workspace to a VC
        VC_LIST.remove(member.id)

    if member.id in pomo_data:
        await pomo_logic(member, pomo_data[member.id])
    


with open("token", "r", encoding="utf-8") as tf:
    TOKEN = tf.read()

bot.run(TOKEN)

