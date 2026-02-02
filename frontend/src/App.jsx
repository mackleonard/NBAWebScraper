import { useState } from "react";

const API_URL = window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1'
  ? 'http://localhost:8000'  // Local development
  : '/api';                    // Docker (proxied through nginx)

console.log('Using API_URL:', API_URL);

export default function App() {
  const [player, setPlayer] = useState("");
  const [detailedStats, setDetailedStats] = useState([]);
  const [careerSummary, setCareerSummary] = useState(null);
  const [projections, setProjections] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [viewMode, setViewMode] = useState("projections");

  async function loadPlayerData() {
    if (!player.trim()) {
      setError("Please enter a player name");
      return;
    }

    try {
      setLoading(true);
      setError(null);
      setDetailedStats([]);
      setCareerSummary(null);
      setProjections(null);
      
      console.log(`Fetching data for: ${player}`);
      console.log(`API URL: ${API_URL}`);
      
      // Fetch detailed stats
      const detailedRes = await fetch(
        `${API_URL}/player/detailed-stats?player=${encodeURIComponent(player)}`
      );
      
      console.log(`Detailed stats response status: ${detailedRes.status}`);
      
      if (!detailedRes.ok) {
        const errorData = await detailedRes.json().catch(() => ({}));
        throw new Error(errorData.detail || "Player not found or API error");
      }
      
      const detailedData = await detailedRes.json();
      console.log(`Detailed stats received: ${detailedData.length} seasons`);
      setDetailedStats(detailedData);
      
      // Fetch career summary
      const summaryRes = await fetch(
        `${API_URL}/player/career-summary?player=${encodeURIComponent(player)}`
      );
      
      if (summaryRes.ok) {
        const summaryData = await summaryRes.json();
        console.log(`Career summary received`);
        setCareerSummary(summaryData);
      }
      
      // Fetch projections
      const projectionsRes = await fetch(
        `${API_URL}/projections/all?player=${encodeURIComponent(player)}&season=2025-26`
      );
      
      if (projectionsRes.ok) {
        const projectionsData = await projectionsRes.json();
        console.log(`Projections received`);
        setProjections(projectionsData);
      }
      
    } catch (e) {
      console.error("Error loading player data:", e);
      setDetailedStats([]);
      setCareerSummary(null);
      setProjections(null);
      
      // More detailed error message
      if (e.message.includes("Failed to fetch")) {
        setError(`Cannot connect to backend at ${API_URL}. Make sure the backend server is running.`);
      } else {
        setError(e.message);
      }
    } finally {
      setLoading(false);
    }
  }

  function handleKeyPress(e) {
    if (e.key === "Enter") {
      loadPlayerData();
    }
  }

  const maxFantasyPoints = Math.max(...detailedStats.map(r => r.fantasy_points), 0);

  return (
    <div className="min-h-screen bg-zinc-50 font-mono">
      <div className="max-w-6xl mx-auto px-8 py-16">
        {/* Header */}
        <div className="mb-16 border-8 border-black p-8 bg-white relative">
          <div className="absolute -top-4 -right-4 w-20 h-20 bg-orange-500 border-4 border-black"></div>
          <h1 className="text-7xl font-black uppercase tracking-tighter mb-2">
            NBA
            <br />
            ANALYTICS
          </h1>
          <div className="w-32 h-2 bg-black"></div>
        </div>

        {/* Search */}
        <div className="mb-8 border-4 border-black bg-white">
          <div className="border-b-4 border-black p-4 bg-zinc-900 text-white">
            <p className="font-bold uppercase text-sm tracking-wider">Search Player</p>
          </div>
          <div className="p-6">
            <div className="flex gap-4">
              <input
                className="flex-1 border-4 border-black px-4 py-3 text-lg font-bold uppercase
                         focus:outline-none focus:bg-yellow-100 transition-colors"
                value={player}
                onChange={(e) => setPlayer(e.target.value)}
                onKeyPress={handleKeyPress}
                placeholder="PLAYER NAME"
                disabled={loading}
              />
              <button
                onClick={loadPlayerData}
                disabled={loading}
                className="px-8 py-3 border-4 border-black bg-orange-500 font-black uppercase
                         hover:bg-orange-400 active:translate-x-1 active:translate-y-1
                         disabled:bg-zinc-300 transition-all shadow-[4px_4px_0px_0px_rgba(0,0,0,1)]
                         hover:shadow-[2px_2px_0px_0px_rgba(0,0,0,1)] active:shadow-none"
              >
                {loading ? "WAIT" : "GO"}
              </button>
            </div>
          </div>
        </div>

        {/* Loading */}
        {loading && (
          <div className="border-4 border-black bg-white p-12 text-center mb-8">
            <div className="inline-block border-4 border-black p-4 bg-yellow-100">
              <p className="font-black uppercase text-lg">LOADING DATA...</p>
            </div>
          </div>
        )}

        {/* Error */}
        {error && (
          <div className="border-4 border-black bg-red-500 p-6 mb-8">
            <p className="font-black uppercase text-white">[ERROR] {error}</p>
          </div>
        )}

        {/* Career Summary */}
        {careerSummary && !loading && (
          <div className="mb-8">
            <div className="border-4 border-black bg-zinc-900 text-white p-4 mb-4">
              <h2 className="font-black uppercase text-xl">CAREER SUMMARY</h2>
            </div>
            
            <div className="grid grid-cols-2 md:grid-cols-4 gap-6">
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

        {/* View Mode Toggle */}
        {detailedStats.length > 0 && !loading && (
          <div className="mb-8 flex gap-4">
            <button
              onClick={() => setViewMode("projections")}
              className={`px-6 py-3 border-4 border-black font-black uppercase
                       ${viewMode === "projections" ? "bg-purple-500 text-white" : "bg-white"}
                       hover:bg-purple-400 active:translate-x-1 active:translate-y-1 transition-all
                       shadow-[4px_4px_0px_0px_rgba(0,0,0,1)] hover:shadow-[2px_2px_0px_0px_rgba(0,0,0,1)]
                       active:shadow-none`}
            >
              [PROJECTIONS]
            </button>
            <button
              onClick={() => setViewMode("detailed")}
              className={`px-6 py-3 border-4 border-black font-black uppercase
                       ${viewMode === "detailed" ? "bg-orange-500 text-white" : "bg-white"}
                       hover:bg-orange-400 active:translate-x-1 active:translate-y-1 transition-all
                       shadow-[4px_4px_0px_0px_rgba(0,0,0,1)] hover:shadow-[2px_2px_0px_0px_rgba(0,0,0,1)]
                       active:shadow-none`}
            >
              [STATS]
            </button>
            <button
              onClick={() => setViewMode("simple")}
              className={`px-6 py-3 border-4 border-black font-black uppercase
                       ${viewMode === "simple" ? "bg-blue-500 text-white" : "bg-white"}
                       hover:bg-blue-400 active:translate-x-1 active:translate-y-1 transition-all
                       shadow-[4px_4px_0px_0px_rgba(0,0,0,1)] hover:shadow-[2px_2px_0px_0px_rgba(0,0,0,1)]
                       active:shadow-none`}
            >
              [FANTASY]
            </button>
          </div>
        )}

        {/* PROJECTIONS VIEW */}
        {projections && !loading && viewMode === "projections" && (
          <div className="space-y-8">
            {/* Next Game Projection */}
            {projections.next_game && (
              <div className="border-4 border-black bg-white">
                <div className="border-b-4 border-black p-4 bg-purple-500">
                  <h2 className="font-black uppercase text-white text-xl flex items-center gap-3">
                    [NEXT GAME PROJECTION]
                    <span className="text-sm font-normal">
                      ({projections.next_game.games_analyzed} GAMES ANALYZED)
                    </span>
                  </h2>
                </div>
                
                <div className="p-8">
                  {/* Trend */}
                  {projections.next_game.recent_performance && (
                    <div className="mb-6 border-4 border-black p-4 inline-block">
                      <span className="font-black uppercase mr-4">TREND:</span>
                      <span className={`font-black uppercase ${
                        projections.next_game.recent_performance.trend === "trending_up" 
                          ? "text-green-600"
                          : projections.next_game.recent_performance.trend === "trending_down"
                          ? "text-red-600"
                          : "text-black"
                      }`}>
                        {projections.next_game.recent_performance.trend === "trending_up" && "[↑ UP]"}
                        {projections.next_game.recent_performance.trend === "trending_down" && "[↓ DOWN]"}
                        {projections.next_game.recent_performance.trend === "stable" && "[→ STABLE]"}
                      </span>
                    </div>
                  )}
                  
                  <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
                    {Object.entries(projections.next_game.projected_stats).map(([stat, value]) => (
                      <div key={stat} className="border-2 border-black p-4 bg-zinc-100">
                        <div className="text-xs uppercase font-black mb-2">
                          {stat.replace(/_/g, ' ')}
                        </div>
                        <div className="text-4xl font-black">{value}</div>
                      </div>
                    ))}
                  </div>
                  
                  <div className="border-4 border-black bg-yellow-400 p-6">
                    <div className="flex items-center justify-between">
                      <span className="font-black text-lg uppercase">Fantasy Points</span>
                      <span className="text-5xl font-black">
                        {projections.next_game.projected_fantasy_points}
                      </span>
                    </div>
                  </div>
                </div>
              </div>
            )}

            {/* Season Projections */}
            {projections.season_projections && (
              <div className="border-4 border-black bg-white">
                <div className="border-b-4 border-black p-4 bg-zinc-900">
                  <h2 className="font-black uppercase text-white text-xl">
                    [SEASON PROJECTIONS / 2025-26]
                  </h2>
                </div>
                
                <div className="p-8 space-y-6">
                  {Object.entries(projections.season_projections).map(([method, data]) => {
                    if (!data) return null;
                    
                    return (
                      <div key={method} className="border-2 border-black p-6 bg-zinc-50">
                        <h3 className="text-xl font-black mb-4 uppercase flex items-center gap-2">
                          [{method.replace(/_/g, ' ')}]
                          {data.adjustment_factor && (
                            <span className="text-sm">
                              (ADJ: {(data.adjustment_factor * 100).toFixed(0)}%)
                            </span>
                          )}
                        </h3>
                        
                        <div className="grid grid-cols-4 md:grid-cols-8 gap-2 mb-4">
                          {Object.entries(data.projected_per_game).map(([stat, value]) => (
                            <div key={stat} className="text-center border border-black p-2 bg-white">
                              <div className="text-xs uppercase font-bold mb-1">
                                {stat.replace(/_/g, ' ').replace('three pointers', '3PM')}
                              </div>
                              <div className="text-xl font-black">{value}</div>
                            </div>
                          ))}
                        </div>
                        
                        <div className="grid grid-cols-2 gap-4">
                          <div className="border-2 border-black p-4 bg-white">
                            <div className="text-xs uppercase font-black mb-1">Per Game</div>
                            <div className="text-3xl font-black">
                              {data.projected_fantasy_points_per_game} FP
                            </div>
                          </div>
                          <div className="border-2 border-black p-4 bg-white">
                            <div className="text-xs uppercase font-black mb-1">Season (82G)</div>
                            <div className="text-3xl font-black">
                              {data.projected_fantasy_points_season} FP
                            </div>
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

        {/* DETAILED STATS VIEW */}
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
                    <th className="text-left p-3 font-black uppercase border-r-4 border-black">Season</th>
                    <th className="text-center p-3 font-black uppercase border-r-2 border-black">GP</th>
                    <th className="text-right p-3 font-black uppercase border-r-2 border-black">MPG</th>
                    <th className="text-right p-3 font-black uppercase border-r-2 border-black">PPG</th>
                    <th className="text-right p-3 font-black uppercase border-r-2 border-black">RPG</th>
                    <th className="text-right p-3 font-black uppercase border-r-2 border-black">APG</th>
                    <th className="text-right p-3 font-black uppercase border-r-2 border-black">SPG</th>
                    <th className="text-right p-3 font-black uppercase border-r-2 border-black">BPG</th>
                    <th className="text-right p-3 font-black uppercase border-r-2 border-black">FG%</th>
                    <th className="text-right p-3 font-black uppercase">FPTS</th>
                  </tr>
                </thead>
                <tbody>
                  {detailedStats.map((r, idx) => {
                    const isTopSeason = r.fantasy_points === maxFantasyPoints;
                    
                    return (
                      <tr
                        key={r.season}
                        className={`border-b-2 border-black ${
                          idx % 2 === 0 ? 'bg-white' : 'bg-zinc-50'
                        } hover:bg-yellow-100 transition-colors`}
                      >
                        <td className="p-3 font-black uppercase border-r-2 border-black">
                          {isTopSeason && <span className="text-orange-500">[★] </span>}
                          {r.season}
                        </td>
                        <td className="p-3 text-center font-bold border-r-2 border-black">{r.games_played}</td>
                        <td className="p-3 text-right font-bold border-r-2 border-black">{r.mpg}</td>
                        <td className="p-3 text-right font-bold border-r-2 border-black">{r.ppg}</td>
                        <td className="p-3 text-right font-bold border-r-2 border-black">{r.rpg}</td>
                        <td className="p-3 text-right font-bold border-r-2 border-black">{r.apg}</td>
                        <td className="p-3 text-right font-bold border-r-2 border-black">{r.spg}</td>
                        <td className="p-3 text-right font-bold border-r-2 border-black">{r.bpg}</td>
                        <td className="p-3 text-right font-bold border-r-2 border-black">{r.fg_pct}%</td>
                        <td className="p-3 text-right">
                          <span className={`font-black text-lg ${isTopSeason ? 'text-orange-500' : ''}`}>
                            {r.fantasy_ppg}
                          </span>
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          </div>
        )}

        {/* SIMPLE FANTASY VIEW */}
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
                  const percentage = (r.fantasy_points / maxFantasyPoints) * 100;
                  const isTopSeason = r.fantasy_points === maxFantasyPoints;
                  
                  return (
                    <tr
                      key={r.season}
                      className={`border-b-2 border-black ${
                        idx % 2 === 0 ? 'bg-white' : 'bg-zinc-50'
                      } hover:bg-yellow-100 transition-colors`}
                    >
                      <td className="p-4 font-black uppercase border-r-2 border-black">
                        {isTopSeason && <span className="text-orange-500">[★] </span>}
                        {r.season}
                      </td>
                      <td className="p-4 text-right font-black text-2xl border-r-2 border-black">
                        {r.fantasy_points.toLocaleString(undefined, {maximumFractionDigits: 1})} FP
                      </td>
                      <td className="p-4 text-right font-black text-lg border-r-2 border-black">
                        {r.fantasy_ppg} FP
                      </td>
                      <td className="p-4">
                        <div className="flex items-center gap-4">
                          <div className="flex-1 h-8 border-2 border-black bg-zinc-200">
                            <div
                              className={`h-full ${
                                isTopSeason ? 'bg-orange-500' : 'bg-blue-500'
                              } border-r-2 border-black`}
                              style={{width: `${percentage}%`}}
                            ></div>
                          </div>
                          <span className="font-black text-sm w-12">
                            {percentage.toFixed(0)}%
                          </span>
                        </div>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}

        {/* Empty State */}
        {!loading && !error && detailedStats.length === 0 && (
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