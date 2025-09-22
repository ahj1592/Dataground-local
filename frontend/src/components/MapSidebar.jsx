import React, { useState, useEffect } from 'react';
import { getCountries, getCitiesByCountry } from '../api';

const TASKS = [
  { value: 'slr-risk', label: 'Sea-Level Rise Risk', years: 1, minYear: 2014, maxYear: 2024 },
  { value: 'urban-area-comprehensive', label: 'Urban Area Comprehensive', years: 2, minYear: 2001, maxYear: 2020 },
  { value: 'infrastructure-exposure', label: 'Infrastructure Exposure', years: 1, minYear: 2001, maxYear: 2020 },
  { value: 'topic-modeling', label: 'Topic Modeling', years: 0, minYear: 0, maxYear: 0 },
];

function MapSidebar({ onAnalyze, initialParams = null }) {
  const [task, setTask] = useState(TASKS[0].value);
  const [year1, setYear1] = useState(2020);
  const [year2, setYear2] = useState(2020);
  const [threshold, setThreshold] = useState(2.0);
  
  // Location selection state
  const [countries, setCountries] = useState([]);
  const [cities, setCities] = useState([]);
  const [selectedCountry, setSelectedCountry] = useState('');
  const [selectedCity, setSelectedCity] = useState('');
  const [loadingCountries, setLoadingCountries] = useState(true);
  const [loadingCities, setLoadingCities] = useState(false);
  
  // Topic modeling specific state
  const [method, setMethod] = useState('lda');
  const [nTopics, setNTopics] = useState(10);
  const [minDf, setMinDf] = useState(2.0);
  const [maxDf, setMaxDf] = useState(0.95);
  const [ngramRange, setNgramRange] = useState('1,1');
  const [textInput, setTextInput] = useState('');
  const [selectedFiles, setSelectedFiles] = useState([]);
  const [inputType, setInputType] = useState('text'); // 'text' or 'files'

  const selectedTask = TASKS.find(t => t.value === task);
  const minYear = selectedTask.minYear;
  const maxYear = selectedTask.maxYear;

  // Load countries on component mount
  useEffect(() => {
    const loadCountries = async () => {
      try {
        setLoadingCountries(true);
        const countriesData = await getCountries();
        setCountries(countriesData);
        setLoadingCountries(false);
        
        // Set first country as default
        if (countriesData.length > 0) {
          setSelectedCountry(countriesData[0]);
        }
      } catch (error) {
        console.error('Error loading countries:', error);
        setLoadingCountries(false);
      }
    };
    loadCountries();
  }, []);

  // Handle initial parameters from ADK
  useEffect(() => {
    if (initialParams) {
      console.log('🔧 [MapSidebar] Setting initial parameters from ADK:', initialParams);
      
      // Set task
      if (initialParams.task) {
        setTask(initialParams.task);
      }
      
      // Set year
      if (initialParams.year1) {
        setYear1(parseInt(initialParams.year1));
      }
      
      // Set threshold
      if (initialParams.threshold) {
        setThreshold(parseFloat(initialParams.threshold));
      }
      
      // Set country
      if (initialParams.country) {
        setSelectedCountry(initialParams.country);
      }
      
      // Set city
      if (initialParams.city) {
        setSelectedCity(initialParams.city);
      }
    }
  }, [initialParams]);

  // Load cities when country changes
  useEffect(() => {
    const loadCities = async () => {
      if (!selectedCountry) return;
      
      try {
        setLoadingCities(true);
        const citiesData = await getCitiesByCountry(selectedCountry);
        setCities(citiesData);
        setLoadingCities(false);
        
        // Reset selected city when country changes
        if (citiesData.length > 0) {
          setSelectedCity(citiesData[0].city);
        }
      } catch (error) {
        console.error('Error loading cities:', error);
        setLoadingCities(false);
      }
    };
    loadCities();
  }, [selectedCountry]);

  const handleAnalyze = () => {
    if (task === 'topic-modeling') {
      const params = {
        country: selectedCountry,
        city: selectedCity,
        task,
        method,
        minDf,
        maxDf,
        ngramRange,
        textInput: inputType === 'text' ? textInput : null,
        files: inputType === 'files' ? selectedFiles : null,
        inputType
      };
      
      // Only include nTopics for LDA method
      if (method === 'lda') {
        params.nTopics = nTopics;
      }
      
      console.log('MapSidebar - topic modeling params:', params);
      onAnalyze(params);
    } else {
      const params = {
        country: selectedCountry,
        city: selectedCity,
        task,
        year1,
        year2: selectedTask.years === 2 ? year2 : null,
        mapOption: 'OpenStreetMap',
        threshold,
      };
      
      console.log('MapSidebar - geospatial params:', params);
      onAnalyze(params);
    }
  };

  const handleFileSelect = (e) => {
    setSelectedFiles(Array.from(e.target.files));
  };

  return (
    <div style={{ width: 300, padding: 20, borderRight: '1px solid #eee', background: '#fafbfc', minHeight: '100vh' }}>
      <h3>Select Analysis Type:</h3>
      <select value={task} onChange={e => setTask(e.target.value)} style={{ width: '100%', marginBottom: 16 }}>
        {TASKS.map(t => (
          <option key={t.value} value={t.value}>{t.label}</option>
        ))}
      </select>

      {task === 'topic-modeling' ? (
        // Topic Modeling Configuration
        <div>
          <h4>Method</h4>
          <select value={method} onChange={e => setMethod(e.target.value)} style={{ width: '100%', marginBottom: 16 }}>
            <option value="lda">LDA (requires topic count)</option>
            <option value="bertopic">BERTopic (multiple documents required)</option>
          </select>

          {method === 'lda' && (
            <>
              <h4>Number of Topics</h4>
              <input 
                type="number" 
                value={nTopics} 
                onChange={e => setNTopics(Number(e.target.value))} 
                min={2} 
                max={50} 
                style={{ width: '100%', marginBottom: 16 }} 
              />
            </>
          )}

          {method === 'bertopic' && (
            <div style={{ 
              padding: 12, 
              backgroundColor: '#fff3cd', 
              border: '1px solid #ffeaa7', 
              borderRadius: 4, 
              marginBottom: 16,
              fontSize: 14,
              color: '#856404'
            }}>
              <strong>📊 Auto Topic Detection</strong><br/>
              BERTopic will automatically determine the optimal number of topics. 
              Works best with multiple documents but can handle small datasets.
            </div>
          )}

          <h4>Min DF</h4>
          <input 
            type="number" 
            value={minDf} 
            onChange={e => setMinDf(Number(e.target.value))} 
            min={1} 
            max={10} 
            step={0.5}
            style={{ width: '100%', marginBottom: 16 }} 
          />

          <h4>Max DF</h4>
          <input 
            type="range"
            min={0.1}
            max={1.0}
            step={0.05}
            value={maxDf}
            onChange={e => setMaxDf(Number(e.target.value))}
            style={{ width: '100%', marginBottom: 16 }}
          />
          <div style={{ textAlign: 'right', fontSize: 14 }}>{maxDf.toFixed(2)}</div>

          <h4>N-gram Range</h4>
          <select value={ngramRange} onChange={e => setNgramRange(e.target.value)} style={{ width: '100%', marginBottom: 16 }}>
            <option value="1,1">Unigrams (1,1)</option>
            <option value="1,2">Bigrams (1,2)</option>
            <option value="1,3">Trigrams (1,3)</option>
            <option value="2,2">Bigrams only (2,2)</option>
          </select>

          <h4>Input Type</h4>
          <div style={{ marginBottom: 16 }}>
            <label style={{ marginRight: 16 }}>
              <input 
                type="radio" 
                value="text" 
                checked={inputType === 'text'} 
                onChange={e => setInputType(e.target.value)}
              />
              Type Text
            </label>
            <label>
              <input 
                type="radio" 
                value="files" 
                checked={inputType === 'files'} 
                onChange={e => setInputType(e.target.value)}
              />
              Upload Files
            </label>
          </div>

          {inputType === 'text' && (
            <div>
              <h4>Text Input</h4>
              <textarea 
                value={textInput} 
                onChange={e => setTextInput(e.target.value)} 
                placeholder="Enter your text here..."
                style={{ width: '100%', height: 100, marginBottom: 16, padding: 8 }}
              />
            </div>
          )}

          {inputType === 'files' && (
            <div>
              <h4>Upload Files</h4>
              <input 
                type="file" 
                multiple 
                accept=".txt,.docx,.pdf,.csv"
                onChange={handleFileSelect}
                style={{ width: '100%', marginBottom: 16 }} 
              />
              {selectedFiles.length > 0 && (
                <div style={{ fontSize: 12, color: '#666', marginBottom: 16 }}>
                  Selected: {selectedFiles.map(f => f.name).join(', ')}
                </div>
              )}
            </div>
          )}
        </div>
      ) : (
        // Existing geospatial analysis configuration
        <div>
          <h4>Country</h4>
          <select 
            value={selectedCountry} 
            onChange={e => setSelectedCountry(e.target.value)} 
            disabled={loadingCountries}
            style={{ width: '100%', marginBottom: 16 }}
          >
            {loadingCountries ? (
              <option>Loading countries...</option>
            ) : (
              countries.map(country => (
                <option key={country} value={country}>{country}</option>
              ))
            )}
          </select>
          
          <h4>City</h4>
          <select 
            value={selectedCity} 
            onChange={e => setSelectedCity(e.target.value)} 
            disabled={loadingCities || cities.length === 0}
            style={{ width: '100%', marginBottom: 16 }}
          >
            {loadingCities ? (
              <option>Loading cities...</option>
            ) : cities.length === 0 ? (
              <option>No cities available</option>
            ) : (
              cities.map(city => (
                <option key={city.city} value={city.city_ascii}>{city.city_ascii}</option>
              ))
            )}
          </select>
          <h4>Time Period</h4>
          {selectedTask.years === 1 ? (
            <div>
              <label>Year: </label>
              <input type="number" value={year1} onChange={e => setYear1(Number(e.target.value))} min={minYear} max={maxYear} style={{ width: 100 }} />
            </div>
          ) : (
            <div>
              <label>Start Year: </label>
              <input type="number" value={year1} onChange={e => setYear1(Number(e.target.value))} min={minYear} max={maxYear} style={{ width: 100 }} />
              <br />
              <label>End Year: </label>
              <input type="number" value={year2} onChange={e => setYear2(Number(e.target.value))} min={minYear} max={maxYear} style={{ width: 100 }} />
            </div>
          )}
          <h4 style={{ marginTop: 24 }}>Sea Level Threshold (m)</h4>
          <input
            type="range"
            min={0.0}
            max={5.0}
            step={0.1}
            value={threshold}
            onChange={e => setThreshold(Number(e.target.value))}
            style={{ width: '100%' }}
          />
          <div style={{ textAlign: 'right', fontSize: 14 }}>{threshold.toFixed(1)} m</div>
          <h4 style={{ marginTop: 24 }}>Map Option</h4>
          <select disabled style={{ width: '100%', marginBottom: 16 }}><option>OpenStreetMap</option></select>
        </div>
      )}

      <button style={{ marginTop: 20, width: '100%', padding: '10px', fontWeight: 'bold', background: '#1976d2', color: 'white', border: 'none', borderRadius: 4, cursor: 'pointer' }} onClick={handleAnalyze}>
        Analyze it
      </button>
    </div>
  );
}

export default MapSidebar; 