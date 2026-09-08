import customtkinter as ctk
from tkinter import messagebox, filedialog, simpledialog
import json, os, sys, shutil, urllib.parse, webbrowser, subprocess, tempfile, time
from pathlib import Path
from datetime import datetime, date, timedelta

APP_NAME = "Birthday Reminder Pro"
TASK_NAME = "Birthday Reminder Pro - Automatic Notification"

DATA_DIR = Path.home() / "BirthdayReminder"
DATA_FILE = DATA_DIR / "birthdays.json"
PHOTOS_DIR = DATA_DIR / "photos"
SETTINGS_FILE = DATA_DIR / "settings.json"
DATA_DIR.mkdir(exist_ok=True)
PHOTOS_DIR.mkdir(exist_ok=True)

try:
    from PIL import Image, ImageOps, ImageTk
    PIL_OK = True
except Exception:
    PIL_OK = False

try:
    from winotify import Notification, audio
    TOAST_OK = True
except Exception:
    TOAST_OK = False

DEFAULT_SETTINGS = {
    "sender_name": "P.T.Parmar",
    "greetings": [
        "🎂 Happy Birthday, {name}! 🎉\n\nWishing you a wonderful birthday filled with happiness, good health and beautiful moments.\n\nHave a fantastic year ahead! 🌷🎈\n\nWith warm wishes,\n{sender}",
        "Many many happy returns of the day, {name}! 🎉🎂\n\nMay your special day bring you lots of joy, peace and success. Wishing you a beautiful year ahead.\n\nBest wishes,\n{sender}",
        "🎈 Happy Birthday, {name}! 🎂\n\nMay your life always be filled with smiles, good health, love and success. Enjoy your special day to the fullest! 🌹✨\n\nWarm regards,\n{sender}",
        "🎉 Wishing you a very Happy Birthday, {name}! 🎂\n\nMay this new year of your life bring wonderful opportunities, memorable moments and endless happiness.\n\nHave a great day!\n{sender}",
        "🌟 Happy Birthday, dear {name}! 🎂\n\nWishing you happiness today and always. May all your good wishes come true and may the coming year be your best one yet.\n\nLots of good wishes,\n{sender}"
    ]
}

def load_settings():
    try:
        d = json.loads(SETTINGS_FILE.read_text(encoding="utf-8"))
        if not isinstance(d, dict):
            return DEFAULT_SETTINGS.copy()
        return {**DEFAULT_SETTINGS, **d}
    except Exception:
        return DEFAULT_SETTINGS.copy()

SETTINGS = load_settings()

def load_birthdays():
    try:
        d = json.loads(DATA_FILE.read_text(encoding="utf-8"))
        return d if isinstance(d, dict) else {}
    except Exception:
        return {}

def next_birthday(ds, today=None):
    today = today or date.today()
    b = datetime.strptime(ds, "%d-%m-%Y").date()
    try:
        n = b.replace(year=today.year)
    except ValueError:
        n = date(today.year, 2, 28)
    if n < today:
        try:
            n = b.replace(year=today.year + 1)
        except ValueError:
            n = date(today.year + 1, 2, 28)
    return n

def build_notification_photo(items):
    if not PIL_OK:
        return items[0][2] if items else ""
    paths = [p for _, _, p in items if p and Path(p).exists()]
    if not paths:
        return ""
    try:
        imgs = []
        for p in paths[:4]:
            im = Image.open(p).convert("RGB")
            im = ImageOps.fit(im, (220, 220))
            imgs.append(im)
        canvas = Image.new("RGB", (440, 440), "white")
        positions = [(0, 0), (220, 0), (0, 220), (220, 220)]
        for im, pos in zip(imgs, positions):
            canvas.paste(im, pos)
        out = Path(tempfile.gettempdir()) / "BirthdayReminder_notification.jpg"
        canvas.save(out, "JPEG", quality=90)
        return str(out)
    except Exception:
        return paths[0]

