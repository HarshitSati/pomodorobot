from platform import platform
import discord
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from pytz import utc
from datetime import datetime, timedelta
#import pandas as pd
from discord.ext import commands
bot = commands.Bot(intents=discord.Intents.all(), command_prefix='ps!')

USER_LIST={}
VC_LIST= set() #if a person leaves or joins the VC during or at start of pomo

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user} (ID: {bot.user.id})")
    print("------")
    global VC_LIST
    global notif_channel
    
    workspace = 813199122999803924  #tortoise workspace  VC ID
    spam = 813196358067945483
    notif_channel = bot.get_channel(spam) #unified channel to send notifs
    workspace_channel = bot.get_channel(workspace)
    VC_LIST.update(set([x.id for x in workspace_channel.members]))

@bot.slash_command()
async def hello(interaction: discord.Interaction):
    """Says hello!"""
    await interaction.response.send_message(f'Hi, {interaction.user.mention}')


@bot.slash_command(guild_ids=[810282906215383090])
async def hello_num(interaction: discord.Interaction, num: int):
    """Says hello!"""
    await interaction.response.send_message(f'Hi, {interaction.user.mention}. Your number is {num}.')

pomo_data={}
complete_pomo={}
notif_channel = None


scheduler = AsyncIOScheduler(timezone=utc)
scheduler.start()

@bot.slash_command(guild_ids=[810282906215383090])
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

    number_of_breaks= number_of_pomos-1
    total_time= pomo_time*number_of_pomos+break_time*number_of_breaks
    total_pomo_time= number_of_pomos*pomo_time

    pomo_data[member.id] = {
        'member_id': member.id, # Member_ID of user who started pomo
        'pomo_time': pomo_time, # Time per pomo
        'number_of_pomos':number_of_pomos, # Number of pomos
        'number_of_breaks': number_of_breaks, # Number of breaks
        'breaks_left': number_of_breaks, # Breaks left (decremented after each break)
        'break_time':break_time,  # Time for each break
        'total_pomo_time': total_pomo_time, # Total pomo time (number of pomos * pomo time)
        'total_time':total_time, # Total time (total pomo time + total break time)
        'job': None, # Main job (Finishes pomo when complete)
        'secondary_job': None, # Secondary job (Breaks)
        'pomo_active': False, # Whether the pomo has been started yet, when True user has started the pomo.
        'run_time': None, # Current time when the main job should run, changes with breaks
        'secondary_run_time': None, # Current time when the secondary job should run, changes with breaks
        'break_status': False, # Whether the use is currently on break
        'pause_time': None, # Time when the pomo was last paused, used to reschedule the main job.
        'paused': False # Whether the pomo is currently paused.
        }
    
    if not vc_check(member.id):
        await interaction.response.send_message("Join the VC to start the pomo!!")
        return

    await pomo_logic(member, pomo_data[member.id])


async def finish_pomo(member, pomo_data):
    print(f"Finished pomo for member {member}")
    print(f"Your total pomo time is {pomo_data['total_pomo_time']}")
    await notif_channel.send(f"<@{member.id}> Pomo finished!!")

# If user in VC, reschedules and starts job immediately
# else, sets variable in pomo_data to True, which is checked in pomo_logic next time user joins VC
# which then calls reschedule_job again
async def reschedule_job(pomo_data):
    if vc_check(pomo_data['member_id']):
        print("Job rescheduled")
        await notif_channel.send(f"<@{pomo_data['member_id']}> Pomo resumed!!")
        current_time = datetime.utcnow()
        break_time = current_time - pomo_data['pause_time']
        previous_run_time = pomo_data['run_time']
        new_run_time = previous_run_time+break_time
        pomo_data['run_time'] = new_run_time

        pomo_data['paused'] = False

        pomo_data['job'].reschedule("date", run_date = pomo_data['run_time'])
        if pomo_data['break_status']:
            pomo_data['break_status'] = False
            pomo_data['breaks_left'] -= 1 
            create_secondary_task(pomo_data)
        elif pomo_data['secondary_job'] is not None:
            previous_run_time = pomo_data['secondary_run_time']
            new_run_time = previous_run_time+break_time
            pomo_data['secondary_run_time'] = new_run_time

            pomo_data['secondary_job'].reschedule("date", run_date = pomo_data['secondary_run_time'])


        print(f"main job: {pomo_data['job']}")
    else:
        await notif_channel.send(f"<@{pomo_data['member_id']}> Your break is over, but you are not in the VC. Please join the VC to continue the pomo.")
        pomo_data['paused'] = True

    
async def create_break_job(pomo_data):
    print("Break job created")
    await notif_channel.send(f"<@{pomo_data['member_id']}> Your break has started. You are now free to leave the VC.")
    pomo_data['job'].pause()
    time_paused = datetime.utcnow()
    pomo_data['pause_time'] = time_paused
    break_job = scheduler.add_job(reschedule_job, "date", 
                run_date = datetime.utcnow()+timedelta(minutes=pomo_data['break_time']), args=[pomo_data])
    pomo_data['break_status'] = True
    print(f"break job {break_job}")


@bot.slash_command(guild_ids=[810282906215383090])
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
        secondary_run_time = datetime.utcnow() + timedelta(minutes=pomo_data['pomo_time'])
        pomo_data['secondary_run_time'] = secondary_run_time
        secondary_task = scheduler.add_job(create_break_job, "date", run_date=secondary_run_time, args=[pomo_data])

        pomo_data['secondary_job'] = secondary_task

        print(f"secondary task: {secondary_task}")
        # create task

async def pomo_logic(member, pomo_data):
    """mail logic for the bot wohhoo"""
    if vc_check(member.id):
        print(pomo_data)
        if not pomo_data['pomo_active']:
            pomo_data['pomo_active'] = True
            await notif_channel.send(f"<@{pomo_data['member_id']}> Pomodoro started! :)")
            pomo_data['run_time'] = datetime.utcnow() + timedelta(minutes=pomo_data["total_pomo_time"])
            pomo_data['job'] = scheduler.add_job(
                finish_pomo, "date",
                run_date=pomo_data['run_time'],
                args=[member, pomo_data]
            )
            create_secondary_task(pomo_data)
        if pomo_data['paused']:
            await reschedule_job(pomo_data)
    else:
        if pomo_data['pomo_active'] and not pomo_data['paused'] and not pomo_data['break_status']:
            pomo_data['paused'] = True
            pomo_data['job'].pause()
            pomo_data['secondary_job'].pause()
            pomo_data['pause_time'] = datetime.utcnow()
            await notif_channel.send(f"<@{pomo_data['member_id']}> You left the VC prior to finishing your pomo. Please join the VC to continue your pomo.")


            
        
        

def vc_check(member_id):
    """Flag to check if the person is still in VC
       returns: Boolean
    """
    if member_id in pomo_data and member_id in VC_LIST: # Check if user currently in VC
        return True
    return False


@bot.event #VC events #leaving or joining a VC alert
async def on_voice_state_update(member, before, after):
    """Logic for if the person has left or joined the VC
        Supports:  vc_check
        Updates: VC_LIST to have the IDs of the people in the workspace VC """

    joined_voice_channel = None
    if before.channel is None and after.channel is not None:
        joined_voice_channel = True
    else:
        joined_voice_channel = False

    workspace_channel = bot.get_channel(813199122999803924)#tortoise workspace  VC ID

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