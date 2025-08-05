import tkinter as tk
from tkinter import ttk, messagebox
import itertools, random, json, os, sys

from quote_bank import QUOTE_BANK

SAVE_FILE      = "tasks.json"
POMODORO_GREEN = "#156653"
CHAMPAGNE      = "#f7e7ce"

# button colors
BUTTON_BG      = CHAMPAGNE
BUTTON_FG      = POMODORO_GREEN

# quadrant item colors
QUAD_COLORS = {
    1: "#FF6347",
    2: "#90EE90",
    3: "#FFD700",
    4: "#ADD8E6"
}


class TaskApp:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("One Step Closer To Your Goals")
        self.root.configure(bg=POMODORO_GREEN)

        self.tasks           = []   # list of (text, quad)
        self.completed_tasks = []   # list of (text, quad)
        self.pending_quad    = 1

        self.authors     = list(QUOTE_BANK.keys())
        self.quote_cycle = itertools.cycle(self.authors)

        self.setup_tabs()
        self.setup_task_area()
        self.setup_entry_bar()
        self.setup_completed_area()
        self.setup_quote_bar()

        self.load_tasks()
        self.bind_keys()

    def style_common(self, widget, **extra):
        widget.configure(bg=POMODORO_GREEN, fg=CHAMPAGNE, **extra)

    def bind_keys(self):
        self.task_entry.bind("<Return>", lambda e: self.add_task())
        self.root.bind("<BackSpace>", lambda e: self.move_selected_to_done())
        for i in (1, 2, 3, 4):
            for mod in ("Control", "Command"):
                self.root.bind(f"<{mod}-KeyPress-{i}>",
                               lambda e, q=i: self.set_pending_quad(q))

    def setup_tabs(self):
        self.notebook = ttk.Notebook(self.root)
        style = ttk.Style()
        style.theme_use('default')
        style.configure('TNotebook', background=POMODORO_GREEN, borderwidth=0)
        style.configure('TNotebook.Tab', background=POMODORO_GREEN,
                        foreground=CHAMPAGNE, borderwidth=0)
        style.map('TNotebook.Tab', background=[('selected', POMODORO_GREEN)])
        self.notebook.pack(fill="both", expand=True, padx=8, pady=8)

        self.tab_tasks = tk.Frame(self.notebook, bg=POMODORO_GREEN)
        self.tab_done  = tk.Frame(self.notebook, bg=POMODORO_GREEN)
        self.notebook.add(self.tab_tasks, text="Tasks")
        self.notebook.add(self.tab_done,  text="Done")

    def setup_entry_bar(self):
        self.task_entry = tk.Entry(self.root,
                                   bg=POMODORO_GREEN,
                                   fg=CHAMPAGNE,
                                   insertbackground=CHAMPAGNE,
                                   font=("Helvetica", 14))
        self.task_entry.pack(fill="x", padx=8, pady=(0, 8))
        self.task_entry.focus()

    def setup_task_area(self):
        box = tk.LabelFrame(self.tab_tasks,
                            text=" Tasks ",
                            bg=POMODORO_GREEN,
                            fg=CHAMPAGNE,
                            bd=2, relief="groove",
                            font=("Helvetica", 12, "bold"))
        box.pack(fill="both", expand=True, padx=8, pady=(8, 4))

        for r in (0, 1):
            box.grid_rowconfigure(r, weight=1)
        for c in (0, 1):
            box.grid_columnconfigure(c, weight=1)

        titles = {
            1: "I – Urgent + Important",
            2: "II – Not Urgent + Important",
            3: "III – Urgent + Not Important",
            4: "IV – Not Urgent + Not Important",
        }

        self.quads = {}
        for i in (1, 2, 3, 4):
            frame = tk.Frame(box, bg=POMODORO_GREEN)
            frame.grid(row=(0 if i in (1, 2) else 1),
                       column=(0 if i in (1, 3) else 1),
                       sticky="nsew", padx=4, pady=4)

            lbl = tk.Label(frame,
                           text=titles[i],
                           font=("Helvetica", 14, "underline", "bold"))
            self.style_common(lbl)
            lbl.pack(anchor="w", padx=4, pady=(4, 0))

            lb = tk.Listbox(frame,
                            bg=POMODORO_GREEN,
                            fg=QUAD_COLORS[i],
                            selectbackground=CHAMPAGNE,
                            activestyle="none",
                            highlightthickness=0,
                            font=("Helvetica", 13, "bold"))
            lb.pack(fill="both", expand=True, padx=4, pady=(0, 4))

            # double-click binding removed

            self.quads[i] = lb

        tk.Button(self.tab_tasks,
                  text="🚀 Launch Fresh Start",
                  font=("Helvetica", 12, "bold"),
                  bg=BUTTON_BG, fg=BUTTON_FG,
                  command=self.clear_current_tasks,
                  relief="flat")\
          .pack(fill="x", padx=8, pady=(2, 8))

    def setup_completed_area(self):
        box = tk.LabelFrame(self.tab_done,
                            text=" Done ",
                            bg=POMODORO_GREEN,
                            fg=CHAMPAGNE,
                            bd=2, relief="groove",
                            font=("Helvetica", 12, "bold"))
        box.pack(fill="both", expand=True, padx=8, pady=(8, 4))

        self.done_listbox = tk.Listbox(box,
                                       bg=POMODORO_GREEN,
                                       fg=CHAMPAGNE,
                                       selectbackground=CHAMPAGNE,
                                       activestyle="none",
                                       highlightthickness=0,
                                       font=("Helvetica", 13, "bold"))
        self.done_listbox.pack(fill="both", expand=True, padx=4, pady=4)

        frm = tk.Frame(self.tab_done, bg=POMODORO_GREEN)
        frm.pack(fill="x", padx=8, pady=(0, 8))
        for col in (0, 1, 2):
            frm.grid_columnconfigure(col, weight=1)

        tk.Button(frm,
                  text="🗑️  Delete Selected",
                  font=("Helvetica", 12, "bold"),
                  bg="white",       # white background
                  fg=BUTTON_FG,
                  command=self.delete_selected_done,
                  relief="flat")\
          .grid(row=0, column=0, sticky="w")

        tk.Button(frm,
                  text="🧹  Clear All",
                  font=("Helvetica", 12, "bold"),
                  bg="white",       # white background
                  fg=BUTTON_FG,
                  command=self.clear_done_tasks,
                  relief="flat")\
          .grid(row=0, column=1)

        tk.Button(frm,
                  text="📊  Show Stats",
                  font=("Helvetica", 12, "bold"),
                  bg="white",       # white background
                  fg=BUTTON_FG,
                  command=self.show_stats,
                  relief="flat")\
          .grid(row=0, column=2, sticky="e")


    def setup_quote_bar(self):
        bar = tk.Frame(self.root, bg=POMODORO_GREEN)
        bar.pack(side="bottom", pady=8)

        lbl = tk.Label(bar, text="🔄", font=("Helvetica", 16), cursor="hand2")
        self.style_common(lbl)
        lbl.bind("<Button-1>", lambda e: self.update_quote(manual=True))
        lbl.pack(side="left", padx=(0, 6))

        self.quote_label = tk.Label(bar,
                                    wraplength=600,
                                    justify="center",
                                    font=("Helvetica", 13))
        self.style_common(self.quote_label)
        self.quote_label.pack(side="left")
        self.update_quote()

    def refresh_quadrant(self, quad):
        lb = self.quads[quad]
        lb.delete(0, tk.END)
        count = 1
        for task_text, q in self.tasks:
            if q == quad:
                lb.insert(tk.END, f"{count}. {task_text}")
                lb.itemconfig(lb.size()-1, fg=QUAD_COLORS[quad])
                count += 1

    def refresh_all_quads(self):
        for q in self.quads:
            self.refresh_quadrant(q)
        self.refresh_done()

    def refresh_done(self):
        self.done_listbox.delete(0, tk.END)
        for idx, (task_text, orig_quad) in enumerate(self.completed_tasks, start=1):
            self.done_listbox.insert(tk.END, f"{idx}. {task_text}")
            self.done_listbox.itemconfig(
                self.done_listbox.size()-1,
                fg=QUAD_COLORS[orig_quad]
            )

    def add_task(self):
        txt = self.task_entry.get().strip()
        if not txt:
            return
        self.tasks.append((txt, self.pending_quad))
        self.task_entry.delete(0, tk.END)
        self.pending_quad = 1
        self.save_tasks()
        self.refresh_all_quads()

    def move_selected_to_done(self):
        for quad, lb in self.quads.items():
            sel = lb.curselection()
            if not sel:
                continue
            pos_in_quad = sel[0]
            quad_idxs = [i for i, (_, q) in enumerate(self.tasks) if q == quad]
            real_idx = quad_idxs[pos_in_quad]
            text, orig_quad = self.tasks.pop(real_idx)
            self.completed_tasks.append((text, orig_quad))
            self.save_tasks()
            self.refresh_all_quads()
            return

    def delete_selected_done(self):
        sel = self.done_listbox.curselection()
        if not sel:
            return
        self.completed_tasks.pop(sel[0])
        self.save_tasks()
        self.refresh_done()

    def clear_current_tasks(self):
        self.tasks.clear()
        self.save_tasks()
        self.refresh_all_quads()

    def clear_done_tasks(self):
        self.completed_tasks.clear()
        self.save_tasks()
        self.refresh_done()

    def set_pending_quad(self, quad: int):
        self.pending_quad = quad

    def load_tasks(self):
        if os.path.exists(SAVE_FILE):
            try:
                data = json.load(open(SAVE_FILE))
                self.tasks = data.get("tasks", [])
                self.completed_tasks = data.get("done", [])
            except:
                self.tasks = []
                self.completed_tasks = []
        else:
            self.tasks = []
            self.completed_tasks = []
            self.save_tasks()
        self.refresh_all_quads()

    def save_tasks(self):
        data = {"tasks": self.tasks, "done": self.completed_tasks}
        with open(SAVE_FILE, "w") as f:
            json.dump(data, f, indent=2)

    def show_stats(self):
        pending = len(self.tasks)
        done    = len(self.completed_tasks)
        messagebox.showinfo("Stats",
                            f"Pending: {pending}\nCompleted: {done}")

    def update_quote(self, manual=False):
        author = next(self.quote_cycle)
        quote  = random.choice(QUOTE_BANK[author])
        self.quote_label.config(text=f"{quote} — {author}")
        if not manual:
            self.root.after(120_000, self.update_quote)


if __name__ == "__main__":
    root = tk.Tk()
    TaskApp(root)
    root.mainloop()
