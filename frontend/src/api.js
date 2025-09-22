import axios from 'axios';

const API_BASE = 'http://localhost:8000';

// Add request interceptor for debugging
axios.interceptors.request.use(
  (config) => {
    console.log('API Request:', config.method?.toUpperCase(), config.url, config.headers);
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Add response interceptor for debugging
axios.interceptors.response.use(
  (response) => {
    console.log('API Response:', response.status, response.config.url);
    return response;
  },
  (error) => {
    console.error('API Error:', error.response?.status, error.response?.data, error.config?.url);
    return Promise.reject(error);
  }
);

export const login = async (email, password) => {
  const res = await axios.post(`${API_BASE}/auth/login`, { email, password });
  return res.data.access_token;
};

export const signup = async (user_name, email, password, confirm_password) => {
  const res = await axios.post(`${API_BASE}/auth/signup`, { user_name, email, password, confirm_password });
  return res.data;
};

export const getChats = async (token) => {
  const res = await axios.get(`${API_BASE}/chat/chats`, { headers: { Authorization: `Bearer ${token}` } });
  return res.data;
};

export const createChat = async (title, token) => {
  const res = await axios.post(`${API_BASE}/chat/chats`, null, { params: { title }, headers: { Authorization: `Bearer ${token}` } });
  return res.data;
};

export const getMessages = async (chatId, token) => {
  const res = await axios.get(`${API_BASE}/chat/chats/${chatId}/messages`, { headers: { Authorization: `Bearer ${token}` } });
  return res.data;
};

export const sendMessage = async (chatId, content, token) => {
  const res = await axios.post(`${API_BASE}/chat/chats/${chatId}/messages`, null, { params: { content }, headers: { Authorization: `Bearer ${token}` } });
  return res.data;
};

export const uploadFile = async (file, token) => {
  const formData = new FormData();
  formData.append('file', file);
  const res = await axios.post(`${API_BASE}/files/upload`, formData, { headers: { Authorization: `Bearer ${token}`, 'Content-Type': 'multipart/form-data' } });
  return res.data;
};

export const getMe = async (token) => {
  const res = await axios.get(`${API_BASE}/auth/me`, { headers: { Authorization: `Bearer ${token}` } });
  return res.data;
};

export const updateChatTitle = async (chatId, title, token) => {
  const res = await axios.patch(`${API_BASE}/chat/chats/${chatId}/title`, { title }, { headers: { Authorization: `Bearer ${token}` } });
  return res.data;
};

export const createChatWithFirstMessage = async (title, content, token) => {
  const res = await axios.post(`${API_BASE}/chat/chats/first`, { title, content }, { headers: { Authorization: `Bearer ${token}` } });
  return res.data;
};

export const generateAIResponse = async (chatId, token) => {
  const res = await axios.post(`${API_BASE}/chat/chats/${chatId}/ai_response`, null, { headers: { Authorization: `Bearer ${token}` } });
  return res.data;
};

// Location API functions
export const getCountries = async () => {
  const res = await axios.get(`${API_BASE}/location/countries`);
  return res.data;
};

export const getCitiesByCountry = async (country) => {
  const res = await axios.get(`${API_BASE}/location/cities/${encodeURIComponent(country)}`);
  return res.data;
};

export const getAllCities = async () => {
  const res = await axios.get(`${API_BASE}/location/cities`);
  return res.data;
};

export const getCityCoordinates = async (cityAscii) => {
  const res = await axios.get(`${API_BASE}/location/city-coordinates/${encodeURIComponent(cityAscii)}`);
  return res.data;
};
