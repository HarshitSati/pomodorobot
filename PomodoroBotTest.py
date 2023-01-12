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

scheduler = AsyncIOScheduler(timezone=utc)

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

    pomo_data[member.id] = {"Pomo_time": pomo_time, "Number_of_pomos":number_of_pomos,
                          "Breat_time":break_time, "Total_time":total_time,'Elapsed_time': elapsed_time, 'pomo_active': False}
    

    await interaction.response.send_message("Join the VC to start the pomo!!")
    await pomo_logic(member, pomo_data[member.id])


def finish_pomo(member, pomo_data):
    print(f"Finished pomo for member {member}")


async def pomo_logic(member, pomo_data):
    channel = bot.get_channel(1041715750047596574) #unified channel to send notifs
    if pomo_check(member.id):
        print(pomo_data)
        if not pomo_data['pomo_active']:
            pomo_data['pomo_active'] = True
            await channel.send("Pomodoro started! :)")
            scheduler.add_job(
                finish_pomo, "date",
                run_date=datetime.utcnow() + timedelta(seconds=pomo_data["Pomo_time"]),
                args=[member, pomo_data]
            )

def pomo_check(member_id):
    print("pomo_data",pomo_data)
    print("VCLIST",VC_LIST)
    print("memberID",member_id)
    if member_id in pomo_data and member_id in VC_LIST: # Check if user currently in VC
        return True
    return False


@bot.event #VC events #leaving or joining a VC alert
async def on_voice_state_update(member, before, after):

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
    
    print(VC_LIST)


with open("token", "r", encoding="utf-8") as tf:
    TOKEN = tf.read()

bot.run(TOKEN)

