# Filename: BASE/tools/installed/league_of_legends/component.py
"""
League of Legends Tool - GUI Component
Dynamic GUI panel for real-time match monitoring and threat analysis
"""
import tkinter as tk
from tkinter import ttk
from BASE.interface.gui_themes import DarkTheme
import asyncio
from typing import Optional, Dict, Any


class LeagueOfLegendsComponent:
    """GUI component for League of Legends spectator mode"""

    __slots__ = (
        'parent_gui', 'ai_core', 'logger', 'league_tool', 'panel_frame',
        'status_label', 'game_time_label', 'champion_label', 'stats_text',
        'events_text', 'threat_indicator', 'update_job', '_last_game_data'
    )
    
    def __init__(self, parent_gui, ai_core, logger):
        self.parent_gui = parent_gui
        self.ai_core = ai_core
        self.logger = logger
        self.league_tool = None
        self.panel_frame = None
        self.status_label = None
        self.game_time_label = None
        self.champion_label = None
        self.stats_text = None
        self.events_text = None
        self.threat_indicator = None
        self.update_job = None
        self._last_game_data = None
    
    def create_panel(self, parent_frame):
        """Create the League of Legends panel"""
        self.panel_frame = ttk.LabelFrame(
            parent_frame,
            text="League of Legends - Live Match Monitor",
            style="Dark.TLabelframe"
        )
        self.panel_frame.pack(fill=tk.BOTH, expand=True, pady=(5, 0))
        
        # Status section
        self._create_status_section()
        
        # Threat indicator section
        self._create_threat_section()
        
        # Champion info section
        self._create_champion_section()
        
        # Stats display section
        self._create_stats_section()
        
        # Events section
        self._create_events_section()
        
        # Start status updates
        self._schedule_status_update()
        
        return self.panel_frame
    
    def _create_status_section(self):
        """Create status and connection display"""
        status_frame = ttk.Frame(self.panel_frame)
        status_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # Connection status
        self.status_label = tk.Label(
            status_frame,
            text="⚫ Checking connection...",
            font=("Segoe UI", 9),
            foreground=DarkTheme.FG_MUTED,
            background=DarkTheme.BG_DARKER,
            anchor=tk.W
        )
        self.status_label.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        # Game time
        self.game_time_label = tk.Label(
            status_frame,
            text="--:--",
            font=("Consolas", 9, "bold"),
            foreground=DarkTheme.FG_PRIMARY,
            background=DarkTheme.BG_DARKER,
            width=8
        )
        self.game_time_label.pack(side=tk.RIGHT, padx=(5, 0))
        
        # Refresh button
        refresh_btn = ttk.Button(
            status_frame,
            text="🔄",
            command=self._manual_refresh,
            width=3
        )
        refresh_btn.pack(side=tk.RIGHT)
    
    def _create_threat_section(self):
        """Create threat level indicator"""
        threat_frame = ttk.Frame(self.panel_frame)
        threat_frame.pack(fill=tk.X, padx=5, pady=(0, 5))
        
        ttk.Label(
            threat_frame,
            text="Threat Level:",
            style="TLabel"
        ).pack(side=tk.LEFT, padx=(0, 5))
        
        self.threat_indicator = tk.Label(
            threat_frame,
            text="⚫ Unknown",
            font=("Segoe UI", 9, "bold"),
            foreground=DarkTheme.FG_MUTED,
            background=DarkTheme.BG_DARKER,
            anchor=tk.W
        )
        self.threat_indicator.pack(side=tk.LEFT, fill=tk.X, expand=True)
    
    def _create_champion_section(self):
        """Create champion info display"""
        champ_frame = ttk.LabelFrame(
            self.panel_frame,
            text="Your Champion",
            style="Dark.TLabelframe"
        )
        champ_frame.pack(fill=tk.X, padx=5, pady=(0, 5))
        
        self.champion_label = tk.Label(
            champ_frame,
            text="No active match",
            font=("Segoe UI", 11, "bold"),
            foreground=DarkTheme.ACCENT_PURPLE,
            background=DarkTheme.BG_DARKER,
            anchor=tk.W,
            pady=8,
            padx=8
        )
        self.champion_label.pack(fill=tk.X)
    
    def _create_stats_section(self):
        """Create stats display"""
        stats_frame = ttk.LabelFrame(
            self.panel_frame,
            text="Champion Stats",
            style="Dark.TLabelframe"
        )
        stats_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=(0, 5))
        
        # Scrollable text widget
        scrollbar = ttk.Scrollbar(stats_frame, orient='vertical')
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.stats_text = tk.Text(
            stats_frame,
            height=8,
            wrap=tk.WORD,
            state=tk.DISABLED,
            font=("Consolas", 9),
            bg=DarkTheme.BG_DARK,
            fg=DarkTheme.FG_PRIMARY,
            insertbackground=DarkTheme.FG_PRIMARY,
            selectbackground=DarkTheme.ACCENT_PURPLE,
            selectforeground=DarkTheme.FG_PRIMARY,
            borderwidth=1,
            relief="solid",
            yscrollcommand=scrollbar.set
        )
        self.stats_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        scrollbar.config(command=self.stats_text.yview)
        
        # Configure text tags
        self.stats_text.tag_configure(
            "label",
            foreground=DarkTheme.FG_SECONDARY
        )
        self.stats_text.tag_configure(
            "value",
            foreground=DarkTheme.FG_PRIMARY,
            font=("Consolas", 9, "bold")
        )
        self.stats_text.tag_configure(
            "warning",
            foreground=DarkTheme.ACCENT_RED,
            font=("Consolas", 9, "bold")
        )
        self.stats_text.tag_configure(
            "success",
            foreground=DarkTheme.ACCENT_GREEN,
            font=("Consolas", 9, "bold")
        )
    
    def _create_events_section(self):
        """Create recent events display"""
        events_frame = ttk.LabelFrame(
            self.panel_frame,
            text="Recent Events",
            style="Dark.TLabelframe"
        )
        events_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=(0, 5))
        
        # Scrollable text widget
        scrollbar = ttk.Scrollbar(events_frame, orient='vertical')
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.events_text = tk.Text(
            events_frame,
            height=6,
            wrap=tk.WORD,
            state=tk.DISABLED,
            font=("Consolas", 9),
            bg=DarkTheme.BG_DARK,
            fg=DarkTheme.FG_PRIMARY,
            insertbackground=DarkTheme.FG_PRIMARY,
            selectbackground=DarkTheme.ACCENT_PURPLE,
            selectforeground=DarkTheme.FG_PRIMARY,
            borderwidth=1,
            relief="solid",
            yscrollcommand=scrollbar.set
        )
        self.events_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        scrollbar.config(command=self.events_text.yview)
        
        # Configure tags
        self.events_text.tag_configure(
            "timestamp",
            foreground=DarkTheme.FG_MUTED
        )
        self.events_text.tag_configure(
            "event",
            foreground=DarkTheme.FG_PRIMARY
        )
        self.events_text.tag_configure(
            "critical",
            foreground=DarkTheme.ACCENT_RED,
            font=("Consolas", 9, "bold")
        )
    
    def _manual_refresh(self):
        """Manually refresh game data"""
        self.logger.system("[League] Manual refresh requested")
        self._update_display()
    
    def _update_display(self):
        """Update all display sections with current game data"""
        self.league_tool = self._get_league_tool()
        
        if not self.league_tool:
            self._update_status_no_tool()
            return
        
        # Check if API is available
        if not self.league_tool.is_available():
            self._update_status_disconnected()
            return
        
        # Get game data
        game_data = self.league_tool._get_all_game_data()
        
        if not game_data:
            self._update_status_no_match()
            return
        
        # Get threat analysis
        analysis = self.league_tool.threat_detector.analyze_game_state(game_data)
        
        # Update all sections
        self._update_status_connected()
        self._update_game_time(game_data)
        self._update_threat_indicator(analysis)
        self._update_champion_info(game_data)
        self._update_stats_display(game_data, analysis)
        self._update_events_display(game_data)
        
        self._last_game_data = game_data
    
    def _update_status_no_tool(self):
        """Update UI when tool not available"""
        self.status_label.config(
            text="⚫ Tool Not Available",
            foreground=DarkTheme.FG_MUTED
        )
        self.game_time_label.config(text="--:--")
        self.threat_indicator.config(
            text="⚫ Unknown",
            foreground=DarkTheme.FG_MUTED
        )
        self.champion_label.config(text="Tool not initialized")
        self._clear_stats()
        self._clear_events()
    
    def _update_status_disconnected(self):
        """Update UI when API disconnected"""
        self.status_label.config(
            text="🔴 Disconnected - League Client Not Running",
            foreground=DarkTheme.ACCENT_RED
        )
        self.game_time_label.config(text="--:--")
        self.threat_indicator.config(
            text="⚫ No Data",
            foreground=DarkTheme.FG_MUTED
        )
        self.champion_label.config(text="No active match detected")
        self._clear_stats()
        self._clear_events()
    
    def _update_status_no_match(self):
        """Update UI when no match active"""
        self.status_label.config(
            text="🟡 Connected - No Active Match",
            foreground=DarkTheme.ACCENT_ORANGE if hasattr(DarkTheme, 'ACCENT_ORANGE') else DarkTheme.FG_SECONDARY
        )
        self.game_time_label.config(text="--:--")
        self.threat_indicator.config(
            text="⚫ Standby",
            foreground=DarkTheme.FG_MUTED
        )
        self.champion_label.config(text="Waiting for match to start...")
        self._clear_stats()
        self._clear_events()
    
    def _update_status_connected(self):
        """Update UI when connected and in match"""
        self.status_label.config(
            text="🟢 Live Match - Monitoring Active",
            foreground=DarkTheme.ACCENT_GREEN
        )
    
    def _update_game_time(self, game_data: Dict[str, Any]):
        """Update game time display"""
        game_time = game_data.get('gameData', {}).get('gameTime', 0)
        minutes = int(game_time // 60)
        seconds = int(game_time % 60)
        self.game_time_label.config(text=f"{minutes:02d}:{seconds:02d}")
    
    def _update_threat_indicator(self, analysis: Dict[str, Any]):
        """Update threat level indicator"""
        threat_level = analysis.get('threat_level', 0)
        
        if threat_level >= 9:
            indicator = "🔴 CRITICAL"
            color = DarkTheme.ACCENT_RED
        elif threat_level >= 7:
            indicator = "🟠 HIGH"
            color = DarkTheme.ACCENT_ORANGE if hasattr(DarkTheme, 'ACCENT_ORANGE') else DarkTheme.ACCENT_RED
        elif threat_level >= 4:
            indicator = "🟡 ELEVATED"
            color = DarkTheme.ACCENT_ORANGE if hasattr(DarkTheme, 'ACCENT_ORANGE') else DarkTheme.FG_SECONDARY
        else:
            indicator = "🟢 Normal"
            color = DarkTheme.ACCENT_GREEN
        
        self.threat_indicator.config(
            text=f"{indicator} ({threat_level}/10)",
            foreground=color
        )
        
        # Add threat details if available
        if analysis.get('threats'):
            threats_str = ", ".join(analysis['threats'])
            self.threat_indicator.config(
                text=f"{indicator} ({threat_level}/10) - {threats_str}"
            )
    
    def _update_champion_info(self, game_data: Dict[str, Any]):
        """Update champion name display"""
        active_player = game_data.get('activePlayer', {})
        all_players = game_data.get('allPlayers', [])
        
        # Find champion name
        champion_name = "Unknown"
        active_summoner = active_player.get('summonerName', '')
        
        for player in all_players:
            if player.get('summonerName') == active_summoner:
                champion_name = player.get('championName', 'Unknown')
                break
        
        # Get level
        level = active_player.get('championStats', {}).get('level', 0)
        
        self.champion_label.config(
            text=f"{champion_name} (Level {level})"
        )
    
    def _update_stats_display(self, game_data: Dict[str, Any], analysis: Dict[str, Any]):
        """Update stats text display"""
        self.stats_text.config(state=tk.NORMAL)
        self.stats_text.delete("1.0", tk.END)
        
        active_player = game_data.get('activePlayer', {})
        stats = active_player.get('championStats', {})
        
        # Health
        current_hp = stats.get('currentHealth', 0)
        max_hp = stats.get('maxHealth', 1)
        hp_pct = (current_hp / max_hp * 100) if max_hp > 0 else 0
        
        self.stats_text.insert(tk.END, "Health: ", "label")
        if hp_pct <= 30:
            self.stats_text.insert(tk.END, f"{current_hp:.0f}/{max_hp:.0f} ({hp_pct:.0f}%) ⚠️\n", "warning")
        else:
            self.stats_text.insert(tk.END, f"{current_hp:.0f}/{max_hp:.0f} ({hp_pct:.0f}%)\n", "value")
        
        # Mana/Energy
        current_mana = stats.get('resourceValue', 0)
        max_mana = stats.get('resourceMax', 1)
        mana_pct = (current_mana / max_mana * 100) if max_mana > 0 else 0
        
        self.stats_text.insert(tk.END, "Mana/Energy: ", "label")
        if mana_pct <= 20:
            self.stats_text.insert(tk.END, f"{current_mana:.0f}/{max_mana:.0f} ({mana_pct:.0f}%) ⚠️\n", "warning")
        else:
            self.stats_text.insert(tk.END, f"{current_mana:.0f}/{max_mana:.0f} ({mana_pct:.0f}%)\n", "value")
        
        # Gold
        gold = active_player.get('currentGold', 0)
        self.stats_text.insert(tk.END, "Gold: ", "label")
        self.stats_text.insert(tk.END, f"{gold:.0f}g\n", "value")
        
        # KDA
        kills = stats.get('kills', 0)
        deaths = stats.get('deaths', 0)
        assists = stats.get('assists', 0)
        self.stats_text.insert(tk.END, "KDA: ", "label")
        self.stats_text.insert(tk.END, f"{kills}/{deaths}/{assists}\n", "value")
        
        # CS
        cs = stats.get('creepScore', 0)
        self.stats_text.insert(tk.END, "CS: ", "label")
        self.stats_text.insert(tk.END, f"{cs}\n", "value")
        
        # Combat stats
        self.stats_text.insert(tk.END, "\nCombat Stats:\n", "label")
        self.stats_text.insert(tk.END, f"  AD: ", "label")
        self.stats_text.insert(tk.END, f"{stats.get('attackDamage', 0):.0f}\n", "value")
        self.stats_text.insert(tk.END, f"  AP: ", "label")
        self.stats_text.insert(tk.END, f"{stats.get('abilityPower', 0):.0f}\n", "value")
        self.stats_text.insert(tk.END, f"  Armor: ", "label")
        self.stats_text.insert(tk.END, f"{stats.get('armor', 0):.0f}\n", "value")
        self.stats_text.insert(tk.END, f"  MR: ", "label")
        self.stats_text.insert(tk.END, f"{stats.get('magicResist', 0):.0f}\n", "value")
        
        self.stats_text.config(state=tk.DISABLED)
    
    def _update_events_display(self, game_data: Dict[str, Any]):
        """Update recent events display"""
        self.events_text.config(state=tk.NORMAL)
        self.events_text.delete("1.0", tk.END)
        
        events = game_data.get('events', {}).get('Events', [])
        
        if not events:
            self.events_text.insert(tk.END, "No events yet...", "event")
        else:
            # Show last 10 events
            recent_events = events[-10:]
            
            for event in reversed(recent_events):
                event_time = event.get('EventTime', 0)
                minutes = int(event_time // 60)
                seconds = int(event_time % 60)
                
                event_type = event.get('EventName', '')
                event_desc = self._format_event_short(event)
                
                # Timestamp
                self.events_text.insert(tk.END, f"[{minutes:02d}:{seconds:02d}] ", "timestamp")
                
                # Event (critical or normal)
                is_critical = event_type in {'ChampionKill', 'DragonKill', 'BaronKill', 'Ace'}
                tag = "critical" if is_critical else "event"
                self.events_text.insert(tk.END, f"{event_desc}\n", tag)
        
        self.events_text.config(state=tk.DISABLED)
        self.events_text.see(tk.END)
    
    def _format_event_short(self, event: Dict[str, Any]) -> str:
        """Format event for display"""
        event_type = event.get('EventName', '')
        
        if event_type == 'ChampionKill':
            killer = event.get('KillerName', '?')
            victim = event.get('VictimName', '?')
            return f"💀 {killer} killed {victim}"
        elif event_type == 'DragonKill':
            killer = event.get('KillerName', '?')
            dragon = event.get('DragonType', 'Dragon')
            return f"🐉 {killer}'s team took {dragon}"
        elif event_type == 'BaronKill':
            return "👹 Baron Nashor slain"
        elif event_type == 'HeraldKill':
            return "🦀 Rift Herald slain"
        elif event_type == 'TurretKilled':
            return "🗼 Turret destroyed"
        elif event_type == 'InhibKilled':
            return "🏛️ Inhibitor destroyed"
        elif event_type == 'Ace':
            return "💥 ACE! Team eliminated"
        
        return event_type
    
    def _clear_stats(self):
        """Clear stats display"""
        self.stats_text.config(state=tk.NORMAL)
        self.stats_text.delete("1.0", tk.END)
        self.stats_text.insert(tk.END, "No match data available", "label")
        self.stats_text.config(state=tk.DISABLED)
    
    def _clear_events(self):
        """Clear events display"""
        self.events_text.config(state=tk.NORMAL)
        self.events_text.delete("1.0", tk.END)
        self.events_text.insert(tk.END, "No match data available", "label")
        self.events_text.config(state=tk.DISABLED)
    
    def _schedule_status_update(self):
        """Schedule periodic status updates"""
        if self.panel_frame and self.panel_frame.winfo_exists():
            self._update_display()
            # Update every 2 seconds for real-time feel
            self.update_job = self.panel_frame.after(2000, self._schedule_status_update)
    
    def _get_league_tool(self):
        """Get League tool instance from AI Core"""
        if not hasattr(self.ai_core, 'tool_manager'):
            return None
        
        tool_manager = self.ai_core.tool_manager
        
        # Check if tool is active
        if 'league_of_legends' not in tool_manager._active_tools:
            return None
        
        return tool_manager._active_tools.get('league_of_legends')
    
    def cleanup(self):
        """Cleanup component resources"""
        # Cancel scheduled updates
        if self.update_job:
            try:
                self.panel_frame.after_cancel(self.update_job)
            except:
                pass
        
        self.logger.system("[League] Component cleaned up")


# Factory function for dynamic loading
def create_component(parent_gui, ai_core, logger):
    """
    Factory function called by GUI system
    
    Args:
        parent_gui: Main GUI instance
        ai_core: AI Core instance
        logger: Logger instance
        
    Returns:
        LeagueOfLegendsComponent instance
    """
    return LeagueOfLegendsComponent(parent_gui, ai_core, logger)