/**
 * Bounding Box 계산 유틸리티
 * 좌표와 buffer를 받아서 일관된 bbox를 생성합니다.
 */

/**
 * 좌표와 buffer를 받아서 bbox를 계산합니다.
 * @param {number} lat - 위도
 * @param {number} lng - 경도
 * @param {number} buffer - bbox 확장 정도 (degrees)
 * @returns {Object} bbox 파라미터 객체
 */
export function calculateBbox(lat, lng, buffer = 0.25) {
  return {
    minLat: lat - buffer,
    minLng: lng - buffer,
    maxLat: lat + buffer,
    maxLng: lng + buffer
  };
}

/**
 * 분석 타입에 따른 표준 buffer 크기를 반환합니다.
 * @param {string} analysisType - 분석 타입
 * @returns {number} 표준 buffer 크기 (degrees)
 */
export function getStandardBuffer(analysisType) {
  const bufferMap = {
    'slr-risk': 0.25,
    'sea_level_rise': 0.25,
    'urban-area': 0.25,
    'urban-area-comprehensive': 0.25,
    'infrastructure-exposure': 0.25,
    'topic-modeling': 0.25
  };
  
  return bufferMap[analysisType] || 0.25; // 기본값 0.25
}

/**
 * 좌표와 분석 타입을 받아서 표준 bbox를 계산합니다.
 * @param {number} lat - 위도
 * @param {number} lng - 경도
 * @param {string} analysisType - 분석 타입
 * @returns {Object} bbox 파라미터 객체
 */
export function calculateStandardBbox(lat, lng, analysisType) {
  const buffer = getStandardBuffer(analysisType);
  return calculateBbox(lat, lng, buffer);
}
