import React, { useState, useEffect } from 'react';
import { MapContainer, TileLayer, CircleMarker, Popup, ImageOverlay } from 'react-leaflet';
import 'leaflet/dist/leaflet.css';
import { Icon } from 'leaflet';
import { DataGrid } from '@mui/x-data-grid';
import { getCityCoordinates } from '../api';
import { generateYearOptions, getYearRangeText, getDataSourceText } from '../utils/yearSelector';

// Custom icons for different infrastructure types
const createCustomIcon = (color) => {
  return new Icon({
    iconUrl: `data:image/svg+xml;base64,${btoa(`
      <svg width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
        <circle cx="12" cy="12" r="8" fill="${color}" stroke="white" stroke-width="2"/>
      </svg>
    `)}`,
    iconSize: [24, 24],
    iconAnchor: [12, 12],
    popupAnchor: [0, -12]
  });
};

const infrastructureIcons = {
  'Hospital': createCustomIcon('#ff4444'),
  'School': createCustomIcon('#4444ff'),
  'Police Station': createCustomIcon('#44ff44'),
  'Fire Station': createCustomIcon('#ff8844'),
  'Government Agency': createCustomIcon('#8844ff')
};

// Jakarta bounding box (SW and NE corners)
const JAKARTA_BOUNDS = [
  [-6.365, 106.689], // Southwest (lat, lng)
  [-6.089, 106.971], // Northeast (lat, lng)
];

