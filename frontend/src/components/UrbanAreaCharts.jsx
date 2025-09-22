import React, { useEffect, useState } from 'react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, BarChart, Bar, ResponsiveContainer } from 'recharts';

// Calculate bbox area in km² (approximate, for Jakarta bbox)
const JAKARTA_BBOX_AREA_KM2 = 662; // You can adjust this value as needed

function UrbanAreaCharts({ year }) {
  const [data, setData] = useState(null);
  const [error, setError] = useState(null);

  useEffect(() => {
    if (!year) return;
    setError(null);
    fetch(`http://localhost:8000/analysis/urban-area-stats?year=${year}`)
      .then(res => {
        if (!res.ok) throw new Error('Invalid year or server error');
        return res.json();
      })
      .then(json => {
        setData(json);
      })
      .catch(err => setError(err.message));
  }, [year]);

  if (error) return <div style={{ color: 'red' }}>Error: {error}</div>;
  if (!data) return <div>Loading urban area stats...</div>;

  return (
    <div style={{ marginTop: 32 }}>
      {/* Summary statistics */}
      <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 32, background: '#181c24', color: '#fff', padding: '24px 16px', borderRadius: 8 }}>
        <div>
          <div style={{ fontSize: 16, opacity: 0.8 }}>Urban Area ({data.year})</div>
          <div style={{ fontSize: 32, fontWeight: 700 }}>{data.total_urban_area ? data.total_urban_area.toFixed(1) : '-'} km²</div>
        </div>
        <div>
          <div style={{ fontSize: 16, opacity: 0.8 }}>Urbanization %</div>
          <div style={{ fontSize: 32, fontWeight: 700 }}>{data.urbanization_pct ? data.urbanization_pct.toFixed(1) : '-'}%</div>
        </div>
        <div>
          <div style={{ fontSize: 16, opacity: 0.8 }}>Population in Urban Area</div>
          <div style={{ fontSize: 32, fontWeight: 700 }}>{data.pop_in_urban ? Math.round(data.pop_in_urban).toLocaleString() : '-'}</div>
        </div>
      </div>

      <h3>Urban Area in Risk Area (km²)</h3>
      <div style={{ background: '#f5f5f5', padding: '20px', borderRadius: '8px', marginBottom: '32px' }}>
        <div style={{ fontSize: '24px', fontWeight: 'bold', color: '#e53935' }}>
          {data.urban_area_in_risk ? data.urban_area_in_risk.toFixed(1) : '-'} km²
        </div>
        <div style={{ fontSize: '14px', color: '#666' }}>
          Urban area that is below the sea level threshold
        </div>
      </div>

      <h3>Population in Urban Area and Risk Area</h3>
      <div style={{ background: '#f5f5f5', padding: '20px', borderRadius: '8px', marginBottom: '32px' }}>
        <div style={{ fontSize: '24px', fontWeight: 'bold', color: '#e53935' }}>
          {data.pop_in_urban_risk ? Math.round(data.pop_in_urban_risk).toLocaleString() : '-'} people
        </div>
        <div style={{ fontSize: '14px', color: '#666' }}>
          Population living in urban areas that are below the sea level threshold
        </div>
      </div>

      <h3>Risk Analysis Summary</h3>
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '20px', marginBottom: '32px' }}>
        <div style={{ background: '#fff3e0', padding: '20px', borderRadius: '8px', border: '1px solid #ffb74d' }}>
          <h4 style={{ margin: '0 0 10px 0', color: '#e65100' }}>Urban Area at Risk</h4>
          <div style={{ fontSize: '18px', fontWeight: 'bold' }}>
            {data.urban_area_in_risk && data.total_urban_area ? 
              ((data.urban_area_in_risk / data.total_urban_area) * 100).toFixed(1) : '-'}%
          </div>
          <div style={{ fontSize: '14px', color: '#666' }}>
            of total urban area is at risk
          </div>
        </div>
        <div style={{ background: '#f3e5f5', padding: '20px', borderRadius: '8px', border: '1px solid #ba68c8' }}>
          <h4 style={{ margin: '0 0 10px 0', color: '#7b1fa2' }}>Population at Risk</h4>
          <div style={{ fontSize: '18px', fontWeight: 'bold' }}>
            {data.pop_in_urban_risk && data.pop_in_urban ? 
              ((data.pop_in_urban_risk / data.pop_in_urban) * 100).toFixed(1) : '-'}%
          </div>
          <div style={{ fontSize: '14px', color: '#666' }}>
            of urban population is at risk
          </div>
        </div>
      </div>
    </div>
  );
}

export default UrbanAreaCharts; 