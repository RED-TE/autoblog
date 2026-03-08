import os

filepath = r"C:\Users\jhxox\Desktop\blolg_aoto\bot_app.py"
with open(filepath, "r", encoding="utf-8") as f:
    lines = f.readlines()

for i, line in enumerate(lines):
    if line.strip() == "def __init__(self, plan_obj=None):":
        # The constructor definition is correct
        pass
    if line.strip() == "super().__init__()":
        pass
    if line.strip() == "self.plan_obj = plan_obj":
        pass

# The error was: BotApp.__init__() takes 1 positional argument but 2 were given
# Let's inspect line 57 
print(lines[56:65])
