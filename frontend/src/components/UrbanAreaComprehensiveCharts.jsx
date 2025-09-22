import React, { useEffect, useState } from 'react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, BarChart, Bar } from 'recharts';

function UrbanAreaComprehensiveCharts({ startYear, endYear }) {
  const [data, setData] = useState(null);
  const [error, setError] = useState(null);

  useEffect(() => {
    if (!startYear || !endYear) return;
    setError(null);
    fetch(`http://localhost:8000/analysis/urban-area-comprehensive-stats?start_year=${startYear}&end_year=${endYear}`)
      .then(res => {
        if (!res.ok) throw new Error('Invalid year range or server error');
        return res.json();
      })
      .then(json => {
        // Prepare chart data
        const chartData = json.years.map((year, i) => ({
          year,
          urban_area: json.urban_areas[i],
          urban_area_in_risk: json.urban_areas_in_risk[i],
          population_in_urban: json.populations_in_urban[i],
          population_in_urban_risk: json.populations_in_urban_risk[i],
          total_population: json.total_populations[i],
        }));
        
        // Calculate growth percentages
        const growthData = chartData.slice(1).map((current, i) => {
          const previous = chartData[i];
          
          // Population growth rates
          const totalPopulationGrowth = previous.total_population > 0 
            ? ((current.total_population - previous.total_population) / previous.total_population) * 100 
            : 0;
          const populationInUrbanGrowth = previous.population_in_urban > 0 
            ? ((current.population_in_urban - previous.population_in_urban) / previous.population_in_urban) * 100 
            : 0;
          const populationInUrbanRiskGrowth = previous.population_in_urban_risk > 0 
            ? ((current.population_in_urban_risk - previous.population_in_urban_risk) / previous.population_in_urban_risk) * 100 
            : 0;
          
          // Urban area growth rates
          const urbanAreaGrowth = previous.urban_area > 0 
            ? ((current.urban_area - previous.urban_area) / previous.urban_area) * 100 
            : 0;
          const urbanAreaInRiskGrowth = previous.urban_area_in_risk > 0 
            ? ((current.urban_area_in_risk - previous.urban_area_in_risk) / previous.urban_area_in_risk) * 100 
            : 0;
          
          return {
            year: current.year,
            total_population_growth: totalPopulationGrowth,
            population_in_urban_growth: populationInUrbanGrowth,
            population_in_urban_risk_growth: populationInUrbanRiskGrowth,
            urban_area_growth: urbanAreaGrowth,
            urban_area_in_risk_growth: urbanAreaInRiskGrowth
          };
        });
        
        setData({ ...json, chartData, growthData });
      })
      .catch(err => setError(err.message));
  }, [startYear, endYear]);

  if (error) return <div style={{ color: 'red' }}>Error: {error}</div>;
  if (!data) return <div>Loading comprehensive urban area stats...</div>;

  const summary = data.summary;
  
  // Calculate Y-axis domains for better visualization
  const maxPopulation = Math.max(...data.total_populations);
  const maxUrbanPopulation = Math.max(...data.populations_in_urban);
  const maxUrbanRiskPopulation = Math.max(...data.populations_in_urban_risk);
  
  // Set reasonable Y-axis limits (cut off very high values)
  const populationThreshold = Math.max(maxPopulation, maxUrbanPopulation, maxUrbanRiskPopulation) * 1.1;
  const yDomain = [0, populationThreshold];

  return (
    <div style={{ marginTop: 32 }}>
      {/* Summary Statistics */}
      <div style={{ 
        display: 'grid', 
        gridTemplateColumns: 'repeat(auto-fit, minmax(250px, 1fr))', 
        gap: '20px', 
        marginBottom: '32px' 
      }}>
        <div style={{ background: '#181c24', color: '#fff', padding: '20px', borderRadius: '8px' }}>
          <h4 style={{ margin: '0 0 10px 0', opacity: 0.8 }}>Time Period</h4>
          <div style={{ fontSize: '24px', fontWeight: 'bold' }}>
            {summary.start_year} - {summary.end_year}
          </div>
        </div>
        
        <div style={{ background: '#181c24', color: '#fff', padding: '20px', borderRadius: '8px' }}>
          <h4 style={{ margin: '0 0 10px 0', opacity: 0.8 }}>Urban Area ({summary.end_year})</h4>
          <div style={{ fontSize: '24px', fontWeight: 'bold' }}>
            {summary.urban_area_end_year ? summary.urban_area_end_year.toFixed(1) : '-'} km²
          </div>
        </div>
        
        <div style={{ background: '#181c24', color: '#fff', padding: '20px', borderRadius: '8px' }}>
          <h4 style={{ margin: '0 0 10px 0', opacity: 0.8 }}>Urban Area in Risk</h4>
          <div style={{ fontSize: '24px', fontWeight: 'bold', color: '#ff6b6b' }}>
            {summary.urban_area_in_risk_end_year ? summary.urban_area_in_risk_end_year.toFixed(1) : '-'} km²
          </div>
        </div>
        
        <div style={{ background: '#181c24', color: '#fff', padding: '20px', borderRadius: '8px' }}>
          <h4 style={{ margin: '0 0 10px 0', opacity: 0.8 }}>Urbanization %</h4>
          <div style={{ fontSize: '24px', fontWeight: 'bold' }}>
            {summary.urbanization_pct ? summary.urbanization_pct.toFixed(1) : '-'}%
          </div>
        </div>
        
        <div style={{ background: '#181c24', color: '#fff', padding: '20px', borderRadius: '8px' }}>
          <h4 style={{ margin: '0 0 10px 0', opacity: 0.8 }}>Urbanization Change</h4>
          <div style={{ 
            fontSize: '24px', 
            fontWeight: 'bold',
            color: summary.urbanization_change_ratio >= 0 ? '#4caf50' : '#f44336'
          }}>
            {summary.urbanization_change_ratio ? summary.urbanization_change_ratio.toFixed(1) : '-'}%
          </div>
        </div>
        
        <div style={{ background: '#181c24', color: '#fff', padding: '20px', borderRadius: '8px' }}>
          <h4 style={{ margin: '0 0 10px 0', opacity: 0.8 }}>Population in Urban</h4>
          <div style={{ fontSize: '24px', fontWeight: 'bold' }}>
            {summary.population_in_urban ? Math.round(summary.population_in_urban).toLocaleString() : '-'}
          </div>
        </div>
        
        <div style={{ background: '#181c24', color: '#fff', padding: '20px', borderRadius: '8px' }}>
          <h4 style={{ margin: '0 0 10px 0', opacity: 0.8 }}>Population in Urban & Risk</h4>
          <div style={{ fontSize: '24px', fontWeight: 'bold', color: '#ff6b6b' }}>
            {summary.population_in_urban_risk ? Math.round(summary.population_in_urban_risk).toLocaleString() : '-'}
          </div>
        </div>
        
        <div style={{ background: '#181c24', color: '#fff', padding: '20px', borderRadius: '8px' }}>
          <h4 style={{ margin: '0 0 10px 0', opacity: 0.8 }}>Urban Population Ratio</h4>
          <div style={{ fontSize: '24px', fontWeight: 'bold' }}>
            {summary.population_ratio_urban ? summary.population_ratio_urban.toFixed(1) : '-'}%
          </div>
        </div>
        
        <div style={{ background: '#181c24', color: '#fff', padding: '20px', borderRadius: '8px' }}>
          <h4 style={{ margin: '0 0 10px 0', opacity: 0.8 }}>Urban Risk Population Ratio</h4>
          <div style={{ fontSize: '24px', fontWeight: 'bold', color: '#ff6b6b' }}>
            {summary.population_ratio_urban_risk ? summary.population_ratio_urban_risk.toFixed(1) : '-'}%
          </div>
        </div>
      </div>

      {/* Line Charts */}
      <h3>Population Trends</h3>
      <ResponsiveContainer width="100%" height={400}>
        <LineChart data={data.chartData} margin={{ top: 20, right: 30, left: 20, bottom: 5 }}>
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis dataKey="year" />
          <YAxis domain={yDomain} />
          <Tooltip formatter={(value) => [Math.round(value).toLocaleString(), 'Population']} />
          <Legend />
          <Line 
            type="monotone" 
            dataKey="total_population" 
            stroke="#1976d2" 
            name="Total Population" 
            strokeWidth={2}
          />
          <Line 
            type="monotone" 
            dataKey="population_in_urban" 
            stroke="#4caf50" 
            name="Population in Urban Area" 
            strokeWidth={2}
          />
          <Line 
            type="monotone" 
            dataKey="population_in_urban_risk" 
            stroke="#f44336" 
            name="Population in Urban & Risk Area" 
            strokeWidth={2}
          />
        </LineChart>
      </ResponsiveContainer>

      <h3 style={{ marginTop: 32 }}>Urban Area Trends</h3>
      <ResponsiveContainer width="100%" height={400}>
        <LineChart data={data.chartData} margin={{ top: 20, right: 30, left: 20, bottom: 5 }}>
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis dataKey="year" />
          <YAxis label={{ value: 'Area (km²)', angle: -90, position: 'insideLeft' }} />
          <Tooltip formatter={(value) => [value.toFixed(1), 'km²']} />
          <Legend />
          <Line 
            type="monotone" 
            dataKey="urban_area" 
            stroke="#1976d2" 
            name="Urban Area" 
            strokeWidth={2}
          />
          <Line 
            type="monotone" 
            dataKey="urban_area_in_risk" 
            stroke="#f44336" 
            name="Urban Area in Risk" 
            strokeWidth={2}
          />
        </LineChart>
      </ResponsiveContainer>

      {/* Growth Rate Charts */}
      <h3 style={{ marginTop: 32 }}>Population Growth Rate (%)</h3>
      <ResponsiveContainer width="100%" height={400}>
        <BarChart data={data.growthData} margin={{ top: 20, right: 30, left: 20, bottom: 5 }}>
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis dataKey="year" />
          <YAxis label={{ value: 'Growth Rate (%)', angle: -90, position: 'insideLeft' }} />
          <Tooltip formatter={(value) => [value.toFixed(1) + '%', 'Growth Rate']} />
          <Legend />
          <Bar 
            dataKey="total_population_growth" 
            fill="#1976d2" 
            name="Total Population"
          />
          <Bar 
            dataKey="population_in_urban_growth" 
            fill="#4caf50" 
            name="Population in Urban Area"
          />
          <Bar 
            dataKey="population_in_urban_risk_growth" 
            fill="#f44336" 
            name="Population in Urban & Risk Area"
          />
        </BarChart>
      </ResponsiveContainer>

      <h3 style={{ marginTop: 32 }}>Urban Area Growth Rate (%)</h3>
      <ResponsiveContainer width="100%" height={400}>
        <BarChart data={data.growthData} margin={{ top: 20, right: 30, left: 20, bottom: 5 }}>
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis dataKey="year" />
          <YAxis label={{ value: 'Growth Rate (%)', angle: -90, position: 'insideLeft' }} />
          <Tooltip formatter={(value) => [value.toFixed(1) + '%', 'Growth Rate']} />
          <Legend />
          <Bar 
            dataKey="urban_area_growth" 
            fill="#1976d2" 
            name="Urban Area"
          />
          <Bar 
            dataKey="urban_area_in_risk_growth" 
            fill="#f44336" 
            name="Urban Area in Risk"
          />
        </BarChart>
      </ResponsiveContainer>

      {/* Risk Analysis Summary */}
      <h3 style={{ marginTop: 32 }}>Risk Analysis Summary</h3>
      <div style={{ 
        display: 'grid', 
        gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))', 
        gap: '20px', 
        marginBottom: '32px' 
      }}>
        <div style={{ background: '#fff3e0', padding: '20px', borderRadius: '8px', border: '1px solid #ffb74d' }}>
          <h4 style={{ margin: '0 0 10px 0', color: '#e65100' }}>Urban Area at Risk</h4>
          <div style={{ fontSize: '24px', fontWeight: 'bold' }}>
            {summary.urban_area_in_risk_end_year && summary.urban_area_end_year ? 
              ((summary.urban_area_in_risk_end_year / summary.urban_area_end_year) * 100).toFixed(1) : '-'}%
          </div>
          <div style={{ fontSize: '14px', color: '#666' }}>
            of total urban area is at risk from sea-level rise
          </div>
        </div>
        
        <div style={{ background: '#f3e5f5', padding: '20px', borderRadius: '8px', border: '1px solid #ba68c8' }}>
          <h4 style={{ margin: '0 0 10px 0', color: '#7b1fa2' }}>Urban Population at Risk</h4>
          <div style={{ fontSize: '24px', fontWeight: 'bold' }}>
            {summary.population_in_urban_risk && summary.population_in_urban ? 
              ((summary.population_in_urban_risk / summary.population_in_urban) * 100).toFixed(1) : '-'}%
          </div>
          <div style={{ fontSize: '14px', color: '#666' }}>
            of urban population is at risk from sea-level rise
          </div>
        </div>
        
        <div style={{ background: '#e8f5e8', padding: '20px', borderRadius: '8px', border: '1px solid #81c784' }}>
          <h4 style={{ margin: '0 0 10px 0', color: '#2e7d32' }}>Urbanization Growth</h4>
          <div style={{ fontSize: '24px', fontWeight: 'bold' }}>
            {summary.urbanization_change_ratio ? summary.urbanization_change_ratio.toFixed(1) : '-'}%
          </div>
          <div style={{ fontSize: '14px', color: '#666' }}>
            change in urbanization from {summary.start_year} to {summary.end_year}
          </div>
        </div>
      </div>
    </div>
  );
}

export default UrbanAreaComprehensiveCharts; 