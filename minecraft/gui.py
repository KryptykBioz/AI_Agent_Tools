import tkinter as tk
from tkinter import ttk
import requests
import threading
import time
from datetime import datetime
from typing import Optional, Dict, Any

API_BASE = 'http://127.0.0.1:3001'

class MinecraftBotGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Minecraft Bot Control")
        self.root.geometry("1400x900")
        self.root.configure(bg='#111827')
        
        self.connected = False
        self.vision_data = None
        self.executing = False
        self.running = True
        
        self._setup_styles()
        self._build_ui()
        self._start_background_threads()
    
    def _setup_styles(self):
        style = ttk.Style()
        style.theme_use('default')
        
        # Dark theme colors
        bg_dark = '#111827'
        bg_panel = '#1f2937'
        bg_input = '#0f172a'
        fg_text = '#f3f4f6'
        fg_dim = '#9ca3af'
        border = '#374151'
        
        style.configure('Dark.TFrame', background=bg_panel, borderwidth=1, relief='solid')
        style.configure('Dark.TLabel', background=bg_panel, foreground=fg_text, font=('Consolas', 9))
        style.configure('Title.TLabel', background=bg_panel, foreground=fg_text, font=('Consolas', 12, 'bold'))
        style.configure('Dim.TLabel', background=bg_panel, foreground=fg_dim, font=('Consolas', 8))
        style.configure('Dark.TButton', background='#374151', foreground=fg_text, borderwidth=1, font=('Consolas', 9))
        
    def _build_ui(self):
        # Main container
        main = tk.Frame(self.root, bg='#111827')
        main.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Header
        self._build_header(main)
        
        # Status panels row
        status_row = tk.Frame(main, bg='#111827')
        status_row.pack(fill=tk.X, pady=(10, 0))
        
        self._build_status_panel(status_row)
        self._build_inventory_panel(status_row)
        self._build_threats_panel(status_row)
        
        # Quick actions
        self._build_quick_actions(main)
        
        # Command and blocks row
        cmd_row = tk.Frame(main, bg='#111827')
        cmd_row.pack(fill=tk.BOTH, expand=True, pady=(10, 0))
        
        self._build_command_panel(cmd_row)
        self._build_blocks_panel(cmd_row)
        
        # Activity log
        self._build_log_panel(main)
    
    def _build_header(self, parent):
        header = tk.Frame(parent, bg='#1f2937', highlightbackground='#374151', highlightthickness=1)
        header.pack(fill=tk.X, pady=(0, 10))
        
        left = tk.Frame(header, bg='#1f2937')
        left.pack(side=tk.LEFT, padx=15, pady=10)
        
        tk.Label(left, text="Minecraft Bot", bg='#1f2937', fg='#f3f4f6', 
                font=('Consolas', 16, 'bold')).pack(side=tk.LEFT)
        
        self.status_indicator = tk.Canvas(left, width=12, height=12, bg='#1f2937', highlightthickness=0)
        self.status_indicator.pack(side=tk.LEFT, padx=(10, 5))
        self.status_circle = self.status_indicator.create_oval(2, 2, 10, 10, fill='#ef4444', outline='')
        
        self.status_label = tk.Label(left, text="Disconnected", bg='#1f2937', fg='#f3f4f6', 
                                     font=('Consolas', 9))
        self.status_label.pack(side=tk.LEFT)
        
        right = tk.Frame(header, bg='#1f2937')
        right.pack(side=tk.RIGHT, padx=15, pady=10)
        
        self.health_label = tk.Label(right, text="❤ --/20", bg='#1f2937', fg='#9ca3af', 
                                     font=('Consolas', 10))
        self.health_label.pack(side=tk.LEFT, padx=10)
        
        self.food_label = tk.Label(right, text="🍖 --/20", bg='#1f2937', fg='#9ca3af', 
                                   font=('Consolas', 10))
        self.food_label.pack(side=tk.LEFT)
    
    def _build_status_panel(self, parent):
        frame = tk.Frame(parent, bg='#1f2937', highlightbackground='#374151', highlightthickness=1)
        frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 5))
        
        tk.Label(frame, text="Status", bg='#1f2937', fg='#f3f4f6', 
                font=('Consolas', 11, 'bold')).pack(anchor=tk.W, padx=10, pady=(10, 5))
        
        self.pos_label = tk.Label(frame, text="Position: --, --, --", bg='#1f2937', fg='#22d3ee', 
                                 font=('Consolas', 9), anchor=tk.W)
        self.pos_label.pack(fill=tk.X, padx=10, pady=2)
        
        self.biome_label = tk.Label(frame, text="Biome: --", bg='#1f2937', fg='#f3f4f6', 
                                   font=('Consolas', 9), anchor=tk.W)
        self.biome_label.pack(fill=tk.X, padx=10, pady=2)
        
        self.time_label = tk.Label(frame, text="Time: --", bg='#1f2937', fg='#f3f4f6', 
                                  font=('Consolas', 9), anchor=tk.W)
        self.time_label.pack(fill=tk.X, padx=10, pady=2)
        
        self.weather_label = tk.Label(frame, text="", bg='#1f2937', fg='#60a5fa', 
                                     font=('Consolas', 9), anchor=tk.W)
        self.weather_label.pack(fill=tk.X, padx=10, pady=(2, 10))
    
    def _build_inventory_panel(self, parent):
        frame = tk.Frame(parent, bg='#1f2937', highlightbackground='#374151', highlightthickness=1)
        frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5)
        
        tk.Label(frame, text="Inventory", bg='#1f2937', fg='#f3f4f6', 
                font=('Consolas', 11, 'bold')).pack(anchor=tk.W, padx=10, pady=(10, 5))
        
        self.holding_label = tk.Label(frame, text="Holding: empty", bg='#1f2937', fg='#fbbf24', 
                                     font=('Consolas', 9), anchor=tk.W)
        self.holding_label.pack(fill=tk.X, padx=10, pady=2)
        
        self.items_label = tk.Label(frame, text="Total Items: 0", bg='#1f2937', fg='#f3f4f6', 
                                   font=('Consolas', 9), anchor=tk.W)
        self.items_label.pack(fill=tk.X, padx=10, pady=2)
        
        self.inv_details = tk.Text(frame, bg='#1f2937', fg='#9ca3af', font=('Consolas', 8), 
                                  height=3, wrap=tk.WORD, borderwidth=0)
        self.inv_details.pack(fill=tk.BOTH, expand=True, padx=10, pady=(2, 10))
    
    def _build_threats_panel(self, parent):
        frame = tk.Frame(parent, bg='#1f2937', highlightbackground='#374151', highlightthickness=1)
        frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(5, 0))
        
        tk.Label(frame, text="Threats", bg='#1f2937', fg='#f3f4f6', 
                font=('Consolas', 11, 'bold')).pack(anchor=tk.W, padx=10, pady=(10, 5))
        
        self.threats_text = tk.Text(frame, bg='#1f2937', fg='#f87171', font=('Consolas', 9), 
                                   height=6, wrap=tk.WORD, borderwidth=0)
        self.threats_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 10))
    
    def _build_quick_actions(self, parent):
        frame = tk.Frame(parent, bg='#1f2937', highlightbackground='#374151', highlightthickness=1)
        frame.pack(fill=tk.X, pady=(10, 0))
        
        tk.Label(frame, text="Quick Actions", bg='#1f2937', fg='#f3f4f6', 
                font=('Consolas', 11, 'bold')).pack(anchor=tk.W, padx=10, pady=(10, 5))
        
        btn_frame = tk.Frame(frame, bg='#1f2937')
        btn_frame.pack(fill=tk.X, padx=10, pady=(0, 10))
        
        btns = [
            ("Stop", lambda: self._exec('stop', []), '#7f1d1d'),
            ("Get Wood", lambda: self._exec('gather', ['oak_log', 5]), '#374151'),
            ("Get Stone", lambda: self._exec('gather', ['stone', 10]), '#374151'),
            ("Status", lambda: self._exec('status', []), '#374151'),
        ]
        
        for text, cmd, color in btns:
            btn = tk.Button(btn_frame, text=text, command=cmd, bg=color, fg='#f3f4f6',
                          font=('Consolas', 9), relief=tk.FLAT, padx=15, pady=8,
                          cursor='hand2', activebackground='#4b5563')
            btn.pack(side=tk.LEFT, padx=5)
        
        self.attack_btn = tk.Button(btn_frame, text="Attack", bg='#7c2d12', fg='#f3f4f6',
                                   font=('Consolas', 9), relief=tk.FLAT, padx=15, pady=8,
                                   cursor='hand2', activebackground='#9a3412')
        self.attack_btn.pack(side=tk.LEFT, padx=5)
        self.attack_btn.pack_forget()
    
    def _build_command_panel(self, parent):
        frame = tk.Frame(parent, bg='#1f2937', highlightbackground='#374151', highlightthickness=1)
        frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 5))
        
        tk.Label(frame, text="Custom Command", bg='#1f2937', fg='#f3f4f6', 
                font=('Consolas', 11, 'bold')).pack(anchor=tk.W, padx=10, pady=(10, 5))
        
        self.cmd_var = tk.StringVar()
        cmd_combo = ttk.Combobox(frame, textvariable=self.cmd_var, 
                                values=['gather', 'goto', 'move', 'attack', 'stop', 'follow', 
                                       'craft', 'use', 'chat', 'build'],
                                font=('Consolas', 9), state='readonly')
        cmd_combo.pack(fill=tk.X, padx=10, pady=5)
        
        self.args_entry = tk.Entry(frame, bg='#0f172a', fg='#f3f4f6', font=('Consolas', 9),
                                  insertbackground='#f3f4f6', relief=tk.FLAT, borderwidth=1)
        self.args_entry.pack(fill=tk.X, padx=10, pady=5)
        self.args_entry.insert(0, "Args (comma-separated)")
        self.args_entry.bind('<FocusIn>', lambda e: self.args_entry.delete(0, tk.END) if self.args_entry.get() == "Args (comma-separated)" else None)
        self.args_entry.bind('<Return>', lambda e: self._execute_custom())
        
        exec_btn = tk.Button(frame, text="Execute", command=self._execute_custom,
                           bg='#1d4ed8', fg='#f3f4f6', font=('Consolas', 9, 'bold'),
                           relief=tk.FLAT, padx=20, pady=10, cursor='hand2',
                           activebackground='#2563eb')
        exec_btn.pack(fill=tk.X, padx=10, pady=(5, 10))
    
    def _build_blocks_panel(self, parent):
        frame = tk.Frame(parent, bg='#1f2937', highlightbackground='#374151', highlightthickness=1)
        frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(5, 0))
        
        tk.Label(frame, text="Nearby Blocks (0)", bg='#1f2937', fg='#f3f4f6', 
                font=('Consolas', 11, 'bold')).pack(anchor=tk.W, padx=10, pady=(10, 5))
        
        self.blocks_text = tk.Text(frame, bg='#1f2937', fg='#9ca3af', font=('Consolas', 8), 
                                  height=8, wrap=tk.WORD, borderwidth=0)
        self.blocks_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 10))
    
    def _build_log_panel(self, parent):
        frame = tk.Frame(parent, bg='#1f2937', highlightbackground='#374151', highlightthickness=1)
        frame.pack(fill=tk.BOTH, expand=True, pady=(10, 0))
        
        tk.Label(frame, text="Activity Log", bg='#1f2937', fg='#f3f4f6', 
                font=('Consolas', 11, 'bold')).pack(anchor=tk.W, padx=10, pady=(10, 5))
        
        self.log_text = tk.Text(frame, bg='#1f2937', fg='#9ca3af', font=('Consolas', 8), 
                               height=10, wrap=tk.WORD, borderwidth=0)
        self.log_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 10))
        
        self.log_text.tag_config('error', foreground='#f87171')
        self.log_text.tag_config('success', foreground='#4ade80')
        self.log_text.tag_config('cmd', foreground='#22d3ee')
        self.log_text.tag_config('info', foreground='#9ca3af')
    
    def _add_log(self, msg, tag='info'):
        ts = datetime.now().strftime('%H:%M:%S')
        self.log_text.insert(tk.END, f"[{ts}] {msg}\n", tag)
        self.log_text.see(tk.END)
        
        lines = int(self.log_text.index('end-1c').split('.')[0])
        if lines > 100:
            self.log_text.delete('1.0', '51.0')
    
    def _execute_custom(self):
        cmd = self.cmd_var.get()
        if not cmd:
            return
        
        args_text = self.args_entry.get()
        if args_text == "Args (comma-separated)" or not args_text:
            args = []
        else:
            args = [a.strip() for a in args_text.split(',')]
            args = [float(a) if a.replace('.', '').replace('-', '').isdigit() else a for a in args]
        
        self._exec(cmd, args)
        self.args_entry.delete(0, tk.END)
        self.args_entry.insert(0, "Args (comma-separated)")
    
    def _exec(self, cmd, args):
        if not self.connected:
            self._add_log("Bot not connected", 'error')
            return
        
        if self.executing:
            self._add_log("Command already executing", 'error')
            return
        
        def run():
            self.executing = True
            self._add_log(f"Executing: {cmd} {args}", 'cmd')
            
            try:
                r = requests.post(f"{API_BASE}/api/action",
                                json={'action': cmd, 'args': args},
                                headers={'Content-Type': 'application/json'},
                                timeout=15)
                
                d = r.json()
                msg = d.get('message', 'Complete')
                tag = 'success' if d.get('status') == 'success' else 'error'
                self.root.after(0, self._add_log, msg, tag)
                
            except Exception as e:
                self.root.after(0, self._add_log, f"Error: {str(e)[:100]}", 'error')
            
            self.executing = False
        
        threading.Thread(target=run, daemon=True).start()
    
    def _check_health(self):
        while self.running:
            try:
                r = requests.get(f"{API_BASE}/api/health", timeout=2)
                d = r.json()
                connected = d.get('botConnected', False) and d.get('botSpawned', False)
                
                self.root.after(0, self._update_connection, connected)
                
            except:
                self.root.after(0, self._update_connection, False)
            
            time.sleep(5)
    
    def _update_connection(self, connected):
        self.connected = connected
        color = '#22c55e' if connected else '#ef4444'
        text = "Connected" if connected else "Disconnected"
        
        self.status_indicator.itemconfig(self.status_circle, fill=color)
        self.status_label.config(text=text)
    
    def _fetch_vision(self):
        while self.running:
            if self.connected:
                try:
                    r = requests.get(f"{API_BASE}/api/vision", timeout=3)
                    d = r.json()
                    
                    if d.get('status') == 'success':
                        self.root.after(0, self._update_vision, d.get('vision', {}))
                        
                except:
                    pass
            
            time.sleep(5)
    
    def _update_vision(self, vision):
        self.vision_data = vision
        
        # Health & Food
        h = vision.get('health', 0)
        f = vision.get('food', 0)
        
        h_color = '#ef4444' if h < 10 else '#22c55e'
        f_color = '#fb923c' if f < 6 else '#22c55e'
        
        self.health_label.config(text=f"❤ {h}/20", fg=h_color)
        self.food_label.config(text=f"🍖 {f}/20", fg=f_color)
        
        # Position
        p = vision.get('position', {})
        self.pos_label.config(text=f"Position: {p.get('x', 0):.1f}, {p.get('y', 0):.1f}, {p.get('z', 0):.1f}")
        
        # Biome
        biome = vision.get('biome', 'unknown').replace('_', ' ')
        self.biome_label.config(text=f"Biome: {biome}")
        
        # Time
        phase = vision.get('time', {}).get('phase', 'unknown')
        self.time_label.config(text=f"Time: {phase}")
        
        # Weather
        w = vision.get('weather', {})
        weather_text = ""
        if w.get('isThundering'):
            weather_text = "⚡ Thunder"
        elif w.get('isRaining'):
            weather_text = "🌧 Rain"
        self.weather_label.config(text=weather_text)
        
        # Inventory
        inv = vision.get('inventory', {})
        hand = inv.get('itemInHand')
        
        if hand:
            holding = f"{hand.get('name', 'unknown')}"
            if hand.get('count', 1) > 1:
                holding += f" x{hand['count']}"
            self.holding_label.config(text=f"Holding: {holding}")
        else:
            self.holding_label.config(text="Holding: empty")
        
        self.items_label.config(text=f"Total Items: {inv.get('totalItems', 0)}")
        
        self.inv_details.delete('1.0', tk.END)
        cats = inv.get('categories', {})
        for cat in ['tools', 'food', 'weapons']:
            items = cats.get(cat, [])
            if items:
                items_str = ', '.join([f"{i['name']} x{i['count']}" for i in items[:3]])
                self.inv_details.insert(tk.END, f"🔧 {cat.title()}: {items_str}\n")
        
        # Threats
        entities = vision.get('entitiesInSight', [])
        hostile = [e for e in entities if e.get('isHostile')]
        
        self.threats_text.delete('1.0', tk.END)
        if hostile:
            for e in hostile[:5]:
                threat = e.get('threatLevel', 5)
                self.threats_text.insert(tk.END, 
                    f"{e.get('type', 'unknown')} - {e.get('distance', 0):.1f}m {e.get('direction', '')}\n"
                    f"Threat: {threat}/10\n\n")
            
            # Show attack button
            if not self.attack_btn.winfo_ismapped():
                self.attack_btn.config(command=lambda: self._exec('attack', [hostile[0]['type']]))
                self.attack_btn.pack(side=tk.LEFT, padx=5)
        else:
            self.threats_text.insert(tk.END, "No threats")
            if self.attack_btn.winfo_ismapped():
                self.attack_btn.pack_forget()
        
        # Blocks
        blocks = vision.get('blocksInSight', [])
        self.blocks_text.delete('1.0', tk.END)
        
        for b in blocks[:10]:
            pos = b.get('position', {})
            self.blocks_text.insert(tk.END, 
                f"{b.get('name', 'unknown')} - {b.get('distance', 0):.1f}m "
                f"({pos.get('x', 0)}, {pos.get('y', 0)}, {pos.get('z', 0)})\n")
    
    def _start_background_threads(self):
        threading.Thread(target=self._check_health, daemon=True).start()
        threading.Thread(target=self._fetch_vision, daemon=True).start()
    
    def on_close(self):
        self.running = False
        self.root.destroy()

if __name__ == '__main__':
    root = tk.Tk()
    app = MinecraftBotGUI(root)
    root.protocol("WM_DELETE_WINDOW", app.on_close)
    root.mainloop()