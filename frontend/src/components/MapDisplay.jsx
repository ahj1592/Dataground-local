import React, { useEffect, useState } from 'react';
import { MapContainer, TileLayer, ImageOverlay } from 'react-leaflet';
import { getCityCoordinates } from '../api';
import { calculateStandardBbox } from '../utils/bboxUtils';
import 'leaflet/dist/leaflet.css';

// Jakarta bounding box (SW and NE corners)
const JAKARTA_BOUNDS = [
  [-6.365, 106.689], // Southwest (lat, lng)
  [-6.089, 106.971], // Northeast (lat, lng)
];

function MapDisplay({ params }) {
  const [imgUrl, setImgUrl] = useState(null);
  const [cityBounds, setCityBounds] = useState(JAKARTA_BOUNDS);
  const [mapCenter, setMapCenter] = useState(null);

  console.log('🔍 [MapDisplay] Component rendered with params:', params);

  useEffect(() => {
    console.log('🔍 [MapDisplay] useEffect triggered, params:', params);
    if (!params) {
      console.log('❌ [MapDisplay] No params, returning');
      return;
    }
    
    // 매 분석 호출마다 모든 지도 상태 초기화
    console.log('🔄 [MapDisplay] Resetting all map states');
    setImgUrl(null);
    setMapCenter(null);
    setCityBounds(JAKARTA_BOUNDS);
    
    const loadAnalysis = async () => {
      try {
        console.log('🔍 [MapDisplay] loadAnalysis called with params:', params);
        
        // Handle chat-triggered updates
        if (params.type === 'chat_triggered' && params.updates) {
          console.log('🔍 [MapDisplay] processing chat-triggered updates:', params.updates);
          
          // Find map update from dashboard_updates
          const mapUpdate = params.updates.find(update => update.type === 'map_update');
          console.log('🔍 [MapDisplay] mapUpdate found:', mapUpdate);
          
          if (mapUpdate && mapUpdate.data) {
            console.log('🔍 [MapDisplay] map update data:', mapUpdate.data);
            
            // Set image URL from API response
            if (mapUpdate.data.image_url) {
              console.log('🔍 [MapDisplay] Setting image URL:', mapUpdate.data.image_url);
              setImgUrl(mapUpdate.data.image_url);
            }
            
            // Set map center and bounds from API response
            if (mapUpdate.data.center) {
              console.log('🔍 [MapDisplay] Setting map center:', mapUpdate.data.center);
              setMapCenter([mapUpdate.data.center[1], mapUpdate.data.center[0]]); // [lat, lng]
            }
            
            if (mapUpdate.data.bbox) {
              console.log('🔍 [MapDisplay] Setting city bounds:', mapUpdate.data.bbox);
              const [minLng, minLat, maxLng, maxLat] = mapUpdate.data.bbox;
              setCityBounds([
                [minLat, minLng], // Southwest
                [maxLat, maxLng]  // Northeast
              ]);
            }
          } else {
            console.log('❌ [MapDisplay] No map update found or no data');
          }
          return;
        }
        
        // Handle manual analysis (existing logic)
        console.log('MapDisplay - selected city:', params.city);
        
        // Get city coordinates
        const cityData = await getCityCoordinates(params.city);
        console.log('MapDisplay - city data:', cityData);
        const lat = cityData.lat;
        const lng = cityData.lng;
        
        // Update map center to the selected city
        setMapCenter([lat, lng]);
        console.log('MapDisplay - new map center:', [lat, lng]);
        
        // Create bounding box around the city using standard buffer
        const bbox = calculateStandardBbox(lat, lng, params.task);
        const newBounds = [
          [bbox.minLat, bbox.minLng], // Southwest
          [bbox.maxLat, bbox.maxLng]  // Northeast
        ];
        setCityBounds(newBounds);
        
        if (params.task === 'slr-risk') {
          const threshold = params.threshold !== undefined ? params.threshold : 2.0;
          const { minLat, minLng, maxLat, maxLng } = bbox;
          
          const response = await fetch(`http://localhost:8000/analysis/sea-level-rise?threshold=${threshold}&min_lat=${minLat}&min_lon=${minLng}&max_lat=${maxLat}&max_lon=${maxLng}`);
          const data = await response.json();
          setImgUrl(data.url);
        } else if (params.task === 'urban-area') {
          const year = params.year1;
          const bbox = calculateStandardBbox(lat, lng, params.task);
          const { minLat, minLng, maxLat, maxLng } = bbox;
          
          const response = await fetch(`http://localhost:8000/analysis/urban-area-map?year=${year}&min_lat=${minLat}&min_lon=${minLng}&max_lat=${maxLat}&max_lon=${maxLng}`);
          const data = await response.json();
          setImgUrl(data.url);
        } else if (params.task === 'urban-area-comprehensive') {
          const year = params.year2; // Use end year for the map display
          const threshold = params.threshold !== undefined ? params.threshold : 2.0;
          const bbox = calculateStandardBbox(lat, lng, params.task);
          const { minLat, minLng, maxLat, maxLng } = bbox;
          
          const response = await fetch(`http://localhost:8000/analysis/urban-area-risk-combined-map?year=${year}&threshold=${threshold}&min_lat=${minLat}&min_lon=${minLng}&max_lat=${maxLat}&max_lon=${maxLng}`);
          const data = await response.json();
          setImgUrl(data.url);
        }
      } catch (error) {
        console.error('Error loading analysis:', error);
        // Fallback to Jakarta coordinates if city not found
        setCityBounds(JAKARTA_BOUNDS);
        if (params.task === 'slr-risk') {
          const threshold = params.threshold !== undefined ? params.threshold : 2.0;
          fetch(`http://localhost:8000/analysis/sea-level-rise?threshold=${threshold}`)
            .then(res => res.json())
            .then(data => setImgUrl(data.url));
        }
      }
    };
    
    loadAnalysis();
    // Infrastructure exposure has its own map component, so we don't need to fetch a map here
  }, [params?.city, params?.task, params?.year1, params?.year2, params?.threshold]);

  if (!params) return <div>Please select options and click Analyze it.</div>;

  // Don't show map for infrastructure exposure as it has its own component
  if (params.task === 'infrastructure-exposure') {
    return null;
  }

  let title = '';
  if (params.task === 'slr-risk') title = 'Sea-Level Rise Risk Map';
  if (params.task === 'urban-area') title = 'Urban Area Map';
  if (params.task === 'urban-area-comprehensive') title = 'Urban Area & Risk Map';

  return (
    <div>
      <h2>{title}</h2>
      {params.task === 'urban-area-comprehensive' && (
        <div style={{ 
          background: '#f5f5f5', 
          padding: '10px', 
          borderRadius: '4px', 
          marginBottom: '10px',
          fontSize: '14px'
        }}>
          <strong>Legend:</strong> White = Non-urban, Pink = Urban areas, Red = Urban areas at risk from sea-level rise
        </div>
      )}
      <div style={{ height: 500, width: '100%' }}>
        <MapContainer
          key={`${params?.city}-${params?.task}-${params?.year1}-${params?.year2}-${params?.threshold}-${Date.now()}`}
          center={mapCenter || [-6.227, 106.83]}
          zoom={10}
          style={{ height: '100%', width: '100%' }}
          scrollWheelZoom={true}
        >
          <TileLayer
            url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
            attribution="&copy; OpenStreetMap contributors"
          />
          {imgUrl && (
            <ImageOverlay
              url={imgUrl}
              bounds={cityBounds}
              opacity={0.6}
            />
          )}
        </MapContainer>
        {!imgUrl && <p>Loading map...</p>}
      </div>
    </div>
  );
}

export default MapDisplay; 