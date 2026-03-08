import tkinter as tk

class BotApp(tk.Tk):
    def __init__(self, plan_obj=None):
        super().__init__()
        self.plan_obj = plan_obj

try:
    app = BotApp("pro")
    print("Success")
except Exception as e:
    import traceback
    traceback.print_exc()