def show_aesthetic_notification(items, special=False):
    import tkinter as tk
    root = tk.Tk()
    root.overrideredirect(True)
    root.attributes("-topmost", True)
    root.configure(bg="#0b1220")
    sw, sh = root.winfo_screenwidth(), root.winfo_screenheight()
    width, height = 470, 205 if not special else 190
    x, y = sw - width - 24, sh - height - 55
    root.geometry(f"{width}x{height}+{x}+{y}")
    outer = tk.Frame(root, bg="#1f2a44", bd=0)
    outer.pack(fill="both", expand=True, padx=1, pady=1)
    body = tk.Frame(outer, bg="#0f172a")
    body.pack(fill="both", expand=True, padx=2, pady=2)
    top = tk.Frame(body, bg="#0f172a")
    top.pack(fill="x", padx=18, pady=(15, 5))
    tk.Label(top, text="🎂", bg="#0f172a", fg="white", font=("Segoe UI Emoji", 24)).pack(side="left")
    title = "Birthday Today" if not special else "Birthday Tomorrow"
    tk.Label(top, text=title, bg="#0f172a", fg="#f8fafc", font=("Segoe UI", 17, "bold")).pack(side="left", padx=10)
    tk.Button(top, text="×", command=root.destroy, bg="#0f172a", fg="#94a3b8", activebackground="#1e293b", activeforeground="white", bd=0, font=("Segoe UI", 16), cursor="hand2").pack(side="right")
    content = tk.Frame(body, bg="#0f172a")
    content.pack(fill="both", expand=True, padx=18, pady=5)
    photo = build_notification_photo(items)
    if PIL_OK and photo and Path(photo).exists():
        try:
            im = Image.open(photo).convert("RGB")
            im = ImageOps.fit(im, (78, 78))
            img = ImageTk.PhotoImage(im)
            av = tk.Label(content, image=img, bg="#0f172a")
            av.image = img
            av.pack(side="left", padx=(0, 14))
        except Exception:
            tk.Label(content, text="🎁", bg="#0f172a", fg="#a78bfa", font=("Segoe UI Emoji", 42)).pack(side="left", padx=(0, 14))
    else:
        tk.Label(content, text="🎁", bg="#0f172a", fg="#a78bfa", font=("Segoe UI Emoji", 42)).pack(side="left", padx=(0, 14))
    textf = tk.Frame(content, bg="#0f172a")
    textf.pack(side="left", fill="both", expand=True)
    if special:
        names = ", ".join(n for n, _, _ in items)
        reasons = ", ".join(sorted(set(r for _, r, _ in items)))
        message = f"{names}\nBirthday is tomorrow ({reasons})."
    else:
        names = ", ".join(n for n, _, _ in items)
        message = names
    tk.Label(textf, text=message, bg="#0f172a", fg="#ffffff", justify="left", anchor="w", wraplength=315, font=("Segoe UI", 13, "bold")).pack(anchor="w", pady=(5, 3))
    if not special:
        tk.Label(textf, text="Don't forget to send your birthday wishes! 🎉", bg="#0f172a", fg="#94a3b8", justify="left", wraplength=315, font=("Segoe UI", 10)).pack(anchor="w")
    root.after(15000, root.destroy)
    root.mainloop()

def headless_startup_check():
    birthdays = load_birthdays()
    today = date.today()
    todays = []
    special = []
    for name, raw in birthdays.items():
        d = raw if isinstance(raw, dict) else {"date": raw}
        try:
            b = datetime.strptime(d["date"], "%d-%m-%Y").date()
            if b.month == today.month and b.day == today.day:
                todays.append((name, today.year - b.year, d.get("photo", "")))
            nxt = next_birthday(d["date"], today)
            if nxt - today == timedelta(days=1):
                occ = (nxt.day - 1) // 7 + 1
                reason = ""
                if nxt.weekday() == 6:
                    reason = "Sunday"
                elif nxt.weekday() == 5 and occ == 2:
                    reason = "2nd Saturday"
                elif nxt.weekday() == 5 and occ == 4:
                    reason = "4th Saturday"
                if reason:
                    special.append((name, reason, d.get("photo", "")))
        except Exception as e:
            print("Birthday check skipped:", name, e)
    if todays:
        show_aesthetic_notification(todays, special=False)
    if special:
        show_aesthetic_notification(special, special=True)

