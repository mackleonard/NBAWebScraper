import { useState, useEffect } from "react";

// API URL detection
const API_URL =
  window.location.hostname === "localhost" || window.location.hostname === "127.0.0.1"
    ? "http://localhost:8000"
    : "/api";

console.log("Using API_URL:", API_URL);

export default function App() {
  const [player, setPlayer] = useState("");
  const [inputValue, setInputValue] = useState("");

  // Data states
  const [careerSummary, setCareerSummary] = useState(null);
  const [detailedStats, setDetailedStats] = useState([]);
  const [projections, setProjections] = useState(null);
  const [gameLogs, setGameLogs] = useState([]);
  const [advancedStats, setAdvancedStats] = useState(null);
  const [popularPlayers, setPopularPlayers] = useState([]);
  const [dbStats, setDbStats] = useState(null);
  
  // Rankings & Compare
  const [compareList, setCompareList] = useState([]);
  const [comparisonData, setComparisonData] = useState(null);
  const [rankings, setRankings] = useState([]);
  const [selectedSeason, setSelectedSeason] = useState("2025-26");
  const [selectedPosition, setSelectedPosition] = useState("ALL");
  const [compareSearchInput, setCompareSearchInput] = useState("");
  const [loadingRankings, setLoadingRankings] = useState(false);
  const [loadingComparison, setLoadingComparison] = useState(false);

  // Fantasy Settings (NEW)
  const [fantasySettings, setFantasySettings] = useState(null);
  const [showSettings, setShowSettings] = useState(false);
  const [settingsForm, setSettingsForm] = useState({});
  const [userId] = useState(() => {
    let id = localStorage.getItem('nba_user_id');
    if (!id) {
      id = 'user_' + Math.random().toString(36).substr(2, 9);
      localStorage.setItem('nba_user_id', id);
    }
    return id;
  });

  // UI states
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [viewMode, setViewMode] = useState("projections"); // projections | detailed | simple | logs | rankings | compare | standings | draft

  // Mock Draft states
  const [draftConfig, setDraftConfig] = useState({
    numTeams: 12,
    rounds: 15,
    draftType: 'snake'
  });
  const [draftResults, setDraftResults] = useState(null);
  const [draftingNow, setDraftingNow] = useState(false);
  const [availablePlayers, setAvailablePlayers] = useState([]);
  const [draftedPlayers, setDraftedPlayers] = useState([]);

  useEffect(() => {
  // Fetch fantasy settings
  fetch(`${API_URL}/fantasy/settings?user_id=${userId}`)
    .then(r => r.json())
    .then(data => {
      setFantasySettings(data);
      setSettingsForm(data);
    })
    .catch(console.error);
    
  // ... existing popular players fetch ...
}, []);

  // ── On mount: popular players + db ribbon ──
  useEffect(() => {
  // Fetch fantasy settings
  fetch(`${API_URL}/fantasy/settings?user_id=${userId}`)
    .then((r) => r.json())
    .then(data => {
      setFantasySettings(data);
      setSettingsForm(data);
    })
    .catch(console.error);
  
  fetch(`${API_URL}/analytics/popular-players?limit=5`)
    .then((r) => r.json())
    .then(setPopularPlayers)
    .catch(() => {});
  fetch(`${API_URL}/db/stats`)
    .then((r) => r.json())
    .then(setDbStats)
    .catch(() => {});
}, [userId]);

  // ── Master fetch when player changes ──
  useEffect(() => {
    if (!player) return;
    let cancelled = false;
    setLoading(true);
    setError(null);
    setCareerSummary(null);
    setDetailedStats([]);
    setProjections(null);
    setGameLogs([]);
    setAdvancedStats(null);

    async function fetchAll() {
      try {
        const [sumRes, detRes, projRes, logsRes, advRes] = await Promise.all([
          fetch(`${API_URL}/player/career-summary?player=${encodeURIComponent(player)}&user_id=${userId}`),
          fetch(`${API_URL}/player/detailed-stats?player=${encodeURIComponent(player)}&user_id=${userId}`),
          fetch(`${API_URL}/projections/all?player=${encodeURIComponent(player)}&season=2025-26&user_id=${userId}`),
          fetch(`${API_URL}/player/game-logs?player=${encodeURIComponent(player)}&season=${selectedSeason}&last_n=15&user_id=${userId}`),
          fetch(`${API_URL}/player/season-advanced?player=${encodeURIComponent(player)}&season=${selectedSeason}&user_id=${userId}`)
        ]);

        if (!sumRes.ok) {
          const err = await sumRes.json().catch(() => ({}));
          throw new Error("Player not found. Please check your spelling and search again.");
        }

        if (!cancelled) {
          setCareerSummary(await sumRes.json());
          if (detRes.ok) setDetailedStats(await detRes.json());
          if (projRes.ok) setProjections(await projRes.json());
          
          // Log status of new endpoints
          console.log("Game logs status:", logsRes.status);
          console.log("Advanced stats status:", advRes.status);
          
          if (logsRes.ok) {
            const logs = await logsRes.json();
            console.log("Game logs data:", logs);
            setGameLogs(logs);
          } else {
            console.error("Game logs failed:", await logsRes.text());
          }
          
          if (advRes.ok) {
            const adv = await advRes.json();
            console.log("Advanced stats data:", adv);
            setAdvancedStats(adv);
          } else {
            console.error("Advanced stats failed:", await advRes.text());
          }
        }
      } catch (e) {
        if (!cancelled) {
          if (e.message.includes("Failed to fetch"))
            setError(`Cannot connect to backend at ${API_URL}. Make sure the backend is running.`);
          else setError(e.message);
        }
      } finally {
        if (!cancelled) setLoading(false);
      }
    }

    fetchAll();
    return () => { cancelled = true; };
  }, [player]);

  useEffect(() => {
    if (!player || viewMode !== "logs") return;
    
    async function fetchLogs() {
      try {
        const [logsRes, advRes] = await Promise.all([
        fetch(`${API_URL}/player/game-logs?player=${encodeURIComponent(player)}&season=${selectedSeason}&last_n=15&user_id=${userId}`),
        fetch(`${API_URL}/player/season-advanced?player=${encodeURIComponent(player)}&season=${selectedSeason}&user_id=${userId}`),
      ]);

        if (logsRes.ok) {
          const logs = await logsRes.json();
          setGameLogs(logs);
        } else {
          console.error("Game logs failed:", await logsRes.text());
          setGameLogs([]);
        }
        
        if (advRes.ok) {
          const adv = await advRes.json();
          setAdvancedStats(adv);
        } else {
          console.error("Advanced stats failed:", await advRes.text());
          setAdvancedStats(null);
        }
      } catch (e) {
        console.error("Error fetching logs:", e);
      }
    }

    fetchLogs();
  }, [player, selectedSeason, viewMode]);

  useEffect(() => {
    if (viewMode === "rankings") {
      runRankings();
    }
  }, [selectedPosition, viewMode]);

  // Auto-fetch rankings when entering standings view
  useEffect(() => {
    if (viewMode === "standings" && rankings.length === 0 && !loadingRankings) {
      runRankings();
    }
  }, [viewMode, selectedPosition, selectedSeason]);

  const handleSubmit = () => {
    if (inputValue.trim()) {
      setPlayer(inputValue.trim());
      // Add to compare list if not already there
      if (!compareList.includes(inputValue.trim())) {
        setCompareList(prev => [...prev, inputValue.trim()].slice(-5)); // Keep last 5
      }
    }
  };

  const saveFantasySettings = async () => {
  try {
    console.log('💾 Saving settings for user:', userId);
    console.log('📊 New settings:', settingsForm);
    
    const res = await fetch(`${API_URL}/fantasy/settings?user_id=${userId}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(settingsForm)
    });
    
    if (res.ok) {
      const updated = await res.json();
      console.log('✅ Settings saved:', updated);
      setFantasySettings(updated);
      setShowSettings(false);
      
      // AGGRESSIVE STATE CLEARING
      console.log('🗑️ Clearing all cached state...');
      setCareerSummary(null);
      setDetailedStats([]);
      setProjections(null);
      setGameLogs([]);
      setAdvancedStats(null);
      setRankings([]);
      setComparisonData(null);
      
      // Force page reload (nuclear option but guaranteed to work)
      alert('Settings saved! Page will reload with new scoring.');
      window.location.reload();
      
    } else {
      const error = await res.json();
      console.error('❌ Save failed:', error);
      alert('Failed to save: ' + (error.detail || 'Unknown error'));
    }
  } catch (e) {
    console.error('💥 Error:', e);
    alert('Error saving settings. Check console.');
  }
};

const loadPreset = async (presetName) => {
  try {
    const res = await fetch(`${API_URL}/fantasy/settings/presets`);
    const presets = await res.json();
    if (presets[presetName]) {
      setSettingsForm({ ...settingsForm, ...presets[presetName] });
    }
  } catch (e) {
    console.error('Failed to load preset:', e);
  }
};

  const addToCompare = (name) => {
    if (!compareList.includes(name)) {
      setCompareList(prev => [...prev, name].slice(-5));
    }
  };

  const removeFromCompare = (name) => {
    setCompareList(prev => prev.filter(p => p !== name));
  };

  const runComparison = async () => {
    if (compareList.length < 2) return;
    setLoadingComparison(true);
    try {
      const res = await fetch(`${API_URL}/compare?season=2025-26&user_id=${userId}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ players: compareList })
      });
      if (res.ok) {
        setComparisonData(await res.json());
      }
    } catch (e) {
      console.error("Comparison failed:", e);
    } finally {
      setLoadingComparison(false);
    }
  };

  const runRankings = async () => {
    setLoadingRankings(true);
    try {
      const posParam = selectedPosition === "ALL" ? "" : selectedPosition;
      const res = await fetch(`${API_URL}/rankings/top?position=${posParam}&limit=10&season=2025-26&user_id=${userId}`);
      if (res.ok) {
        const data = await res.json();
        setRankings(data.rankings || []);
      }
    } catch (e) {
      console.error("Rankings failed:", e);
    } finally {
      setLoadingRankings(false);
    }
  };

  const startMockDraft = async () => {
    setDraftingNow(true);
    try {
      const res = await fetch(`${API_URL}/rankings/top?limit=200&season=${selectedSeason}&user_id=${userId}`);
      if (!res.ok) throw new Error('Failed to load players');
      
      const data = await res.json();
      setAvailablePlayers(data.rankings);
      setDraftedPlayers([]);
      setDraftResults({
        teams: Array.from({ length: draftConfig.numTeams }, (_, i) => ({
          teamNumber: i + 1,
          picks: []
        })),
        currentPick: 1,
        currentRound: 1,
        totalPicks: draftConfig.numTeams * draftConfig.rounds
      });
    } catch (e) {
      console.error('Failed to start draft:', e);
      alert('Failed to load players for draft');
      setDraftingNow(false);
    }
  };

  const makeDraftPick = (player) => {
    if (!draftResults) return;
    
    const currentPickNum = draftResults.currentPick;
    const round = draftResults.currentRound;
    const { numTeams } = draftConfig;
    
    let teamIndex;
    if (draftConfig.draftType === 'snake') {
      const pickInRound = ((currentPickNum - 1) % numTeams) + 1;
      teamIndex = round % 2 === 1 
        ? pickInRound - 1
        : numTeams - pickInRound;
    } else {
      teamIndex = ((currentPickNum - 1) % numTeams);
    }
    
    const newTeams = [...draftResults.teams];
    newTeams[teamIndex].picks.push({
      ...player,
      round,
      pickNumber: currentPickNum,
      overallRank: player.rank
    });
    
    setAvailablePlayers(availablePlayers.filter(p => p.player !== player.player));
    setDraftedPlayers([...draftedPlayers, player]);
    
    const nextPick = currentPickNum + 1;
    const nextRound = Math.ceil(nextPick / numTeams);
    
    setDraftResults({
      teams: newTeams,
      currentPick: nextPick,
      currentRound: nextRound,
      totalPicks: draftConfig.numTeams * draftConfig.rounds
    });
  };

  const resetDraft = () => {
    setDraftResults(null);
    setDraftingNow(false);
    setAvailablePlayers([]);
    setDraftedPlayers([]);
  };

  const maxFantasyPoints = Math.max(...detailedStats.map((r) => r.fantasy_points), 0);

  // ── RENDER ──
  return (
    <div className="min-h-screen bg-zinc-50 font-mono">
      <div className="max-w-7xl mx-auto px-4 md:px-8 py-10 md:py-16">

        {/* ── HEADER ── */}
        <div className="mb-10 border-8 border-black p-6 md:p-8 bg-white relative">
          <div className="absolute -top-4 -right-4 w-20 h-20 bg-orange-500 border-4 border-black"></div>
          <h1 className="text-5xl md:text-7xl font-black uppercase tracking-tighter mb-2">
            NBA<br />ANALYTICS
          </h1>
          <div className="w-32 h-2 bg-black"></div>
        </div>

        <button
          onClick={() => setShowSettings(!showSettings)}
          className="absolute top-6 right-6 px-4 py-2 border-4 border-black bg-purple-500 
                    font-black uppercase text-white hover:bg-purple-400
                    shadow-[4px_4px_0px_0px_rgba(0,0,0,1)]"
        >
          ⚙️ Fantasy Settings
        </button>

        {/* Fantasy Settings Modal */}
        {showSettings && (
          <div className="fixed inset-0 bg-black bg-opacity-50 z-50 flex items-center justify-center p-4">
            <div className="border-8 border-black bg-white max-w-4xl w-full max-h-[90vh] overflow-auto">
              <div className="border-b-4 border-black p-4 bg-purple-500 sticky top-0 z-10">
                <h2 className="font-black uppercase text-white text-2xl">Fantasy Scoring Settings</h2>
              </div>
              
              <div className="p-6 space-y-6">
                
                {/* Presets */}
                <div>
                  <label className="font-black uppercase text-sm block mb-2">Quick Presets:</label>
                  <div className="flex gap-2 flex-wrap">
                    {['standard', 'points_heavy', 'balanced', 'category_based'].map(preset => (
                      <button
                        key={preset}
                        onClick={() => loadPreset(preset)}
                        className="px-4 py-2 border-2 border-black bg-zinc-100 font-bold uppercase text-sm
                                  hover:bg-yellow-100"
                      >
                        {preset.replace('_', ' ')}
                      </button>
                    ))}
                  </div>
                </div>

                {/* Settings Name */}
                <div>
                  <label className="font-black uppercase text-sm block mb-2">Settings Name:</label>
                  <input
                    type="text"
                    value={settingsForm.name || ''}
                    onChange={(e) => setSettingsForm({...settingsForm, name: e.target.value})}
                    className="w-full border-4 border-black px-4 py-2 font-bold"
                    placeholder="My League Settings"
                  />
                </div>

                {/* Core Stats */}
                <div>
                  <div className="font-black uppercase text-lg mb-3 text-orange-600">Core Stats</div>
                  <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                    {[
                      {key: 'points', label: 'Points', default: 1.0},
                      {key: 'rebounds', label: 'Rebounds', default: 1.0},
                      {key: 'assists', label: 'Assists', default: 1.5},
                      {key: 'steals', label: 'Steals', default: 2.0},
                      {key: 'blocks', label: 'Blocks', default: 2.0},
                      {key: 'turnovers', label: 'Turnovers', default: -2.0},
                      {key: 'three_pointers', label: '3-Pointers', default: 1.0},
                      {key: 'offensive_rebounds', label: 'Off. Rebounds', default: 0.5}
                    ].map(stat => (
                      <div key={stat.key} className="border-2 border-black p-3 bg-zinc-50">
                        <label className="font-bold text-xs uppercase block mb-1">{stat.label}</label>
                        <input
                          type="number"
                          step="0.1"
                          value={settingsForm[stat.key] ?? stat.default}
                          onChange={(e) => setSettingsForm({...settingsForm, [stat.key]: parseFloat(e.target.value) || 0})}
                          className="w-full border-2 border-black px-2 py-1 font-bold text-center"
                        />
                      </div>
                    ))}
                  </div>
                </div>

                {/* Advanced Stats */}
                <div>
                  <div className="font-black uppercase text-lg mb-3 text-blue-600">Advanced (Optional)</div>
                  <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
                    {[
                      {key: 'field_goals_made', label: 'FG Made', default: 0.0},
                      {key: 'field_goals_missed', label: 'FG Missed', default: 0.0},
                      {key: 'free_throws_made', label: 'FT Made', default: 0.0},
                      {key: 'free_throws_missed', label: 'FT Missed', default: 0.0},
                      {key: 'double_double', label: 'Double-Double', default: 0.0},
                      {key: 'triple_double', label: 'Triple-Double', default: 0.0}
                    ].map(stat => (
                      <div key={stat.key} className="border-2 border-black p-3 bg-zinc-50">
                        <label className="font-bold text-xs uppercase block mb-1">{stat.label}</label>
                        <input
                          type="number"
                          step="0.5"
                          value={settingsForm[stat.key] ?? stat.default}
                          onChange={(e) => setSettingsForm({...settingsForm, [stat.key]: parseFloat(e.target.value) || 0})}
                          className="w-full border-2 border-black px-2 py-1 font-bold text-center"
                        />
                      </div>
                    ))}
                  </div>
                </div>

                {/* Actions */}
                <div className="flex gap-4 justify-end pt-4 border-t-4 border-black">
                  <button
                    onClick={() => setShowSettings(false)}
                    className="px-6 py-3 border-4 border-black bg-zinc-300 font-black uppercase"
                  >
                    Cancel
                  </button>
                  <button
                    onClick={saveFantasySettings}
                    className="px-6 py-3 border-4 border-black bg-purple-500 font-black uppercase text-white
                              hover:bg-purple-400 shadow-[4px_4px_0px_0px_rgba(0,0,0,1)]"
                  >
                    Save Settings
                  </button>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* ── SEARCH ── */}
        <div className="mb-8 border-4 border-black bg-white">
          <div className="border-b-4 border-black p-4 bg-zinc-900 text-white">
            <p className="font-bold uppercase text-sm tracking-wider">Search Player</p>
          </div>
          <div className="p-6">
            <div className="flex gap-4">
              <input
                className="flex-1 border-4 border-black px-4 py-3 text-lg font-bold uppercase
                           focus:outline-none focus:bg-yellow-100 transition-colors"
                value={inputValue}
                onChange={(e) => setInputValue(e.target.value)}
                onKeyDown={(e) => e.key === "Enter" && handleSubmit()}
                placeholder="PLAYER NAME"
                disabled={loading}
              />
              <button
                onClick={handleSubmit}
                disabled={loading}
                className="px-8 py-3 border-4 border-black bg-orange-500 font-black uppercase
                           hover:bg-orange-400 active:translate-x-1 active:translate-y-1
                           disabled:bg-zinc-300 transition-all
                           shadow-[4px_4px_0px_0px_rgba(0,0,0,1)]
                           hover:shadow-[2px_2px_0px_0px_rgba(0,0,0,1)] active:shadow-none"
              >
                {loading ? "WAIT" : "GO"}
              </button>
            </div>

            {/* Popular quick-select */}
            {popularPlayers.length > 0 && (
              <div className="mt-4 flex flex-wrap gap-2">
                <div className="text-sm font-bold uppercase">Recent Searches: </div>
                {popularPlayers.map((p) => (
                  <button
                    key={p.nba_id}
                    onClick={() => { setInputValue(p.player_name); setPlayer(p.player_name); }}
                    className="border-2 border-black bg-zinc-100 px-3 py-1 text-xs font-black uppercase
                               hover:bg-yellow-100 transition-colors"
                  >
                    {p.player_name} <span className="text-zinc-500"></span>
                  </button>
                ))}
              </div>
            )}
          </div>
        </div>

        {/* ── LOADING ── */}
        {loading && (
          <div className="border-4 border-black bg-white p-12 text-center mb-8">
            <div className="inline-block border-4 border-black p-4 bg-yellow-100">
              <p className="font-black uppercase text-lg">LOADING DATA...</p>
            </div>
          </div>
        )}

        {/* ── ERROR ── */}
        {error && (
          <div className="border-4 border-black bg-red-500 p-6 mb-8">
            <p className="font-black uppercase text-white">[ERROR] {error}</p>
          </div>
        )}

        {/* ── CAREER SUMMARY CARDS ── */}
        {careerSummary && !loading && (
          <div className="mb-8">
            <div className="border-4 border-black bg-zinc-900 text-white p-4 mb-4">
              <h2 className="font-black uppercase text-xl">CAREER SUMMARY</h2>
            </div>

            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <div className="border-4 border-black bg-white p-6 relative overflow-hidden">
                <div className="absolute top-0 right-0 w-24 h-24 bg-purple-500 -mr-12 -mt-12 rotate-45"></div>
                <p className="font-black text-sm mb-2 uppercase">Seasons</p>
                <p className="text-5xl font-black">{careerSummary.seasons_played}</p>
                <div className="w-full h-2 bg-black mt-4"></div>
              </div>

              <div className="border-4 border-black bg-white p-6 relative overflow-hidden">
                <div className="absolute top-0 right-0 w-24 h-24 bg-orange-500 -mr-12 -mt-12 rotate-45"></div>
                <p className="font-black text-sm mb-2 uppercase">Points</p>
                <p className="text-5xl font-black">{careerSummary.career_totals.points.toLocaleString()}</p>
                <div className="w-full h-2 bg-black mt-4"></div>
                <p className="text-sm font-bold mt-2">{careerSummary.career_averages.ppg} PPG</p>
              </div>

              <div className="border-4 border-black bg-white p-6 relative overflow-hidden">
                <div className="absolute top-0 right-0 w-24 h-24 bg-blue-500 -mr-12 -mt-12 rotate-45"></div>
                <p className="font-black text-sm mb-2 uppercase">Rebounds</p>
                <p className="text-5xl font-black">{careerSummary.career_totals.rebounds.toLocaleString()}</p>
                <div className="w-full h-2 bg-black mt-4"></div>
                <p className="text-sm font-bold mt-2">{careerSummary.career_averages.rpg} RPG</p>
              </div>

              <div className="border-4 border-black bg-white p-6 relative overflow-hidden">
                <div className="absolute top-0 right-0 w-24 h-24 bg-green-500 -mr-12 -mt-12 rotate-45"></div>
                <p className="font-black text-sm mb-2 uppercase">Assists</p>
                <p className="text-5xl font-black">{careerSummary.career_totals.assists.toLocaleString()}</p>
                <div className="w-full h-2 bg-black mt-4"></div>
                <p className="text-sm font-bold mt-2">{careerSummary.career_averages.apg} APG</p>
              </div>
            </div>
          </div>
        )}

        {/* ── GLOBAL NAVIGATION (No Player Required) ── */}
        {!player && (
          <div className="mb-8 border-4 border-black bg-white p-4">
            <div className="flex gap-3 flex-wrap">
              <div className="px-3 py-2 border-2 border-black bg-zinc-200 font-black text-xs uppercase">
                EXPLORE:
              </div>
              {[
                { id: "standings", label: "STANDINGS", active: "bg-orange-500", hover: "hover:bg-orange-400" },
                { id: "draft", label: "MOCK DRAFT", active: "bg-purple-500", hover: "hover:bg-purple-400" }
              ].map((tab) => (
                <button
                  key={tab.id}
                  onClick={() => setViewMode(tab.id)}
                  className={`px-5 py-2 border-4 border-black font-black uppercase transition-all text-sm
                              shadow-[4px_4px_0px_0px_rgba(0,0,0,1)]
                              hover:shadow-[2px_2px_0px_0px_rgba(0,0,0,1)]
                              active:shadow-none active:translate-x-1 active:translate-y-1
                              ${viewMode === tab.id ? `${tab.active} text-white` : `bg-white ${tab.hover}`}`}
                >
                  {tab.label}
                </button>
              ))}
            </div>
          </div>
        )}

        {/* ── VIEW MODE TOGGLE ── */}
        {detailedStats.length > 0 && !loading && (
          <div className="mb-8 flex gap-3 flex-wrap">
            {[
              { id: "detailed",    label: "[STATS]", active: "bg-orange-500", hover: "hover:bg-orange-400" },
              { id: "simple",      label: "[FANTASY]", active: "bg-blue-500",   hover: "hover:bg-blue-400" },
              { id: "logs",        label: "[GAME LOGS]", active: "bg-green-500",  hover: "hover:bg-green-400" },
              { id: "rankings",    label: "[RANKINGS]", active: "bg-pink-500",   hover: "hover:bg-pink-400" },
              { id: "compare",     label: "[COMPARE]", active: "bg-cyan-500",   hover: "hover:bg-cyan-400" },
              { id: "projections", label: "[PROJECTIONS]", active: "bg-purple-500", hover: "hover:bg-purple-400" }
            ].map((tab) => (
              <button
                key={tab.id}
                onClick={() => setViewMode(tab.id)}
                className={`px-5 py-2 border-4 border-black font-black uppercase transition-all text-sm
                            shadow-[4px_4px_0px_0px_rgba(0,0,0,1)]
                            hover:shadow-[2px_2px_0px_0px_rgba(0,0,0,1)]
                            active:shadow-none active:translate-x-1 active:translate-y-1
                            ${viewMode === tab.id ? `${tab.active} text-white` : `bg-white ${tab.hover}`}`}
              >
                {tab.label}
              </button>
            ))}
          </div>
        )}

        {/* ═══════════════════════════════════════════════════════════════════════
            PROJECTIONS VIEW
            ═══════════════════════════════════════════════════════════════════════ */}
        {!loading && viewMode === "projections" && projections && (
          <div className="space-y-8">
            {/* Next Game */}
            {projections.next_game ? (
              <div className="border-4 border-black bg-white">
                <div className="border-b-4 border-black p-4 bg-purple-500">
                  <h2 className="font-black uppercase text-white text-xl flex items-center gap-3">
                    [NEXT GAME PROJECTION]
                    {projections.next_game.games_analyzed && (
                      <span className="text-sm font-normal">(Games Analyzed for projection: {projections.next_game.games_analyzed} GAMES)</span>
                    )}
                  </h2>
                </div>

                <div className="p-6 md:p-8">
                  {projections.next_game.recent_performance?.trend && (
                    <div className="mb-6 border-4 border-black p-4 inline-block">
                      <span className="font-black uppercase mr-4">TREND:</span>
                      <span className={`font-black uppercase ${
                        projections.next_game.recent_performance.trend === "trending_up"   ? "text-green-600" :
                        projections.next_game.recent_performance.trend === "trending_down" ? "text-red-600"   : "text-black"
                      }`}>
                        {projections.next_game.recent_performance.trend === "trending_up"   && "[↑ UP]"}
                        {projections.next_game.recent_performance.trend === "trending_down" && "[↓ DOWN]"}
                        {projections.next_game.recent_performance.trend === "stable"        && "[→ STABLE]"}
                      </span>
                    </div>
                  )}

                  {projections.next_game.projected_stats && (
                    <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
                      {Object.entries(projections.next_game.projected_stats).map(([stat, value]) => (
                        <div key={stat} className="border-2 border-black p-4 bg-zinc-100">
                          <div className="text-xs uppercase font-black mb-2">{stat.replace(/_/g, " ").replace("three pointers made", "3PM")} (Projected)</div>
                          <div className="text-4xl font-black">{value}</div>
                          
                        </div>
                      ))}
                    </div>
                  )}

                  <div className="border-4 border-black bg-yellow-400 p-6">
                    <div className="flex items-center justify-between">
                      <span className="font-black text-lg uppercase">Fantasy Points</span>
                      <span className="text-5xl font-black">{projections.next_game.projected_fantasy_points}</span>
                    </div>
                  </div>
                </div>
              </div>
            ) : (
              <div className="border-4 border-black bg-zinc-100 p-6">
                <p className="font-black uppercase">[!] NEXT GAME UNAVAILABLE</p>
                <p className="text-sm mt-2 uppercase">No 2025-26 game log data yet.</p>
              </div>
            )}

            {/* Season Projections */}
            {projections.season_projections && (
              <div className="border-4 border-black bg-white">
                <div className="border-b-4 border-black p-4 bg-zinc-900">
                  <h2 className="font-black uppercase text-white text-xl">[SEASON PROJECTIONS / 2025-26]</h2>
                </div>

                <div className="p-6 md:p-8 space-y-6">
                  {Object.entries(projections.season_projections).map(([method, data]) => {
                    if (!data) return null;
                    return (
                      <div key={method} className="border-2 border-black p-6 bg-zinc-50">
                        <h3 className="text-xl font-black mb-4 uppercase flex items-center gap-2">
                          [{method.replace(/_/g, " ").replace("recent seasons", "last 3 seasons average")}]
                          {data.adjustment_factor && (
                            <span className="text-sm font-normal text-zinc-500">
                              (ADJ: {(data.adjustment_factor * 100).toFixed(0)}%)
                            </span>
                          )}
                        </h3>

                        {data.projected_per_game && (
                          <div className="grid grid-cols-3 md:grid-cols-6 gap-2 mb-4">
                            {Object.entries(data.projected_per_game).map(([stat, value]) => (
                              <div key={stat} className="text-center border border-black p-2 bg-white">
                                <div className="text-xs uppercase font-bold mb-1">
                                  {stat.replace(/_/g, " ").replace("three pointers", "3PM")} Per Game
                                </div>
                                <div className="text-xl font-black">{value}</div>
                              </div>
                            ))}
                          </div>
                        )}

                        <div className="grid grid-cols-2 gap-4">
                          <div className="border-2 border-black p-4 bg-white">
                            <div className="text-xs uppercase font-black mb-1">Fantasy Points Per Game</div>
                            <div className="text-3xl font-black">{data.projected_fantasy_points_per_game}</div>
                          </div>
                          <div className="border-2 border-black p-4 bg-white">
                            <div className="text-xs uppercase font-black mb-1">Season Total Fantasy Points</div>
                            <div className="text-3xl font-black">{data.projected_fantasy_points_season}</div>
                          </div>
                        </div>
                      </div>
                    );
                  })}
                </div>
              </div>
            )}
          </div>
        )}

        {/* ═══════════════════════════════════════════════════════════════════════
            DETAILED STATS VIEW
            ═══════════════════════════════════════════════════════════════════════ */}
        {detailedStats.length > 0 && !loading && viewMode === "detailed" && (
          <div className="border-4 border-black bg-white">
            <div className="border-b-4 border-black p-4 bg-zinc-900">
              <h2 className="font-black uppercase text-white text-xl">
                {player.toUpperCase()} / CAREER DATA
              </h2>
            </div>

            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b-4 border-black bg-zinc-100">
                    {["Season","GP","MPG","PPG","RPG","APG","SPG","BPG","FG%","3P%","FPPG"].map((h) => (
                      <th key={h} className="p-3 font-black uppercase border-r-2 border-black last:border-r-0 text-right first:text-left">
                        {h}
                      </th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {detailedStats.map((r, idx) => {
                    const isTop = r.fantasy_points === maxFantasyPoints;
                    return (
                      <tr
                        key={idx}
                        className={`border-b-2 border-black hover:bg-yellow-100 transition-colors ${idx % 2 === 0 ? "bg-white" : "bg-zinc-50"}`}
                      >
                        <td className="p-3 font-black uppercase border-r-2 border-black">
                          {isTop && <span className="text-orange-500">[★] </span>}
                          {r.season}
                        </td>
                        <td className="p-3 text-right font-bold border-r-2 border-black">{r.games_played}</td>
                        <td className="p-3 text-right font-bold border-r-2 border-black">{r.mpg}</td>
                        <td className="p-3 text-right font-bold border-r-2 border-black">{r.ppg}</td>
                        <td className="p-3 text-right font-bold border-r-2 border-black">{r.rpg}</td>
                        <td className="p-3 text-right font-bold border-r-2 border-black">{r.apg}</td>
                        <td className="p-3 text-right font-bold border-r-2 border-black">{r.spg}</td>
                        <td className="p-3 text-right font-bold border-r-2 border-black">{r.bpg}</td>
                        <td className="p-3 text-right font-bold border-r-2 border-black">{r.fg_pct}%</td>
                        <td className="p-3 text-right font-bold border-r-2 border-black">{r.three_pt_pct}%</td>
                        <td className="p-3 text-right">
                          <span className={`font-black text-lg ${isTop ? "text-orange-500" : ""}`}>{r.fantasy_ppg}</span>
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          </div>
        )}

        {/* ═══════════════════════════════════════════════════════════════════════
            FANTASY BAR-CHART VIEW
            ═══════════════════════════════════════════════════════════════════════ */}
        {detailedStats.length > 0 && !loading && viewMode === "simple" && (
          <div className="border-4 border-black bg-white">
            <div className="border-b-4 border-black p-4 bg-zinc-900">
              <h2 className="font-black uppercase text-white text-xl">
                {player.toUpperCase()} / FANTASY POINTS
              </h2>
            </div>

            <table className="w-full">
              <thead>
                <tr className="border-b-4 border-black bg-zinc-100">
                  <th className="text-left p-4 font-black uppercase border-r-4 border-black">Season</th>
                  <th className="text-right p-4 font-black uppercase border-r-4 border-black">Total</th>
                  <th className="text-right p-4 font-black uppercase border-r-4 border-black">Per Game</th>
                  <th className="text-left p-4 font-black uppercase">Performance</th>
                </tr>
              </thead>
              <tbody>
                {detailedStats.map((r, idx) => {
                  const pct = (r.fantasy_points / maxFantasyPoints) * 100;
                  const isTop = r.fantasy_points === maxFantasyPoints;
                  return (
                    <tr
                      key={idx}
                      className={`border-b-2 border-black hover:bg-yellow-100 transition-colors ${idx % 2 === 0 ? "bg-white" : "bg-zinc-50"}`}
                    >
                      <td className="p-4 font-black uppercase border-r-2 border-black">
                        {isTop && <span className="text-orange-500">[★] </span>}
                        {r.season}
                      </td>
                      <td className="p-4 text-right font-black text-2xl border-r-2 border-black">
                        {r.fantasy_points.toLocaleString(undefined, { maximumFractionDigits: 1 })}
                      </td>
                      <td className="p-4 text-right font-black text-lg border-r-2 border-black">
                        {r.fantasy_ppg}
                      </td>
                      <td className="p-4">
                        <div className="flex items-center gap-4">
                          <div className="flex-1 h-8 border-2 border-black bg-zinc-200">
                            <div
                              className={`h-full border-r-2 border-black ${isTop ? "bg-orange-500" : "bg-blue-500"}`}
                              style={{ width: `${pct}%` }}
                            ></div>
                          </div>
                          <span className="font-black text-sm w-12">{pct.toFixed(0)}%</span>
                        </div>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}

        {/* ═══════════════════════════════════════════════════════════════════════
            GAME LOGS VIEW (NEW!)
            ═══════════════════════════════════════════════════════════════════════ */}
        {!loading && viewMode === "logs" && (
          gameLogs.length > 0 ? (
          <div className="space-y-6">
            <div className="border-4 border-black bg-white p-4">
              <div className="flex items-center gap-4 flex-wrap">
                <label className="font-black uppercase text-sm">SEASON:</label>
                <div className="flex gap-2 flex-wrap">
                  {["2025-26", "2024-25", "2023-24", "2022-23", "2021-22"].map(season => (
                    <button
                      key={season}
                      onClick={() => setSelectedSeason(season)}
                      className={`px-4 py-2 border-2 border-black font-bold uppercase text-sm
                                 transition-colors ${
                                   selectedSeason === season 
                                     ? "bg-green-500 text-white" 
                                     : "bg-white hover:bg-green-100"
                                 }`}
                    >
                      {season}
                    </button>
                  ))}
                </div>
              </div>
            </div>
            {/* Advanced Stats Summary */}
{advancedStats && (
  <div className="border-4 border-black bg-white">
    <div className="border-b-4 border-black p-4 bg-green-500">
      <h2 className="font-black uppercase text-white text-xl">
        {selectedSeason} SEASON ({advancedStats.games_played}G, {advancedStats.wins}W-{advancedStats.games_played - advancedStats.wins}L)
      </h2>
    </div>
    <div className="p-6 space-y-4">
      
      {/* Main Stats */}
      <div>
        <div className="text-sm font-black uppercase mb-2 text-green-600">Per-Game Averages</div>
        <div className="grid grid-cols-3 md:grid-cols-6 gap-3">
          <div className="border-2 border-black p-3 bg-zinc-100 text-center">
            <div className="text-xs uppercase font-black mb-1">PPG</div>
            <div className="text-2xl font-black">{advancedStats.points}</div>
          </div>
          <div className="border-2 border-black p-3 bg-zinc-100 text-center">
            <div className="text-xs uppercase font-black mb-1">RPG</div>
            <div className="text-2xl font-black">{advancedStats.rebounds}</div>
          </div>
          <div className="border-2 border-black p-3 bg-zinc-100 text-center">
            <div className="text-xs uppercase font-black mb-1">APG</div>
            <div className="text-2xl font-black">{advancedStats.assists}</div>
          </div>
          <div className="border-2 border-black p-3 bg-zinc-100 text-center">
            <div className="text-xs uppercase font-black mb-1">SPG</div>
            <div className="text-2xl font-black">{advancedStats.steals}</div>
          </div>
          <div className="border-2 border-black p-3 bg-zinc-100 text-center">
            <div className="text-xs uppercase font-black mb-1">BPG</div>
            <div className="text-2xl font-black">{advancedStats.blocks}</div>
          </div>
          <div className="border-2 border-black p-3 bg-zinc-100 text-center">
            <div className="text-xs uppercase font-black mb-1">MPG</div>
            <div className="text-2xl font-black">{advancedStats.minutes}</div>
          </div>
        </div>
      </div>

      {/* Shooting Stats */}
      <div>
        <div className="text-sm font-black uppercase mb-2 text-orange-600">Shooting</div>
        <div className="grid grid-cols-3 md:grid-cols-6 gap-3">
          <div className="border-2 border-black p-3 bg-zinc-100 text-center">
            <div className="text-xs uppercase font-black mb-1">FG%</div>
            <div className="text-2xl font-black">{advancedStats.fg_pct}%</div>
          </div>
          <div className="border-2 border-black p-3 bg-zinc-100 text-center">
            <div className="text-xs uppercase font-black mb-1">FGM</div>
            <div className="text-2xl font-black">{advancedStats.fgm}</div>
          </div>
          <div className="border-2 border-black p-3 bg-zinc-100 text-center">
            <div className="text-xs uppercase font-black mb-1">FGA</div>
            <div className="text-2xl font-black">{advancedStats.fga}</div>
          </div>
          <div className="border-2 border-black p-3 bg-zinc-100 text-center">
            <div className="text-xs uppercase font-black mb-1">3P%</div>
            <div className="text-2xl font-black">{advancedStats.three_pct}%</div>
          </div>
          <div className="border-2 border-black p-3 bg-zinc-100 text-center">
            <div className="text-xs uppercase font-black mb-1">3PM</div>
            <div className="text-2xl font-black">{advancedStats.three_pm}</div>
          </div>
          <div className="border-2 border-black p-3 bg-zinc-100 text-center">
            <div className="text-xs uppercase font-black mb-1">FT%</div>
            <div className="text-2xl font-black">{advancedStats.ft_pct}%</div>
          </div>
        </div>
      </div>

      {/* Advanced Stats */}
      <div>
        <div className="text-sm font-black uppercase mb-2 text-purple-600">Advanced & Impact</div>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
          <div className="border-2 border-black p-3 bg-purple-50 text-center">
            <div className="text-xs uppercase font-black mb-1">PER</div>
            <div className="text-2xl font-black text-purple-600">{advancedStats.per}</div>
          </div>
          <div className="border-2 border-black p-3 bg-zinc-100 text-center">
            <div className="text-xs uppercase font-black mb-1">+/-</div>
            <div className="text-2xl font-black">{advancedStats.plus_minus > 0 ? '+' : ''}{advancedStats.plus_minus}</div>
          </div>
          <div className="border-2 border-black p-3 bg-zinc-100 text-center">
            <div className="text-xs uppercase font-black mb-1">TO</div>
            <div className="text-2xl font-black">{advancedStats.turnovers}</div>
          </div>
          <div className="border-2 border-black p-3 bg-blue-50 text-center">
            <div className="text-xs uppercase font-black mb-1">FPPG</div>
            <div className="text-2xl font-black text-blue-600">{advancedStats.fantasy_points}</div>
          </div>
        </div>
      </div>

    </div>
  </div>
)}

            {/* Game Logs Table */}
            <div className="border-4 border-black bg-white">
              <div className="border-b-4 border-black p-4 bg-zinc-900">
                <h2 className="font-black uppercase text-white text-xl">LAST 15 GAMES</h2>
              </div>

              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="border-b-4 border-black bg-zinc-100">
                      {["Date","OPP","W/L","PTS","REB","AST","STL","BLK","TO","FGM/A","3PM","3P%","PER","FP"].map((h) => (
                        <th key={h} className="p-3 font-black uppercase border-r-2 border-black last:border-r-0 text-right first:text-left">
                          {h}
                        </th>
                      ))}
                    </tr>
                  </thead>
                  <tbody>
                    {gameLogs.map((game, idx) => (
                      <tr
                        key={idx}
                        className={`border-b-2 border-black hover:bg-yellow-100 transition-colors ${idx % 2 === 0 ? "bg-white" : "bg-zinc-50"}`}
                      >
                        <td className="p-3 font-bold border-r-2 border-black">
                          {new Date(game.date).toLocaleDateString('en-US', { month: 'numeric', day: 'numeric' })}
                        </td>
                        <td className="p-3 text-right font-bold border-r-2 border-black text-xs">{game.opponent}</td>
                        <td className="p-3 text-right font-bold border-r-2 border-black">
                          <span className={game.result === 'W' ? 'text-green-600' : 'text-red-600'}>{game.result}</span>
                        </td>
                        <td className="p-3 text-right font-black border-r-2 border-black">{game.points}</td>
                        <td className="p-3 text-right font-bold border-r-2 border-black">{game.rebounds}</td>
                        <td className="p-3 text-right font-bold border-r-2 border-black">{game.assists}</td>
                        <td className="p-3 text-right font-bold border-r-2 border-black">{game.steals}</td>
                        <td className="p-3 text-right font-bold border-r-2 border-black">{game.blocks}</td>
                        <td className="p-3 text-right font-bold border-r-2 border-black">{game.turnovers}</td>
                        <td className="p-3 text-right font-bold border-r-2 border-black text-xs">{game.fgm}/{game.fga}</td>
                        <td className="p-3 text-right font-bold border-r-2 border-black">{game.three_pm}</td>
                        <td className="p-3 text-right font-bold border-r-2 border-black">{game.three_pct}%</td>
                        <td className="p-3 text-right font-black text-purple-600 border-r-2 border-black">{game.per}</td>
                        <td className="p-3 text-right font-black text-lg">{game.fantasy_points}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          </div>
        ) : (
          <div className="space-y-6">
            <div className="border-4 border-black bg-white p-4">
              <div className="flex items-center gap-4 flex-wrap">
                <label className="font-black uppercase text-sm">SEASON:</label>
                <div className="flex gap-2 flex-wrap">
                  {["2025-26", "2024-25", "2023-24", "2022-23", "2021-22"].map(season => (
                    <button
                      key={season}
                      onClick={() => setSelectedSeason(season)}
                      className={`px-4 py-2 border-2 border-black font-bold uppercase text-sm
                                 transition-colors ${
                                   selectedSeason === season 
                                     ? "bg-green-500 text-white" 
                                     : "bg-white hover:bg-green-100"
                                 }`}
                    >
                      {season}
                    </button>
                  ))}
                </div>
              </div>
            </div>
          <div className="border-4 border-black bg-yellow-100 p-8 text-center">
            <p className="font-black uppercase text-xl mb-2">[!] GAME LOGS UNAVAILABLE</p>
            <p className="text-sm uppercase mb-4">Check browser console (F12) for error details</p>
            <p className="text-xs">Possible causes:</p>
            <ul className="text-xs text-left max-w-md mx-auto mt-2 space-y-1">
              <li>• Backend endpoint not loaded (check main.py has new endpoints)</li>
              <li>• Player did not play in selected season</li>
              <li>• advanced_stats.py module missing in backend folder</li>
              <li>• NBA API rate limit or connection issue</li>
            </ul>
          </div>
        
          </div> 
        ))}

        {/* ═══════════════════════════════════════════════════════════════════════
            RANKINGS VIEW (NEW!)
            ═══════════════════════════════════════════════════════════════════════ */}
        {!loading && viewMode === "rankings" && (
          <div className="space-y-6">
            {/* Position Selector (NEW) */}
            <div className="border-4 border-black bg-white">
              <div className="border-b-4 border-black p-4 bg-pink-500">
                <h2 className="font-black uppercase text-white text-xl">TOP 10 BY POSITION</h2>
              </div>
              <div className="p-6">
                <div className="flex items-center gap-4 mb-4 flex-wrap">
                  <label className="font-black uppercase text-sm">FILTER:</label>
                  <div className="flex flex-wrap gap-2">
                    {["ALL", "G", "F", "C"].map(pos => (
                      <button
                        key={pos}
                        onClick={() => setSelectedPosition(pos)}
                        className={`px-4 py-2 border-2 border-black font-bold uppercase text-sm
                                   transition-colors ${
                                     selectedPosition === pos 
                                       ? "bg-pink-500 text-white" 
                                       : "bg-white hover:bg-pink-100"
                                   }`}
                      >
                        {pos}
                      </button>
                    ))}
                  </div>
                </div>
                <p className="text-xs uppercase text-zinc-500">
                  {selectedPosition === "ALL" ? "Showing top 10 overall" : `Showing top 10 ${selectedPosition}`.replace("G", "Guards").replace("F", "Forwards").replace("C", "Centers")}
                </p>
              </div>
            </div>

            {/* Loading State */}
            {loadingRankings && (
              <div className="border-4 border-black bg-yellow-100 p-8 text-center">
                <p className="font-black uppercase">LOADING RANKINGS...</p>
              </div>
            )}

            {/* Rankings Results */}
            {!loadingRankings && rankings.length > 0 && (
              <div className="border-4 border-black bg-white">
                <div className="border-b-4 border-black p-4 bg-zinc-900">
                  <h2 className="font-black uppercase text-white text-xl">
                    TOP {rankings.length} {selectedPosition !== "ALL" && selectedPosition.replace("G", "GUARDS (AVG)").replace("F", "FORWARDS (AVG)").replace("C", "CENTERS (AVG)")}
                    {selectedPosition === "ALL" ? "OVERALL (AVG)" : ""}
                  </h2>
                </div>

                <div className="overflow-x-auto">
                  <table className="w-full text-sm">
                    <thead>
                      <tr className="border-b-4 border-black bg-zinc-100">
                        {["Rank","Player","FPPG","Season Total","PPG","RPG","APG", "STL", "BLK", "TOV"].map((h) => (
                          <th key={h} className="p-3 font-black uppercase border-r-2 border-black last:border-r-0 text-right first:text-left">
                            {h}
                          </th>
                        ))}
                      </tr>
                    </thead>
                    <tbody>
                      {rankings.map((p, idx) => (
                        <tr
                          key={idx}
                          className={`border-b-2 border-black hover:bg-yellow-100 transition-colors cursor-pointer
                                     ${idx % 2 === 0 ? "bg-white" : "bg-zinc-50"}`}
                          onClick={() => { setInputValue(p.player); setPlayer(p.player); }}
                          title="Click to view this player"
                        >
                          <td className="p-3 font-black text-lg border-r-2 border-black">
                            <span className={idx < 3 ? "text-orange-500" : ""}>{p.rank}</span>
                          </td>
                          <td className="p-3 font-black uppercase border-r-2 border-black">{p.player}</td>
                          <td className="p-3 text-right font-black text-2xl text-purple-600 border-r-2 border-black">
                            {p.fantasy_ppg}
                          </td>
                          <td className="p-3 text-right font-bold border-r-2 border-black">
                            {p.fantasy_season_total?.toFixed(1) ?? "0.0"}
                          </td>
                          
                          <td className="p-3 text-right font-bold border-r-2 border-black">{p.ppg}</td>
                          <td className="p-3 text-right font-bold border-r-2 border-black">{p.rpg}</td>
                          <td className="p-3 text-right font-bold">{p.apg}</td>
                          <td className="p-3 text-right font-bold">{p.stl}</td>
                          <td className="p-3 text-right font-bold">{p.blk}</td>
                          <td className="p-3 text-right font-bold">{p.tov}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            )}

            {!loadingRankings && rankings.length === 0 && (
              <div className="border-4 border-black bg-yellow-100 p-8 text-center">
                <p className="font-black uppercase text-xl">[!] NO RANKINGS AVAILABLE</p>
                <p className="text-sm mt-2">Check backend logs for errors</p>
              </div>
            )}
          </div>
        )}
        {/* ═══════════════════════════════════════════════════════════════════════
            COMPARE VIEW (NEW!)
            ═══════════════════════════════════════════════════════════════════════ */}
        {!loading && viewMode === "compare" && (
          <div className="space-y-6">
            {/* Compare List Manager */}
            <div className="border-4 border-black bg-white">
              <div className="border-b-4 border-black p-4 bg-cyan-500">
                <h2 className="font-black uppercase text-white text-xl">COMPARE PLAYERS</h2>
              </div>
              <div className="p-6 space-y-4">
                
                {/* In-Tab Search Box (NEW) */}
                <div>
                  <label className="font-black uppercase text-sm block mb-2">ADD PLAYER TO COMPARE:</label>
                  <div className="flex gap-2">
                    <input
                      className="flex-1 border-4 border-black px-4 py-2 font-bold uppercase
                                 focus:outline-none focus:bg-yellow-100"
                      value={compareSearchInput}
                      onChange={(e) => setCompareSearchInput(e.target.value)}
                      onKeyDown={(e) => {
                        if (e.key === "Enter" && compareSearchInput.trim()) {
                          addToCompare(compareSearchInput.trim());
                          setCompareSearchInput("");
                        }
                      }}
                      placeholder="TYPE PLAYER NAME..."
                    />
                    <button
                      onClick={() => {
                        if (compareSearchInput.trim()) {
                          addToCompare(compareSearchInput.trim());
                          setCompareSearchInput("");
                        }
                      }}
                      disabled={!compareSearchInput.trim()}
                      className="px-6 py-2 border-4 border-black bg-cyan-500 font-black uppercase text-white
                                 hover:bg-cyan-400 disabled:bg-zinc-300 disabled:text-zinc-500
                                 shadow-[4px_4px_0px_0px_rgba(0,0,0,1)]
                                 hover:shadow-[2px_2px_0px_0px_rgba(0,0,0,1)]"
                    >
                      ADD
                    </button>
                  </div>
                </div>

                {/* Current Compare List */}
                <div>
                  <p className="text-sm uppercase font-bold mb-2">
                    Players in compare list: {compareList.length} / 5
                  </p>
                  <div className="flex flex-wrap gap-2 mb-4">
                    {compareList.map(name => (
                      <div key={name} className="border-2 border-black bg-zinc-100 px-3 py-2 flex items-center gap-2">
                        <span className="font-black text-sm uppercase">{name}</span>
                        <button
                          onClick={() => removeFromCompare(name)}
                          className="font-black text-red-600 hover:text-red-800"
                        >
                          ✕
                        </button>
                      </div>
                    ))}
                  </div>
                  
                  {/* Add current player shortcut */}
                  {player && !compareList.includes(player) && (
                    <button
                      onClick={() => addToCompare(player)}
                      className="mr-3 px-4 py-2 border-2 border-black bg-zinc-100 font-bold uppercase text-sm
                                 hover:bg-yellow-100"
                    >
                      + Add {player}
                    </button>
                  )}

                  {/* Compare Button */}
                  <button
                    onClick={runComparison}
                    disabled={compareList.length < 2 || loadingComparison}
                    className="px-6 py-3 border-4 border-black bg-cyan-500 font-black uppercase text-white
                               hover:bg-cyan-400 active:translate-x-1 active:translate-y-1
                               disabled:bg-zinc-300 disabled:text-zinc-500
                               shadow-[4px_4px_0px_0px_rgba(0,0,0,1)]
                               hover:shadow-[2px_2px_0px_0px_rgba(0,0,0,1)] active:shadow-none"
                  >
                    {loadingComparison ? "COMPARING..." : `COMPARE ${compareList.length} PLAYERS`}
                  </button>
                </div>
              </div>
            </div>

            {/* Comparison Results */}
            {comparisonData && comparisonData.players && (
              <div className="grid gap-6 md:grid-cols-2">
                {comparisonData.players.map((p, idx) => (
                  <div key={idx} className="border-4 border-black bg-white">
                    <div className="border-b-4 border-black p-4 bg-zinc-900">
                      <h3 className="font-black uppercase text-white text-lg">{p.player}</h3>
                    </div>

                    <div className="p-6 space-y-4">
                      {p.current_season && (
                        <div>
                          <div className="font-black uppercase text-sm mb-2 text-orange-500">[2025-26 Current]</div>
                          <div className="grid grid-cols-3 gap-2">
                            <div className="border border-black p-2 bg-zinc-50 text-center">
                              <div className="text-xs font-bold">PPG</div>
                              <div className="text-xl font-black">{p.current_season.points}</div>
                            </div>
                            <div className="border border-black p-2 bg-zinc-50 text-center">
                              <div className="text-xs font-bold">RPG</div>
                              <div className="text-xl font-black">{p.current_season.rebounds}</div>
                            </div>
                            <div className="border border-black p-2 bg-zinc-50 text-center">
                              <div className="text-xs font-bold">APG</div>
                              <div className="text-xl font-black">{p.current_season.assists}</div>
                            </div>
                            <div className="border border-black p-2 bg-zinc-50 text-center">
                              <div className="text-xs font-bold">PER</div>
                              <div className="text-xl font-black text-purple-600">{p.current_season.per}</div>
                            </div>
                            <div className="border border-black p-2 bg-zinc-50 text-center">
                              <div className="text-xs font-bold">3P%</div>
                              <div className="text-xl font-black">{p.current_season.three_pct}%</div>
                            </div>
                            <div className="border border-black p-2 bg-zinc-50 text-center">
                              <div className="text-xs font-bold">FANT</div>
                              <div className="text-xl font-black">{p.current_season.fantasy_points}</div>
                            </div>
                          </div>
                        </div>
                      )}

                      <div>
                        <div className="font-black uppercase text-sm mb-2 text-blue-500">[2025-26 Projected]</div>
                        <div className="grid grid-cols-4 gap-2">
                          <div className="border-2 border-black p-2 bg-blue-50 text-center">
                            <div className="text-xs font-bold">PPG</div>
                            <div className="text-xl font-black">{p.projected_next_season.ppg}</div>
                          </div>
                          <div className="border-2 border-black p-2 bg-blue-50 text-center">
                            <div className="text-xs font-bold">RPG</div>
                            <div className="text-xl font-black">{p.projected_next_season.rpg}</div>
                          </div>
                          <div className="border-2 border-black p-2 bg-blue-50 text-center">
                            <div className="text-xs font-bold">APG</div>
                            <div className="text-xl font-black">{p.projected_next_season.apg}</div>
                          </div>
                          <div className="border-2 border-black p-2 bg-blue-50 text-center">
                            <div className="text-xs font-bold">FANT</div>
                            <div className="text-xl font-black">{p.projected_next_season.fantasy_ppg}</div>
                          </div>
                        </div>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}

        {/* ═══════════════════════════════════════════════════════════════════════
            STANDINGS VIEW (Global - No Player Required)
            ═══════════════════════════════════════════════════════════════════════ */}
        {viewMode === "standings" && (
          <div className="border-4 border-black bg-white p-6">
            <div className="flex items-center justify-between mb-6 pb-4 border-b-4 border-black">
              <h2 className="text-3xl font-black uppercase">Fantasy Standings</h2>
              <select
                value={selectedSeason}
                onChange={(e) => {
                  setSelectedSeason(e.target.value);
                  setRankings([]);
                }}
                className="border-4 border-black px-4 py-2 font-bold"
              >
                <option value="2025-26">2025-26</option>
                <option value="2024-25">2024-25</option>
                <option value="2023-24">2023-24</option>
              </select>
            </div>

            <div className="mb-6">
              <div className="font-black text-sm mb-2">FILTER BY POSITION:</div>
              <div className="flex gap-2 flex-wrap">
                {["ALL", "G", "F", "C"].map((pos) => (
                  <button
                    key={pos}
                    onClick={() => {
                      setSelectedPosition(pos);
                      setRankings([]);
                    }}
                    className={`px-6 py-2 border-4 border-black font-black uppercase ${
                      selectedPosition === pos
                        ? "bg-orange-500 text-white shadow-none translate-x-1 translate-y-1"
                        : "bg-white hover:bg-orange-100 shadow-[4px_4px_0px_0px_rgba(0,0,0,1)]"
                    }`}
                  >
                    {pos === "ALL" ? "ALL POSITIONS" : pos}
                  </button>
                ))}
              </div>
            </div>

            {loadingRankings && (
              <div className="border-4 border-black bg-yellow-50 p-8 text-center">
                <p className="font-black uppercase">Loading Rankings...</p>
              </div>
            )}

            {rankings.length > 0 && (
              <div className="overflow-x-auto border-4 border-black">
                <table className="w-full">
                  <thead>
                    <tr className="bg-black text-white">
                      <th className="p-3 text-left font-black border-r-2 border-white">RANK</th>
                      <th className="p-3 text-left font-black border-r-2 border-white">PLAYER</th>
                      <th className="p-3 text-right font-black border-r-2 border-white">FANT/G</th>
                      <th className="p-3 text-right font-black border-r-2 border-white">SEASON</th>
                      <th className="p-3 text-right font-black border-r-2 border-white">PTS</th>
                      <th className="p-3 text-right font-black border-r-2 border-white">REB</th>
                      <th className="p-3 text-right font-black border-r-2 border-white">AST</th>
                      <th className="p-3 text-right font-black">STL+BLK</th>
                    </tr>
                  </thead>
                  <tbody>
                    {rankings.map((player, idx) => (
                      <tr 
                        key={idx}
                        className={`border-b-2 border-black cursor-pointer hover:bg-orange-50 ${
                          idx % 2 === 0 ? 'bg-zinc-50' : 'bg-white'
                        }`}
                        onClick={() => {
                          setPlayer(player.player);
                          setViewMode("projections");
                        }}
                      >
                        <td className="p-3 font-black text-lg border-r-2 border-black">{player.rank}</td>
                        <td className="p-3 font-bold border-r-2 border-black">{player.player}</td>
                        <td className="p-3 text-right font-black text-orange-600 border-r-2 border-black">
                          {player.fantasy_ppg}
                        </td>
                        <td className="p-3 text-right font-bold border-r-2 border-black">
                          {Math.round(player.fantasy_season_total)}
                        </td>
                        <td className="p-3 text-right border-r-2 border-black">{player.ppg}</td>
                        <td className="p-3 text-right border-r-2 border-black">{player.rpg}</td>
                        <td className="p-3 text-right border-r-2 border-black">{player.apg}</td>
                        <td className="p-3 text-right">{(player.stl + player.blk).toFixed(1)}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}

            <div className="mt-4 text-sm text-zinc-600 italic">
              💡 Click any player to view their full stats
            </div>
          </div>
        )}

        {/* ═══════════════════════════════════════════════════════════════════════
            MOCK DRAFT VIEW
            ═══════════════════════════════════════════════════════════════════════ */}
        {viewMode === "draft" && (
          <div className="border-4 border-black bg-white p-6">
            <div className="flex items-center justify-between mb-6 pb-4 border-b-4 border-black">
              <h2 className="text-3xl font-black uppercase">Mock Draft Simulator</h2>
            </div>

            {!draftingNow && !draftResults && (
              <div>
                <div className="border-4 border-black bg-zinc-50 p-6 mb-6">
                  <h3 className="font-black text-xl mb-4">DRAFT SETTINGS</h3>
                  
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                    <div>
                      <label className="font-black text-sm block mb-2">NUMBER OF TEAMS</label>
                      <input
                        type="number"
                        min="2"
                        max="20"
                        value={draftConfig.numTeams}
                        onChange={(e) => setDraftConfig({...draftConfig, numTeams: parseInt(e.target.value)})}
                        className="w-full border-4 border-black px-4 py-2 font-bold text-center"
                      />
                    </div>
                    
                    <div>
                      <label className="font-black text-sm block mb-2">ROUNDS</label>
                      <input
                        type="number"
                        min="1"
                        max="20"
                        value={draftConfig.rounds}
                        onChange={(e) => setDraftConfig({...draftConfig, rounds: parseInt(e.target.value)})}
                        className="w-full border-4 border-black px-4 py-2 font-bold text-center"
                      />
                    </div>
                    
                    <div>
                      <label className="font-black text-sm block mb-2">DRAFT TYPE</label>
                      <select
                        value={draftConfig.draftType}
                        onChange={(e) => setDraftConfig({...draftConfig, draftType: e.target.value})}
                        className="w-full border-4 border-black px-4 py-2 font-bold"
                      >
                        <option value="snake">Snake Draft</option>
                        <option value="linear">Linear Draft</option>
                      </select>
                    </div>
                  </div>
                  
                  <button
                    onClick={startMockDraft}
                    className="mt-6 w-full px-8 py-4 border-4 border-black bg-orange-500 
                               font-black uppercase text-white text-xl hover:bg-orange-400
                               shadow-[4px_4px_0px_0px_rgba(0,0,0,1)]"
                  >
                    START DRAFT
                  </button>
                </div>

                <div className="border-4 border-black bg-blue-50 p-4">
                  <p className="font-bold mb-2">📋 How it works:</p>
                  <ul className="list-disc list-inside space-y-1 text-sm">
                    <li>Players ranked by fantasy projections (using your custom scoring!)</li>
                    <li>Snake draft reverses order each round (1-12, 12-1, 1-12...)</li>
                    <li>Click any player to draft them</li>
                  </ul>
                </div>
              </div>
            )}

            {draftingNow && draftResults && (
              <div>
                <div className="border-4 border-black bg-orange-500 text-white p-4 mb-6">
                  <div className="flex justify-between items-center">
                    <div>
                      <div className="font-black text-2xl">
                        ROUND {draftResults.currentRound} / {draftConfig.rounds}
                      </div>
                      <div className="text-sm">Pick {draftResults.currentPick} of {draftResults.totalPicks}</div>
                    </div>
                    <div className="text-right">
                      <div className="font-black text-3xl">
                        TEAM {(() => {
                          const round = draftResults.currentRound;
                          const pickInRound = ((draftResults.currentPick - 1) % draftConfig.numTeams) + 1;
                          return draftConfig.draftType === 'snake' && round % 2 === 0
                            ? draftConfig.numTeams - pickInRound + 1
                            : pickInRound;
                        })()}
                      </div>
                      <div className="text-sm">ON THE CLOCK</div>
                    </div>
                  </div>
                </div>

                <div className="mb-6">
                  <h3 className="font-black text-xl mb-3">
                    AVAILABLE PLAYERS ({availablePlayers.length} remaining)
                  </h3>
                  
                  <div className="border-4 border-black overflow-y-auto" style={{maxHeight: '400px'}}>
                    <table className="w-full">
                      <thead className="sticky top-0 bg-black text-white">
                        <tr>
                          <th className="p-2 text-left font-black">RANK</th>
                          <th className="p-2 text-left font-black">PLAYER</th>
                          <th className="p-2 text-right font-black">FANT</th>
                          <th className="p-2 text-right font-black">PTS</th>
                          <th className="p-2 text-right font-black">REB</th>
                          <th className="p-2 text-right font-black">AST</th>
                          <th className="p-2 text-center font-black">ACTION</th>
                        </tr>
                      </thead>
                      <tbody>
                        {availablePlayers.slice(0, 50).map((player, idx) => (
                          <tr key={idx} className={`border-b-2 border-black ${idx % 2 === 0 ? 'bg-white' : 'bg-zinc-50'}`}>
                            <td className="p-2 font-bold">{player.rank}</td>
                            <td className="p-2 font-bold">{player.player}</td>
                            <td className="p-2 text-right font-black text-orange-600">{player.fantasy_ppg}</td>
                            <td className="p-2 text-right">{player.ppg}</td>
                            <td className="p-2 text-right">{player.rpg}</td>
                            <td className="p-2 text-right">{player.apg}</td>
                            <td className="p-2 text-center">
                              <button
                                onClick={() => makeDraftPick(player)}
                                className="px-4 py-1 border-2 border-black bg-orange-500 text-white 
                                           font-black uppercase text-sm hover:bg-orange-400"
                              >
                                DRAFT
                              </button>
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>

                <div>
                  <div className="flex justify-between items-center mb-3">
                    <h3 className="font-black text-xl">DRAFT BOARD</h3>
                    <button
                      onClick={resetDraft}
                      className="px-4 py-2 border-2 border-black bg-red-500 text-white font-bold uppercase text-sm"
                    >
                      RESET
                    </button>
                  </div>
                  
                  <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
                    {draftResults.teams.map((team) => (
                      <div key={team.teamNumber} className="border-4 border-black bg-white">
                        <div className="bg-black text-white p-2 font-black text-center">
                          TEAM {team.teamNumber}
                        </div>
                        <div className="p-2 space-y-1">
                          {team.picks.length === 0 ? (
                            <div className="text-center py-4 text-zinc-400 text-sm">No picks</div>
                          ) : (
                            team.picks.map((pick, idx) => (
                              <div key={idx} className="border-2 border-black p-2 bg-zinc-50 text-xs">
                                <div className="font-black">R{pick.round}</div>
                                <div className="font-bold truncate">{pick.player}</div>
                                <div className="text-orange-600 font-bold">{pick.fantasy_ppg}</div>
                              </div>
                            ))
                          )}
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            )}
          </div>
        )}

        {/* ── EMPTY STATE ── */}
        {!loading && !error && detailedStats.length === 0 && !careerSummary && (
          <div className="border-4 border-black bg-white p-16 text-center">
            <div className="inline-block border-4 border-black p-8 mb-6 bg-zinc-100">
              <div className="text-6xl font-black">[ ? ]</div>
            </div>
            <p className="font-black uppercase text-2xl mb-2">NO DATA</p>
            <p className="uppercase text-sm">Enter a player name to begin</p>
          </div>
        )}

      </div>
    </div>
  );
}