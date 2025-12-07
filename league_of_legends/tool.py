# Filename: BASE/tools/installed/league_of_legends/tool.py
"""
League of Legends Tool - Simplified Architecture
Single master class with start() and end() lifecycle
Includes context loop for real-time match data and threat analysis
Spectator mode only - no command execution
"""
import asyncio
import time
from typing import List, Dict, Any, Optional
from BASE.handlers.base_tool import BaseTool
import requests


class LeagueThreatDetector:
    """Analyzes League game state for critical events"""
    
    CRITICAL_EVENTS = {
        'ChampionKill', 'DragonKill', 'BaronKill', 'HeraldKill', 
        'TurretKilled', 'InhibKilled', 'Ace'
    }
    
    DANGER_HP_THRESHOLD = 30
    LOW_MANA_THRESHOLD = 20
    
    @staticmethod
    def analyze_game_state(game_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze game state for critical situations"""
        if not game_data:
            return {
                'has_critical_event': False,
                'has_health_danger': False,
                'has_mana_issue': False,
                'latest_event': None,
                'health_percent': None,
                'threat_level': 0
            }
        
        analysis = {
            'has_critical_event': False,
            'has_health_danger': False,
            'has_mana_issue': False,
            'latest_event': None,
            'health_percent': None,
            'threat_level': 0,
            'threats': []
        }
        
        # Check active player status
        active_player = game_data.get('activePlayer', {})
        if active_player:
            stats = active_player.get('championStats', {})
            
            # Health analysis
            current_hp = stats.get('currentHealth', 0)
            max_hp = stats.get('maxHealth', 1)
            hp_percent = (current_hp / max_hp * 100) if max_hp > 0 else 0
            analysis['health_percent'] = hp_percent
            
            if hp_percent <= LeagueThreatDetector.DANGER_HP_THRESHOLD:
                analysis['has_health_danger'] = True
                analysis['threat_level'] = 9 if hp_percent <= 15 else 7
                analysis['threats'].append(f"low health ({hp_percent:.0f}%)")
            
            # Mana analysis
            current_mana = stats.get('resourceValue', 0)
            max_mana = stats.get('resourceMax', 1)
            mana_percent = (current_mana / max_mana * 100) if max_mana > 0 else 0
            
            if mana_percent <= LeagueThreatDetector.LOW_MANA_THRESHOLD:
                analysis['has_mana_issue'] = True
                analysis['threats'].append(f"low mana ({mana_percent:.0f}%)")
        
        # Check recent events
        events = game_data.get('events', {}).get('Events', [])
        if events:
            latest = events[-1]
            event_type = latest.get('EventName', '')
            
            if event_type in LeagueThreatDetector.CRITICAL_EVENTS:
                analysis['has_critical_event'] = True
                event_details = LeagueThreatDetector._format_event(latest)
                analysis['latest_event'] = {
                    'type': event_type,
                    'time': latest.get('EventTime', 0),
                    'details': event_details
                }
                analysis['threat_level'] = max(analysis['threat_level'], 8)
                analysis['threats'].append(event_details)
        
        return analysis
    
    @staticmethod
    def _format_event(event: Dict[str, Any]) -> str:
        """Format event details for context"""
        event_type = event.get('EventName', '')
        
        if event_type == 'ChampionKill':
            killer = event.get('KillerName', 'Someone')
            victim = event.get('VictimName', 'Someone')
            return f"{killer} eliminated {victim}"
        elif event_type == 'DragonKill':
            killer = event.get('KillerName', 'Team')
            dragon_type = event.get('DragonType', 'Dragon')
            return f"{killer}'s team secured {dragon_type} Drake"
        elif event_type == 'BaronKill':
            return "Baron Nashor eliminated"
        elif event_type == 'HeraldKill':
            return "Rift Herald eliminated"
        elif event_type == 'TurretKilled':
            return "Turret destroyed"
        elif event_type == 'InhibKilled':
            return "Inhibitor destroyed"
        elif event_type == 'Ace':
            return "ACE - Entire team eliminated"
        
        return event_type


class LeagueOfLegendsTool(BaseTool):
    """
    League of Legends spectator with real-time match data
    Proactively injects game state and critical events into thought buffer
    Spectator mode only - no command execution available
    """
    
    @property
    def name(self) -> str:
        return "league_of_legends"
    
    def has_context_loop(self) -> bool:
        """Enable background context loop for match awareness"""
        return True
    
    async def initialize(self) -> bool:
        """
        Initialize League of Legends spectator system
        
        Returns:
            True if initialization successful (always returns True for graceful degradation)
        """
        # Get API configuration
        self.api_host = getattr(self._controls, 'LEAGUE_API_HOST', 'https://127.0.0.1')
        self.api_port = getattr(self._controls, 'LEAGUE_API_PORT', 2999)
        self.api_base = f"{self.api_host}:{self.api_port}"
        self.timeout = 2
        
        # Caching
        self.cached_data = None
        self.cache_timestamp = 0.0
        self.cache_duration = 1.0
        
        # Threat detection
        self.threat_detector = LeagueThreatDetector()
        self.last_threat_analysis = {}
        self.last_event_count = 0
        
        # Check initial connection
        connected = self._check_api_available()
        
        if self._logger:
            if connected:
                self._logger.system(
                    f"[League] Spectator mode ready: Connected (API: {self.api_base})"
                )
            else:
                self._logger.warning(
                    f"[League] Live Client API not accessible (API: {self.api_base})"
                )
        
        # Always return True for graceful degradation
        return True
    
    async def cleanup(self):
        """Cleanup League interface resources"""
        self.cached_data = None
        self.last_threat_analysis = {}
        
        if self._logger:
            self._logger.system("[League] Cleanup complete")
    
    def is_available(self) -> bool:
        """
        Check if League Live Client API is accessible
        
        Returns:
            True if API is responding
        """
        return self._check_api_available()
    
    def _check_api_available(self) -> bool:
        """Check if League Live Client API is accessible"""
        try:
            response = requests.get(
                f"{self.api_base}/liveclientdata/allgamedata",
                verify=False,
                timeout=self.timeout
            )
            return response.status_code == 200
        except requests.exceptions.RequestException:
            return False
    
    def get_status(self) -> Dict[str, Any]:
        """
        Get League API status
        
        Returns:
            Status dictionary with connection info
        """
        connected = self.is_available()
        
        status = {
            'available': connected,
            'connected': connected,
            'api_base': self.api_base,
            'mode': 'spectator',
            'supports_commands': False
        }
        
        if connected and self.cached_data:
            game_time = self.cached_data.get('gameData', {}).get('gameTime', 0)
            status['game_time'] = game_time
        
        return status
    
    async def context_loop(self, thought_buffer):
        """
        Background loop for real-time match awareness
        Monitors game state and injects critical updates into thought buffer
        
        Args:
            thought_buffer: ThoughtBuffer instance for injecting game state
        """
        if self._logger:
            self._logger.system("[League] Context loop started")
        
        while self._running:
            try:
                if not self.is_available():
                    # Wait longer if API not available
                    await asyncio.sleep(5.0)
                    continue
                
                # Get current game state
                game_data = self._get_all_game_data()
                
                if game_data:
                    # Analyze for threats and critical events
                    analysis = self.threat_detector.analyze_game_state(game_data)
                    self.last_threat_analysis = analysis
                    
                    # Check for new events
                    events = game_data.get('events', {}).get('Events', [])
                    current_event_count = len(events)
                    has_new_event = current_event_count > self.last_event_count
                    self.last_event_count = current_event_count
                    
                    # Determine if we should inject context
                    should_inject = False
                    urgency = 5
                    
                    # Critical health/mana
                    if analysis['threat_level'] >= 7:
                        should_inject = True
                        urgency = analysis['threat_level']
                    
                    # Critical events
                    elif has_new_event and analysis.get('has_critical_event'):
                        should_inject = True
                        urgency = 8
                    
                    # Inject context if needed
                    if should_inject:
                        context = self._format_game_context(game_data, analysis)
                        
                        thought_buffer.add_processed_thought(
                            content=context,
                            source='league_match',
                            urgency_override=urgency
                        )
                        
                        if self._logger:
                            threats = ', '.join(analysis['threats']) if analysis['threats'] else 'general update'
                            self._logger.tool(
                                f"[League] Injected game state (urgency: {urgency}, {threats})"
                            )
                
                # Check every 2 seconds for responsive updates
                await asyncio.sleep(2.0)
                
            except asyncio.CancelledError:
                # Normal cancellation when tool stops
                break
            except Exception as e:
                if self._logger:
                    self._logger.error(f"[League] Context loop error: {e}")
                # Continue running despite errors
                await asyncio.sleep(2.0)
        
        if self._logger:
            self._logger.system("[League] Context loop stopped")
    
    async def execute(self, command: str, args: List[Any]) -> Dict[str, Any]:
        """
        Execute League command (spectator mode only)
        
        League is spectator-only - no command execution available
        Only supports 'get_context' for manual data retrieval
        
        Args:
            command: Command name (only 'get_context' supported)
            args: Command arguments
            
        Returns:
            Standardized result dict
        """
        if self._logger:
            self._logger.tool(f"[League] Command: '{command}', args: {args}")
        
        # League doesn't support commands (spectator mode only)
        if command == 'get_context' or command == '':
            game_data = self._get_all_game_data()
            
            if game_data:
                analysis = self.threat_detector.analyze_game_state(game_data)
                self.last_threat_analysis = analysis
                context = self._format_game_context(game_data, analysis)
                
                return self._success_result(
                    context,
                    metadata={
                        'mode': 'spectator',
                        'threat_analysis': analysis
                    }
                )
            else:
                return self._error_result(
                    'No active game or API unavailable',
                    metadata={'mode': 'spectator'},
                    guidance='Ensure League client is running with active match'
                )
        
        return self._error_result(
            'League integration is spectator-only (no command execution)',
            metadata={'mode': 'spectator'},
            guidance='League only supports passive data observation'
        )
    
    def _get_all_game_data(self) -> Optional[Dict[str, Any]]:
        """Retrieve complete game data from Live Client API with caching"""
        current_time = time.time()
        
        # Use cache if fresh
        if self.cached_data and (current_time - self.cache_timestamp) < self.cache_duration:
            return self.cached_data
        
        try:
            response = requests.get(
                f"{self.api_base}/liveclientdata/allgamedata",
                verify=False,
                timeout=self.timeout
            )
            
            if response.status_code == 200:
                data = response.json()
                self.cached_data = data
                self.cache_timestamp = current_time
                return data
            
            return None
                
        except requests.exceptions.RequestException as e:
            if self._logger:
                self._logger.warning(f"[League] API request failed: {e}")
            return None
    
    def _format_game_context(self, game_data: Dict[str, Any], analysis: Dict[str, Any]) -> str:
        """Format game data into readable context string"""
        lines = ["## [LoL] LEAGUE OF LEGENDS - LIVE MATCH DATA"]
        
        # Add threat warning if critical
        if analysis.get('threat_level') >= 7:
            lines.append("[!] CRITICAL SITUATION DETECTED")
            if analysis.get('threats'):
                lines.append(f"Threats: {', '.join(analysis['threats'])}")
            lines.append("")
        
        # Game time
        game_time = game_data.get('gameData', {}).get('gameTime', 0)
        minutes = int(game_time // 60)
        seconds = int(game_time % 60)
        lines.append(f"**Match Time:** {minutes:02d}:{seconds:02d}")
        
        # Active player stats
        active_player = game_data.get('activePlayer', {})
        all_players = game_data.get('allPlayers', [])
        
        # Find active champion name
        active_champ_name = "Unknown"
        active_summoner = active_player.get('summonerName', '')
        
        for player in all_players:
            if player.get('summonerName') == active_summoner:
                active_champ_name = player.get('championName', 'Unknown')
                break
        
        if active_player:
            lines.append(f"\n### YOUR CHAMPION: {active_champ_name}")
            
            stats = active_player.get('championStats', {})
            level = stats.get('level', 0)
            current_hp = stats.get('currentHealth', 0)
            max_hp = stats.get('maxHealth', 1)
            current_mana = stats.get('resourceValue', 0)
            max_mana = stats.get('resourceMax', 1)
            
            hp_pct = (current_hp / max_hp * 100) if max_hp > 0 else 0
            mana_pct = (current_mana / max_mana * 100) if max_mana > 0 else 0
            
            lines.append(f"**Level:** {level}")
            
            # Highlight low health
            if hp_pct <= 30:
                lines.append(f"**Health:** [!] {current_hp:.0f}/{max_hp:.0f} HP ({hp_pct:.0f}%) - DANGER")
            else:
                lines.append(f"**Health:** {current_hp:.0f}/{max_hp:.0f} HP ({hp_pct:.0f}%)")
            
            # Highlight low mana
            if mana_pct <= 20:
                lines.append(f"**Mana/Energy:** [!] {current_mana:.0f}/{max_mana:.0f} ({mana_pct:.0f}%) - LOW")
            else:
                lines.append(f"**Mana/Energy:** {current_mana:.0f}/{max_mana:.0f} ({mana_pct:.0f}%)")
            
            lines.append(f"**Gold:** {active_player.get('currentGold', 0):.0f}g")
            
            # KDA
            kills = stats.get('kills', 0)
            deaths = stats.get('deaths', 0)
            assists = stats.get('assists', 0)
            cs = stats.get('creepScore', 0)
            lines.append(f"**KDA:** {kills}/{deaths}/{assists}")
            lines.append(f"**CS:** {cs}")
            
            # Combat stats
            lines.append(f"**Attack Damage:** {stats.get('attackDamage', 0):.0f}")
            lines.append(f"**Ability Power:** {stats.get('abilityPower', 0):.0f}")
            lines.append(f"**Armor:** {stats.get('armor', 0):.0f} | **Magic Resist:** {stats.get('magicResist', 0):.0f}")
        
        # Team scores
        if all_players:
            blue_team = [p for p in all_players if p.get('team') == 'ORDER']
            red_team = [p for p in all_players if p.get('team') == 'CHAOS']
            
            blue_kills = sum(p.get('scores', {}).get('kills', 0) for p in blue_team)
            red_kills = sum(p.get('scores', {}).get('kills', 0) for p in red_team)
            
            lines.append(f"\n### TEAM SCORE")
            lines.append(f"**Blue Team:** {blue_kills} kills")
            lines.append(f"**Red Team:** {red_kills} kills")
        
        # Recent events (last 5)
        events = game_data.get('events', {}).get('Events', [])
        if events:
            recent_events = events[-5:]
            lines.append(f"\n### RECENT EVENTS ({len(recent_events)} latest)")
            for event in recent_events:
                event_time = event.get('EventTime', 0)
                event_min = int(event_time // 60)
                event_sec = int(event_time % 60)
                event_desc = self.threat_detector._format_event(event)
                lines.append(f"- [{event_min:02d}:{event_sec:02d}] {event_desc}")
        
        # Situation assessment
        lines.append(f"\n### SITUATION ASSESSMENT")
        if analysis.get('threat_level') >= 7:
            lines.append(f"**Threat Level:** {analysis['threat_level']}/10 - CRITICAL")
            lines.append("**Recommendation:** Play safe, avoid fights")
        elif analysis.get('threat_level') >= 4:
            lines.append(f"**Threat Level:** {analysis['threat_level']}/10 - Elevated")
        else:
            lines.append(f"**Threat Level:** {analysis['threat_level']}/10 - Normal")
        
        return '\n'.join(lines)