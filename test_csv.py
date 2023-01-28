import pandas as pd

pomo_data = {}

pomo_data[100] = {
    'member_id': 100, # Member_ID of user who started pomo
    'pomo_time': 25, # Time per pomo
    'number_of_pomos':3, # Number of pomos
    'number_of_breaks': 5, # Number of breaks
    'breaks_left': 2, # Breaks left (decremented after each break)
    'break_time':10,  # Time for each break
    'total_pomo_time': 50, # Total pomo time (number of pomos * pomo time)
    'total_time':60, # Total time (total pomo time + total break time)
    'job': None, # Main job (Finishes pomo when complete)
    'secondary_job': None, # Secondary job (Breaks)
    'pomo_active': False, # Whether the pomo has been started yet, when True user has started the pomo.
    'run_time': None, # Current time when the main job should run, changes with breaks
    'secondary_run_time': None, # Current time when the secondary job should run, changes with breaks
    'break_status': False, # Whether the use is currently on break
    'pause_time': None, # Time when the pomo was last paused, used to reschedule the main job.
    'paused': False # Whether the pomo is currently paused.
    }
df = pd.DataFrame(pomo_data)
df.head()
#df.to_csv("pomo_data.csv")