const InfrastructureExposure = ({ year, threshold, city, onYearChange }) => {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [cityBounds, setCityBounds] = useState(JAKARTA_BOUNDS);
  const [mapCenter, setMapCenter] = useState(null);
  const [selectedYear, setSelectedYear] = useState(year);
  const [yearOptions, setYearOptions] = useState({ options: '', dataInfo: null });

  // 연도 옵션 초기화
  useEffect(() => {
    const { options, dataInfo } = generateYearOptions('infrastructure-exposure');
    setYearOptions({ options, dataInfo });
  }, []);

  // 연도 변경 시 데이터 로드
  useEffect(() => {
    if (selectedYear && threshold !== undefined && city) {
      fetchInfrastructureData();
    }
  }, [selectedYear, threshold, city]);

  // 외부에서 year prop이 변경되면 내부 상태도 업데이트
  useEffect(() => {
    if (year && year !== selectedYear) {
      setSelectedYear(year);
    }
  }, [year, selectedYear]);

  const fetchInfrastructureData = async () => {
    setLoading(true);
    setError(null);
    try {
      // Get city coordinates
      const cityData = await getCityCoordinates(city);
      const lat = cityData.lat;
      const lng = cityData.lng;
      
      // Update map center to the selected city
      setMapCenter([lat, lng]);
      
      // Create bounding box around the city
      const buffer = 0.25; // degrees
      const minLat = lat - buffer;
      const minLng = lng - buffer;
      const maxLat = lat + buffer;
      const maxLng = lng + buffer;
      
      // Update city bounds for map display
      const newBounds = [
        [minLat, minLng], // Southwest
        [maxLat, maxLng]  // Northeast
      ];
      setCityBounds(newBounds);
      
      const response = await fetch(`http://localhost:8000/analysis/infrastructure-exposure?year=${selectedYear}&threshold=${threshold}&min_lat=${minLat}&min_lon=${minLng}&max_lat=${maxLat}&max_lon=${maxLng}`);
      if (!response.ok) {
        throw new Error('Failed to fetch infrastructure data');
      }
      const result = await response.json();
      setData(result);
    } catch (err) {
      setError(err.message);
      // Fallback to Jakarta coordinates
      setCityBounds(JAKARTA_BOUNDS);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div style={{ padding: '2rem', textAlign: 'center' }}>
        <div>Loading infrastructure exposure analysis...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div style={{ padding: '2rem', textAlign: 'center', color: 'red' }}>
        <div>Error: {error}</div>
      </div>
    );
  }

  if (!data) {
    return (
      <div style={{ padding: '2rem', textAlign: 'center' }}>
        <div>Select parameters and click "Analyze it" to view infrastructure exposure</div>
      </div>
    );
  }

  const { infrastructure_data, statistics, map_url } = data;

  const columns = [
    { field: 'name', headerName: 'Infrastructure Name', width: 220 },
    { field: 'type', headerName: 'Type', width: 160 },
    { field: 'lon', headerName: 'Longitude', width: 120, type: 'number' },
    { field: 'lat', headerName: 'Latitude', width: 120, type: 'number' },
    { field: 'at_risk', headerName: 'Status', width: 120, renderCell: (params) => (
        <span style={{ color: params.value ? '#d32f2f' : '#2e7d32', fontWeight: 'bold' }}>
          {params.value ? 'At Risk' : 'Safe'}
        </span>
      )
    }
  ];

  const handleYearChange = (e) => {
    const newYear = Number(e.target.value);
    setSelectedYear(newYear);
    if (onYearChange) {
      onYearChange(newYear);
    }
  };

  return (
    <div style={{ padding: '2rem' }}>
      <h2>Infrastructure Exposure Analysis</h2>
      
      {/* 연도 선택기 */}
      <div style={{ marginBottom: 24, padding: 16, background: '#f5f5f5', borderRadius: 8 }}>
        <h4 style={{ margin: '0 0 12px 0' }}>분석 연도 선택</h4>
        <div style={{ display: 'flex', gap: 16, alignItems: 'center', marginBottom: 8 }}>
          <div>
            <label style={{ display: 'block', marginBottom: 4, fontSize: 14 }}>연도:</label>
            <select 
              value={selectedYear} 
              onChange={handleYearChange} 
              style={{ width: '120px', padding: '8px' }}
              dangerouslySetInnerHTML={{ __html: yearOptions.options }}
            />
          </div>
          <div>
            <label style={{ display: 'block', marginBottom: 4, fontSize: 14 }}>해수면 임계값:</label>
            <span style={{ fontSize: 16, fontWeight: 'bold' }}>{threshold}m</span>
          </div>
        </div>
        <div style={{ fontSize: 12, color: '#666' }}>
          {getYearRangeText('infrastructure-exposure')}
        </div>
        <div style={{ fontSize: 12, color: '#888' }}>
          {getDataSourceText('infrastructure-exposure')}
        </div>
      </div>
      
      {/* Statistics Summary */}
      <div style={{ 
        display: 'grid', 
        gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', 
        gap: '1rem', 
        marginBottom: '2rem' 
      }}>
        <div style={{ 
          padding: '1rem', 
          background: '#f5f5f5', 
          borderRadius: '8px', 
          textAlign: 'center' 
        }}>
          <h3>{statistics.total_infrastructure}</h3>
          <p>Total Infrastructure</p>
        </div>
        <div style={{ 
          padding: '1rem', 
          background: '#ffebee', 
          borderRadius: '8px', 
          textAlign: 'center' 
        }}>
          <h3 style={{ color: '#d32f2f' }}>{statistics.at_risk_infrastructure}</h3>
          <p>At Risk</p>
        </div>
        <div style={{ 
          padding: '1rem', 
          background: '#e8f5e8', 
          borderRadius: '8px', 
          textAlign: 'center' 
        }}>
          <h3 style={{ color: '#2e7d32' }}>{statistics.total_infrastructure - statistics.at_risk_infrastructure}</h3>
          <p>Safe</p>
        </div>
        <div style={{ 
          padding: '1rem', 
          background: '#fff3e0', 
          borderRadius: '8px', 
          textAlign: 'center' 
        }}>
          <h3 style={{ color: '#f57c00' }}>{statistics.risk_percentage.toFixed(1)}%</h3>
          <p>Risk Percentage</p>
        </div>
      </div>

      {/* Map and Table Layout */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '2rem', marginBottom: '2rem' }}>
        {/* Map */}
        <div>
          <h3>Infrastructure Map</h3>
          <div style={{ height: '400px', border: '1px solid #ddd', borderRadius: '8px', overflow: 'hidden' }}>
            <MapContainer
              key={mapCenter ? `${mapCenter[0]}-${mapCenter[1]}` : 'default'}
              center={mapCenter || [-6.1754, 106.8272]}
              zoom={10}
              style={{ height: '100%', width: '100%' }}
            >
              <TileLayer
                url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
                attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
              />
              {/* Risk area overlay */}
              {map_url && (
                <ImageOverlay
                  url={map_url}
                  bounds={cityBounds}
                  opacity={0.5}
                />
              )}
              {infrastructure_data.map((infra, index) => (
                <CircleMarker
                  key={index}
                  center={[infra.lat, infra.lon]}
                  radius={infra.at_risk ? 8 : 6}
                  fillColor={infra.at_risk ? '#ff4444' : '#44ff44'}
                  color={infra.at_risk ? '#cc0000' : '#00cc00'}
                  weight={2}
                  opacity={1}
                  fillOpacity={0.7}
                >
                  <Popup>
                    <div>
                      <strong>{infra.name}</strong><br />
                      Type: {infra.type}<br />
                      Status: {infra.at_risk ? 'At Risk' : 'Safe'}<br />
                      Coordinates: {infra.lat.toFixed(4)}, {infra.lon.toFixed(4)}
                    </div>
                  </Popup>
                </CircleMarker>
              ))}
            </MapContainer>
          </div>
        </div>

        {/* Infrastructure by Type */}
        <div>
          <h3>Infrastructure by Type</h3>
          <div style={{ background: '#f9f9f9', padding: '1rem', borderRadius: '8px' }}>
            {Object.entries(statistics.by_type).map(([type, counts]) => (
              <div key={type} style={{ 
                display: 'flex', 
                justifyContent: 'space-between', 
                alignItems: 'center',
                padding: '0.5rem 0',
                borderBottom: '1px solid #eee'
              }}>
                <span style={{ fontWeight: 'bold' }}>{type}</span>
                <div style={{ display: 'flex', gap: '1rem' }}>
                  <span style={{ color: '#d32f2f' }}>{counts.at_risk} at risk</span>
                  <span style={{ color: '#2e7d32' }}>{counts.total - counts.at_risk} safe</span>
                  <span style={{ color: '#666' }}>({counts.total} total)</span>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Infrastructure Table */}
      <div>
        <h3>Infrastructure Details</h3>
        <div style={{ height: 500, width: '100%' }}>
          <DataGrid
            rows={infrastructure_data.map((row, idx) => ({ id: idx, ...row }))}
            columns={columns}
            pageSize={10}
            rowsPerPageOptions={[10, 25, 50, 100]}
            checkboxSelection={false}
            disableSelectionOnClick
            sortingOrder={['asc', 'desc']}
            filterMode="client"
            sx={{ background: 'white', borderRadius: 2 }}
          />
        </div>
      </div>
    </div>
  );
};

export default InfrastructureExposure; 