def exe_path():
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve()
    return Path(__file__).resolve()

def install_scheduled_task():
    if os.name != "nt":
        return False
    try:
        exe = exe_path()
        if not getattr(sys, "frozen", False):
            pyw = Path(sys.executable).with_name("pythonw.exe")
            runner = pyw if pyw.exists() else Path(sys.executable)
            command = f'"{runner}" "{exe}" --notify'
        else:
            command = f'"{exe}" --notify'
        startup = Path(os.environ.get("APPDATA", "")) / "Microsoft/Windows/Start Menu/Programs/Startup"
        startup.mkdir(parents=True, exist_ok=True)
        vbs = startup / "Birthday Reminder Pro - Background.vbs"
        q = command.replace('"', '""')
        vbs.write_text('Set WshShell = CreateObject("WScript.Shell")\n' f'WshShell.Run "{q}", 0, False\n', encoding="utf-8")
        try:
            subprocess.run(["schtasks", "/Delete", "/TN", TASK_NAME, "/F"], capture_output=True, creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
        except Exception:
            pass
        return True
    except Exception as e:
        print("Startup registration error:", e)
        return False

class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title(APP_NAME)
        self.geometry("1200x780")
        self.minsize(1000, 650)
        ctk.set_appearance_mode("dark")
        self.C = {"bg":"#090f1f","panel":"#0e1729","card":"#15223a","card2":"#1c2b48","text":"#f8fafc","muted":"#94a3b8","purple":"#7c3aed","purple2":"#a78bfa","green":"#22c55e","yellow":"#f59e0b"}
        self.configure(fg_color=self.C["bg"])
        self.birthdays = load_birthdays()
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)
        self.build_sidebar(); self.build_main(); self.refresh()
        self.after(1000, self.update_clock)
        self.after(1200, install_scheduled_task)
    def update_clock(self):
        if self.winfo_exists():
            self.clock.configure(text=datetime.now().strftime("%d %b %Y  •  %I:%M %p")); self.after(1000, self.update_clock)
    def build_sidebar(self):
        s=ctk.CTkFrame(self,width=230,corner_radius=0,fg_color=self.C["panel"]); s.grid(row=0,column=0,sticky="nsew"); s.grid_propagate(False)
        ctk.CTkLabel(s,text="🎂",font=("Segoe UI",42)).pack(pady=(32,0)); ctk.CTkLabel(s,text="Birthday",font=("Segoe UI",25,"bold")).pack(); ctk.CTkLabel(s,text="REMINDER PRO",font=("Segoe UI",11,"bold"),text_color=self.C["purple2"]).pack(pady=(0,32))
        items=[("⌂   Dashboard",lambda:self.set_filter("All")),("🎂   Today",lambda:self.set_filter("Today")),("◷   Upcoming",lambda:self.set_filter("Upcoming")),("＋   Add Birthday",lambda:self.person_dialog()),("⚙   Settings",self.settings_dialog)]
        for text,cmd in items: ctk.CTkButton(s,text=text,command=cmd,anchor="w",height=44,corner_radius=10,fg_color="transparent",hover_color=self.C["card2"],font=("Segoe UI",13)).pack(fill="x",padx=14,pady=3)
        ctk.CTkFrame(s,height=2,fg_color=self.C["card2"]).pack(fill="x",padx=18,pady=25)
        ctk.CTkLabel(s,text="AUTOMATIC",font=("Segoe UI",10,"bold"),text_color=self.C["muted"]).pack(anchor="w",padx=22)
        ctk.CTkLabel(s,text="✓ Background Windows login alert\n✓ Today's birthday alert\n✓ Sunday / 2nd / 4th Saturday alert\n✓ Photo profile\n✓ WhatsApp greetings",justify="left",font=("Segoe UI",11),text_color=self.C["muted"],wraplength=190).pack(anchor="w",padx=22,pady=8)
        ctk.CTkLabel(s,text="P.T.Parmar",font=("Segoe UI",10,"bold"),text_color="#64748b").pack(side="bottom",pady=20)
    def build_main(self):
        m=ctk.CTkFrame(self,fg_color=self.C["bg"],corner_radius=0); m.grid(row=0,column=1,sticky="nsew"); m.grid_columnconfigure(0,weight=1); m.grid_rowconfigure(3,weight=1)
        top=ctk.CTkFrame(m,fg_color="transparent"); top.grid(row=0,column=0,sticky="ew",padx=30,pady=(25,10)); top.grid_columnconfigure(0,weight=1)
        ctk.CTkLabel(top,text="Birthday Dashboard",font=("Segoe UI",27,"bold")).grid(row=0,column=0,sticky="w")
        self.clock=ctk.CTkLabel(top,text="",font=("Segoe UI",13),text_color=self.C["purple2"]); self.clock.grid(row=0,column=1,sticky="e")
        self.search=ctk.CTkEntry(top,placeholder_text="🔍  Search...",width=230,height=38,corner_radius=10); self.search.grid(row=1,column=0,pady=(10,0),sticky="w"); self.search.bind("<KeyRelease>",lambda e:self.refresh())
        stats=ctk.CTkFrame(m,fg_color="transparent"); stats.grid(row=1,column=0,sticky="ew",padx=30,pady=10)
        for i in range(3): stats.grid_columnconfigure(i,weight=1)
        self.stat_total=self.stat(stats,0,"🎂","TOTAL BIRTHDAYS"); self.stat_today=self.stat(stats,1,"🎉","TODAY"); self.stat_next=self.stat(stats,2,"📅","NEXT BIRTHDAY")
        title=ctk.CTkFrame(m,fg_color="transparent"); title.grid(row=2,column=0,sticky="ew",padx=30,pady=(15,8)); ctk.CTkLabel(title,text="Your birthdays",font=("Segoe UI",20,"bold")).pack(side="left"); ctk.CTkLabel(title,text="  •  Click Wish to open WhatsApp",font=("Segoe UI",11),text_color=self.C["muted"]).pack(side="left",pady=5)
        self.scroll=ctk.CTkScrollableFrame(m,fg_color="transparent",corner_radius=0); self.scroll.grid(row=3,column=0,sticky="nsew",padx=24,pady=(0,20))
    def stat(self,parent,col,icon,title):
        f=ctk.CTkFrame(parent,fg_color=self.C["card"],corner_radius=15,height=82); f.grid(row=0,column=col,sticky="ew",padx=5); f.grid_propagate(False); ctk.CTkLabel(f,text=icon,font=("Segoe UI",23)).pack(side="left",padx=(17,10)); x=ctk.CTkFrame(f,fg_color="transparent"); x.pack(side="left",pady=12); ctk.CTkLabel(x,text=title,font=("Segoe UI",9,"bold"),text_color=self.C["muted"]).pack(anchor="w"); val=ctk.CTkLabel(x,text="0",font=("Segoe UI",18,"bold")); val.pack(anchor="w"); return val
    def set_filter(self,f): self.filter=f; self.refresh()
    def next_date(self,ds): return next_birthday(ds)
    def refresh(self):
        for w in self.scroll.winfo_children(): w.destroy()
        q=self.search.get().strip().lower(); today=date.today(); rows=[]
        for name,raw in self.birthdays.items():
            d=raw if isinstance(raw,dict) else {"date":raw,"phone":"","photo":""}
            if q and q not in name.lower(): continue
            try:
                n=self.next_date(d["date"]); days=(n-today).days
                if getattr(self,"filter","All")=="Today" and days!=0: continue
                if getattr(self,"filter","All")=="Upcoming" and days==0: continue
                rows.append((days,name,d,n))
            except Exception: pass
        rows.sort(key=lambda x:(x[0],x[1].lower())); self.stat_total.configure(text=str(len(self.birthdays))); self.stat_today.configure(text=str(sum(1 for _,d in self.birthdays.items() if self.is_today(d)))); self.stat_next.configure(text=("Today" if rows and rows[0][0]==0 else (f"{rows[0][0]} days" if rows else "—")))
        for r in rows: self.card(*r)
    def is_today(self,d):
        try:
            ds=d["date"] if isinstance(d,dict) else d; b=datetime.strptime(ds,"%d-%m-%Y").date(); t=date.today(); return b.month==t.month and b.day==t.day
        except Exception: return False
    def card(self,days,name,d,nxt):
        f=ctk.CTkFrame(self.scroll,fg_color=self.C["card"],corner_radius=16,height=118); f.pack(fill="x",pady=5,padx=4); f.pack_propagate(False); photo=d.get("photo","") if isinstance(d,dict) else ""
        avatar=ctk.CTkLabel(f,text="👤",font=("Segoe UI",28),width=80); avatar.pack(side="left",padx=(12,3))
        if PIL_OK and photo and Path(photo).exists():
            try:
                im=Image.open(photo).convert("RGB"); im=ImageOps.fit(im,(68,68)); img=ctk.CTkImage(light_image=im,dark_image=im,size=(68,68)); avatar.configure(image=img,text=""); avatar._birthday_image=img
            except Exception: pass
        mid=ctk.CTkFrame(f,fg_color="transparent"); mid.pack(side="left",fill="both",expand=True,pady=17); ctk.CTkLabel(mid,text=name,font=("Segoe UI",17,"bold")).pack(anchor="w"); ctk.CTkLabel(mid,text=f"🎂 {d.get('date','')}   📱 {d.get('phone','') or 'No number'}",font=("Segoe UI",10),text_color=self.C["muted"]).pack(anchor="w",pady=(5,0))
        badge_text="TODAY" if days==0 else ("TOMORROW" if days==1 else f"{days} DAYS"); badge_color=self.C["green"] if days==0 else (self.C["yellow"] if days==1 else self.C["card2"])
        ctk.CTkLabel(f,text=f"  {badge_text}  ",font=("Segoe UI",10,"bold"),fg_color=badge_color,text_color="#07110a" if days<2 else self.C["purple2"],corner_radius=9).pack(side="left",padx=5)
        ctk.CTkButton(f,text="🗑 Delete",width=88,height=36,corner_radius=10,fg_color="#7f1d1d",hover_color="#991b1b",text_color="#fee2e2",font=("Segoe UI",10,"bold"),command=lambda n=name:self.delete_person(n)).pack(side="right",padx=3)
        ctk.CTkButton(f,text="🎁  Wish",width=105,height=36,corner_radius=10,fg_color=self.C["green"],hover_color="#16a34a",text_color="#03120a",font=("Segoe UI",11,"bold"),command=lambda n=name:self.send_whatsapp(n)).pack(side="right",padx=12)
        ctk.CTkButton(f,text="✎",width=38,height=36,corner_radius=10,fg_color=self.C["card2"],command=lambda n=name:self.person_dialog(n)).pack(side="right",padx=3)
    def delete_person(self,name):
        if not messagebox.askyesno("Delete Birthday",f"Delete {name}'s birthday and saved contact/photo information?",parent=self): return
        d=self.birthdays.get(name,{}); photo=d.get("photo","") if isinstance(d,dict) else ""; self.birthdays.pop(name,None); self.save()
        if photo:
            try:
                p=Path(photo)
                if p.exists() and p.parent.resolve()==PHOTOS_DIR.resolve(): p.unlink()
            except Exception: pass
        self.refresh()
    def save(self): DATA_FILE.write_text(json.dumps(self.birthdays,indent=2,ensure_ascii=False),encoding="utf-8")
    def person_dialog(self,name=None):
        old=self.birthdays.get(name,{}) if name else {}
        if isinstance(old,str): old={"date":old,"phone":"","photo":""}
        w=ctk.CTkToplevel(self); w.title("Edit Birthday" if name else "Add Birthday"); w.geometry("500x600"); w.configure(fg_color=self.C["panel"]); w.transient(self); w.grab_set(); ctk.CTkLabel(w,text="Edit Birthday" if name else "Add Birthday",font=("Segoe UI",24,"bold")).pack(pady=25)
        def fld(t,v):
            ctk.CTkLabel(w,text=t,font=("Segoe UI",10,"bold"),text_color=self.C["muted"]).pack(anchor="w",padx=38,pady=(7,3)); e=ctk.CTkEntry(w,height=40,corner_radius=10); e.pack(fill="x",padx=38); e.insert(0,v); return e
        ne=fld("PERSON NAME",name or ""); de=fld("BIRTHDAY • DD-MM-YYYY",old.get("date","")); pe=fld("WHATSAPP MOBILE",old.get("phone","")); selected=[old.get("photo","")]; lab=ctk.CTkLabel(w,text=("📷 "+Path(selected[0]).name if selected[0] else "No photo selected"),text_color=self.C["muted"]); lab.pack(pady=14)
        def pick():
            p=filedialog.askopenfilename(parent=w,filetypes=[("Images","*.jpg *.jpeg *.png *.webp *.bmp")])
            if p: selected[0]=p; lab.configure(text="📷 "+Path(p).name)
        ctk.CTkButton(w,text="🖼️  Choose Person Photo",command=pick,height=40,corner_radius=10,fg_color=self.C["card2"]).pack(fill="x",padx=38)
        def save():
            n=ne.get().strip(); ds=de.get().strip(); ph=pe.get().strip()
            if not n or not ds: messagebox.showwarning("Missing","Name and birthday are required.",parent=w); return
            try: datetime.strptime(ds,"%d-%m-%Y")
            except Exception: messagebox.showerror("Invalid Date","Use DD-MM-YYYY.",parent=w); return
            photo=selected[0]; old_photo=str(old.get("photo",""))
            if photo and Path(photo).exists() and str(photo)!=old_photo:
                dest=PHOTOS_DIR/(str(abs(hash(n)))+Path(photo).suffix.lower()); shutil.copy2(photo,dest); photo=str(dest)
            if name and name!=n: self.birthdays.pop(name,None)
            self.birthdays[n]={"date":ds,"phone":ph,"photo":photo}; self.save(); w.destroy(); self.refresh()
        ctk.CTkButton(w,text="Save Birthday",command=save,height=45,corner_radius=10,fg_color=self.C["purple"],font=("Segoe UI",12,"bold")).pack(fill="x",padx=38,pady=25)
    def send_whatsapp(self,name):
        d=self.birthdays.get(name,{}); d={"date":d,"phone":""} if isinstance(d,str) else d; ph=d.get("phone","")
        if not ph:
            ph=simpledialog.askstring("WhatsApp Number",f"Enter {name}'s WhatsApp number with country code:\nExample: +919876543210",parent=self)
            if not ph: return
            d["phone"]=ph.strip(); self.birthdays[name]=d; self.save(); self.refresh()
        digits="".join(c for c in ph if c.isdigit()); digits=digits[2:] if ph.startswith("00") else digits
        if len(digits)<8: messagebox.showerror("Invalid Number","Enter a valid number with country code.",parent=self); return
        choices=SETTINGS.get("greetings",DEFAULT_SETTINGS["greetings"]); w=ctk.CTkToplevel(self); w.title("Choose Greeting"); w.geometry("650x520"); w.configure(fg_color=self.C["panel"]); w.transient(self); w.grab_set(); ctk.CTkLabel(w,text=f"Choose a greeting for {name}",font=("Segoe UI",21,"bold")).pack(pady=(25,8)); ctk.CTkLabel(w,text=f"From: {SETTINGS.get('sender_name','P.T.Parmar')}",font=("Segoe UI",11),text_color=self.C["purple2"]).pack(pady=(0,15)); box=ctk.CTkTextbox(w,font=("Segoe UI",11),corner_radius=10); box.pack(fill="both",expand=True,padx=28,pady=8); box.insert("1.0",choices[0].format(name=name,sender=SETTINGS.get("sender_name","P.T.Parmar")))
        def use():
            msg=box.get("1.0","end").strip(); webbrowser.open("https://wa.me/"+digits+"?text="+urllib.parse.quote(msg)); w.destroy()
        quick=ctk.CTkFrame(w,fg_color="transparent"); quick.pack(fill="x",padx=28,pady=8)
        for i,g in enumerate(choices): ctk.CTkButton(quick,text=f"Style {i+1}",width=90,height=30,command=lambda g=g:self.replace_greeting(box,g,name)).pack(side="left",padx=3)
        ctk.CTkButton(w,text="Open WhatsApp with this Greeting →",command=use,height=44,corner_radius=10,fg_color=self.C["green"],text_color="#03120a",font=("Segoe UI",12,"bold")).pack(fill="x",padx=28,pady=(8,25))
    def replace_greeting(self,box,g,name): box.delete("1.0","end"); box.insert("1.0",g.format(name=name,sender=SETTINGS.get("sender_name","P.T.Parmar")))
    def settings_dialog(self):
        w=ctk.CTkToplevel(self); w.title("Settings"); w.geometry("600x600"); w.configure(fg_color=self.C["panel"]); w.transient(self); ctk.CTkLabel(w,text="Settings",font=("Segoe UI",25,"bold")).pack(pady=22); ctk.CTkLabel(w,text="Your name (shown at the end of greetings)",font=("Segoe UI",11,"bold")).pack(anchor="w",padx=35); sender=ctk.CTkEntry(w,height=40,corner_radius=10); sender.pack(fill="x",padx=35,pady=7); sender.insert(0,SETTINGS.get("sender_name","P.T.Parmar")); ctk.CTkLabel(w,text="Choose Style 1–5 when sending a WhatsApp birthday greeting.",font=("Segoe UI",10),text_color=self.C["muted"],wraplength=500).pack(pady=15)
        def save_settings(): SETTINGS["sender_name"]=sender.get().strip() or "P.T.Parmar"; SETTINGS_FILE.write_text(json.dumps(SETTINGS,indent=2,ensure_ascii=False),encoding="utf-8"); w.destroy()
        ctk.CTkButton(w,text="Save Settings",command=save_settings,height=44,corner_radius=10,fg_color=self.C["purple"]).pack(fill="x",padx=35,pady=15)
        ctk.CTkButton(w,text="🔔 Test Windows Notification",command=lambda: show_aesthetic_notification([("Test",0,"")]),height=42,corner_radius=10,fg_color=self.C["card2"]).pack(fill="x",padx=35,pady=8)
        ctk.CTkButton(w,text="✓ Reinstall Automatic Login Notification",command=lambda:(install_scheduled_task(),messagebox.showinfo("Automatic Notification","Automatic background notification has been installed in your Windows Startup folder. The main app will NOT open at login.",parent=w)),height=42,corner_radius=10,fg_color=self.C["card2"]).pack(fill="x",padx=35,pady=8)

if __name__ == "__main__":
    if "--notify" in sys.argv:
        headless_startup_check(); raise SystemExit(0)
    app=App(); app.mainloop()
