
#uwuOWO dis is for testing
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from typing import Optional
from platform import platform
import discord
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from pytz import utc
from datetime import datetime, timedelta

from discord.ext import commands
bot = commands.Bot(intents=discord.Intents.all(), command_prefix='ps!')

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user} (ID: {bot.user.id})")
    print("------")


def test_func():
    global job
    print('hi')

    job = scheduler.add_job(
    test_func, "date",
    run_date=datetime.utcnow() + timedelta(seconds=30))


scheduler = AsyncIOScheduler(timezone=utc)
scheduler.start()


job = scheduler.add_job(
    test_func, "date",
    run_date=datetime.utcnow() + timedelta(seconds=30)
)

pomo_data = {"Pomo_time": 25, "Number_of_pomos":2,
             "break_time":5, "Total_time":50,'Elapsed_time': 0, 'pomo_active': False, 'time_paused': None}


choice_dict = {'Pause': 0, 'Resume': 1, 'Check': -1}


@bot.slash_command(guild_ids=[1022156035823251536])
@discord.option("status", description="Whether to pause or resume the task", choices=['Pause', 'Resume', 'Check'])
async def task_status(interaction: discord.Interaction, status: str = 'Check'): #wont accept bool hence we use int
    """Checks status of task, and pauses/resumes based on input!"""
    status = choice_dict[status]

    if status != -1:
        if status:
            current_time = datetime.utcnow()

            break_time = current_time - pomo_data['time_paused']
            previous_next_run_time = job.next_run_time
            job.modify(next_run_time = previous_next_run_time + break_time)

            job.resume()
        else:
            job.pause()

            pomo_data['time_paused'] = datetime.utcnow()
    
    print(f"job: {job.trigger[0]}")


with open("token", "r", encoding="utf-8") as tf:
    TOKEN = tf.read()

bot.run(TOKEN)