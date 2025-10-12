// 연도 선택 유틸리티 함수들

// 데이터셋별 연도 범위 정의
export const yearRanges = {
  modis: {
    name: "MODIS 토지피복 데이터",
    years: Array.from({length: 20}, (_, i) => 2001 + i), // 2001-2020
    description: "도시화 지역 분석용",
    minYear: 2001,
    maxYear: 2020
  },
  worldpop: {
    name: "WorldPop 인구 데이터", 
    years: Array.from({length: 21}, (_, i) => 2000 + i), // 2000-2020
    description: "인구 노출도 분석용",
    minYear: 2000,
    maxYear: 2020
  },
  srtm: {
    name: "SRTM 고도 데이터",
    years: [2000],
    description: "해수면 상승 분석용 (고정)",
    minYear: 2000,
    maxYear: 2000
  }
};

// 분석 유형별 데이터셋 매핑
export const analysisDataMapping = {
  'slr-risk': 'srtm',
  'urban-area-comprehensive': 'modis',
  'infrastructure-exposure': 'modis',
  'urban-area-map': 'modis',
  'urban-area-stats': 'modis',
  'population-exposure-map': 'worldpop',
  'population-exposure-trend': 'worldpop'
};

// 연도 옵션 생성 함수
export function generateYearOptions(analysisType, reverseOrder = true) {
  const dataType = analysisDataMapping[analysisType];
  const yearData = yearRanges[dataType];
  
  if (!yearData) {
    return {
      options: '<option value="">연도 선택</option>',
      dataInfo: null
    };
  }
  
  let options = '<option value="">연도 선택</option>';
  const years = reverseOrder ? [...yearData.years].reverse() : yearData.years;
  
  years.forEach(year => {
    options += `<option value="${year}">${year}년</option>`;
  });
  
  return {
    options: options,
    dataInfo: yearData
  };
}

// 연도 유효성 검사 함수
export function validateYearInput(selectedYear, analysisType) {
  const dataType = analysisDataMapping[analysisType];
  const validYears = yearRanges[dataType]?.years || [];
  
  if (!validYears.includes(parseInt(selectedYear))) {
    const minYear = Math.min(...validYears);
    const maxYear = Math.max(...validYears);
    
    return {
      valid: false,
      message: `선택한 연도는 사용할 수 없습니다. ${minYear}년부터 ${maxYear}년 사이의 연도를 선택해주세요.`,
      suggestions: validYears.slice(-5) // 최근 5개 연도 제안
    };
  }
  
  return { valid: true };
}

// 자동 조정 함수
export function autoAdjustYear(year, analysisType) {
  const dataType = analysisDataMapping[analysisType];
  const yearData = yearRanges[dataType];
  
  if (!yearData) return year;
  
  const { minYear, maxYear } = yearData;
  
  if (year < minYear) return minYear;
  if (year > maxYear) return maxYear;
  return year;
}

// 연도 범위 텍스트 생성
export function getYearRangeText(analysisType) {
  const dataType = analysisDataMapping[analysisType];
  const yearData = yearRanges[dataType];
  
  if (!yearData) return "연도 정보 없음";
  
  return `사용 가능한 연도: ${yearData.minYear}년 - ${yearData.maxYear}년`;
}

// 데이터 소스 정보 텍스트 생성
export function getDataSourceText(analysisType) {
  const dataType = analysisDataMapping[analysisType];
  const yearData = yearRanges[dataType];
  
  if (!yearData) return "";
  
  return `${yearData.name} (${yearData.description})`;
}
