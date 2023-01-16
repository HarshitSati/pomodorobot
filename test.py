
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


def start_job():
    run_time = datetime.utcnow() + timedelta(seconds=30)

    job = scheduler.add_job(
    test_func, "date",
    run_date=run_time)

    pomo_data['run_time'] = run_time

    return job

def reschedule_job(job, time_paused, previous_run_time):
    current_time = datetime.utcnow()

    break_time = current_time - time_paused

    new_run_time = previous_run_time + break_time

    pomo_data['run_time'] = new_run_time

    job.reschedule("date", run_date = new_run_time)

    print("job resumed")


def create_break_job(job, break_time):
    job.pause()

    time_paused = datetime.utcnow()

    break_job = scheduler.add_job(reschedule_job, "date", run_date = datetime.utcnow() + timedelta(seconds=break_time), args=[job, time_paused, pomo_data['run_time']])





def test_func():
    global job
    print('hi')

    job = start_job()


scheduler = AsyncIOScheduler(timezone=utc)
scheduler.start()


pomo_data = {"Pomo_time": 25, "Number_of_pomos":2,
             "break_time":5, "Total_time":50,'Elapsed_time': 0, 'pomo_active': False, 'time_paused': None, 'run_time': None}

job = start_job()

choice_dict = {'Pause': 0, 'Resume': 1, 'Check': -1}


@bot.slash_command(guild_ids=[1022156035823251536])
@discord.option("status", description="Whether to pause or resume the task", choices=['Pause', 'Resume', 'Check'])
async def task_status(interaction: discord.Interaction, status: str = 'Check'): #wont accept bool hence we use int
    """Checks status of task, and pauses/resumes based on input!"""
    status = choice_dict[status]

    if status != -1:
        if status:
            pomo_data['run_time'] = reschedule_job(job)

            job.resume()
        else:
            create_break_job(job, 10)
    
    print(f"job: {job}")


with open("token", "r", encoding="utf-8") as tf:
    TOKEN = tf.read()

bot.run(TOKEN)