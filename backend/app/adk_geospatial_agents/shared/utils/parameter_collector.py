"""
ADK Parameter Collection Utility - Strategy Pattern Implementation
"""

import re
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from .location_matcher import location_matcher

class ParameterExtractionStrategy(ABC):
    """Base strategy for parameter extraction"""
    
    @abstractmethod
    async def extract(self, message: str, existing_params: Dict[str, Any]) -> Dict[str, Any]:
        """Extract parameters from message"""
        pass
    
    @abstractmethod
    def get_required_params(self) -> List[str]:
        """Get list of required parameters for this analysis type"""
        pass
    
    @abstractmethod
    def get_parameter_questions(self) -> Dict[str, str]:
        """Get parameter questions for this analysis type"""
        pass

class LocationBasedStrategy(ParameterExtractionStrategy):
    """Strategy for analyses requiring location data (sea level, urban, infrastructure)"""
    
    def __init__(self, analysis_type: str):
        self.analysis_type = analysis_type
        self.valid_years = list(range(2000, 2025))
        self.valid_thresholds = (0.5, 5.0)
    
    async def extract(self, message: str, existing_params: Dict[str, Any]) -> Dict[str, Any]:
        """Extract parameters for location-based analyses"""
        extracted = {}
        message_lower = message.lower()
        
        # Extract location information first
        extracted.update(await self._extract_location_info(message, existing_params))
        
        # Extract year parameters
        extracted.update(await self._extract_year_params(message_lower, existing_params))
        
        # Extract threshold
        extracted.update(await self._extract_threshold(message_lower))
        
        return extracted
    
    async def _extract_location_info(self, message: str, existing_params: Dict[str, Any]) -> Dict[str, Any]:
        """Extract location information (city/country)"""
        extracted = {}
        
        # Try city search first
        city_result = location_matcher.extract_location_from_message(message, "city")
        if city_result["found"]:
            if city_result.get("exact_match", False):
                extracted['city_name'] = city_result["city"]
                extracted['country_name'] = city_result["country"]
                extracted['coordinates'] = city_result["coordinates"]
                # Successfully found location, remove existing suggestions and errors
                if existing_params:
                    for key in ['location_error', 'suggestion_message', 'suggested_city', 'suggested_country']:
                        if key in existing_params:
                            del existing_params[key]
            else:
                # Suggest similar cities
                extracted['suggested_city'] = city_result.get("suggested_city")
                extracted['suggested_country'] = city_result.get("suggested_country")
                extracted['suggestion_message'] = city_result.get("message")
        else:
            # If city not found, try country search
            country_result = location_matcher.extract_location_from_message(message, "country")
            if country_result["found"]:
                if country_result.get("exact_match", False):
                    extracted['country_name'] = country_result["country"]
                    # Suggest major cities in that country
                    if country_result.get("cities"):
                        extracted['suggested_cities'] = country_result["cities"]
                    # Successfully found location, remove existing suggestions and errors
                    if existing_params:
                        for key in ['location_error', 'suggestion_message', 'suggested_city', 'suggested_country']:
                            if key in existing_params:
                                del existing_params[key]
                else:
                    # Suggest similar countries
                    extracted['suggested_country'] = country_result.get("suggested_country")
                    extracted['suggestion_message'] = country_result.get("message")
            else:
                # Location information not found
                extracted['location_error'] = "Location information not found."
        
        return extracted
    
    async def _extract_year_params(self, message_lower: str, existing_params: Dict[str, Any]) -> Dict[str, Any]:
        """Extract year parameters based on analysis type"""
        extracted = {}
        
        if self.analysis_type == "urban_analysis":
            # Extract year range for urban analysis
            range_patterns = [
                r'(\d{4})\s*[-~]\s*(\d{4})',
                r'(\d{4})\s+to\s+(\d{4})',
                r'(\d{4})\s+부터\s+(\d{4})\s+까지',
                r'from\s+(\d{4})\s+to\s+(\d{4})',
                r'(\d{4})\s*-\s*(\d{4})'
            ]
            
            for pattern in range_patterns:
                match = re.search(pattern, message_lower)
                if match:
                    start_year = int(match.group(1))
                    end_year = int(match.group(2))
                    if (start_year in self.valid_years and end_year in self.valid_years and 
                        start_year <= end_year):
                        extracted['start_year'] = start_year
                        extracted['end_year'] = end_year
                        break
            
            # Extract individual year if range not found
            if 'start_year' not in extracted and 'end_year' not in extracted:
                year_patterns = [r'(\d{4})', r'year\s*:?\s*(\d{4})', r'in\s+(\d{4})', r'(\d{4})\s*year', r'(\d{4})\s*년']
                for pattern in year_patterns:
                    match = re.search(pattern, message_lower)
                    if match:
                        year = int(match.group(1))
                        if year in self.valid_years:
                            if 'start_year' in existing_params:
                                extracted['end_year'] = year
                            else:
                                extracted['start_year'] = year
                            break
        else:
            # Extract single year for other analyses
            year_patterns = [r'(\d{4})', r'year\s*:?\s*(\d{4})', r'in\s+(\d{4})', r'(\d{4})\s*year', r'(\d{4})\s*년']
            for pattern in year_patterns:
                match = re.search(pattern, message_lower)
                if match:
                    year = int(match.group(1))
                    if year in self.valid_years:
                        extracted['year'] = year
                        break
        
        return extracted
    
    async def _extract_threshold(self, message_lower: str) -> Dict[str, Any]:
        """Extract threshold parameter"""
        extracted = {}
        
        threshold_patterns = [
            r'(\d+(?:\.\d+)?)\s*(?:meter|m|meters|미터)',
            r'threshold\s*:?\s*(\d+(?:\.\d+)?)',
            r'(\d+(?:\.\d+)?)\s*m\s*threshold'
        ]
        
        for pattern in threshold_patterns:
            match = re.search(pattern, message_lower)
            if match:
                threshold = float(match.group(1))
                if self.valid_thresholds[0] <= threshold <= self.valid_thresholds[1]:
                    extracted['threshold'] = threshold
                    break
        
        return extracted
    
    def get_required_params(self) -> List[str]:
        """Get required parameters based on analysis type"""
        if self.analysis_type == "urban_analysis":
            return ["country_name", "city_name", "start_year", "end_year", "threshold"]
        else:
            return ["country_name", "city_name", "year", "threshold"]
    
    def get_parameter_questions(self) -> Dict[str, str]:
        """Get parameter questions based on analysis type"""
        base_questions = {
            "country_name": "Which country would you like to analyze? (e.g., South Korea, United States)",
            "city_name": "Which city would you like to analyze? (e.g., Seoul, Busan, New York)",
            "threshold": "Please set the sea level rise threshold (e.g., 2.0m, 1.5m)"
        }
        
        if self.analysis_type == "urban_analysis":
            base_questions.update({
                "start_year": "Please enter the start year (2001-2020) (e.g., 2014, 2015)",
                "end_year": "Please enter the end year (2001-2020) (e.g., 2020, 2019)"
            })
        else:
            base_questions["year"] = "What year would you like to analyze? (2001-2020) (e.g., 2020, 2018)"
        
        return base_questions

class TopicModelingStrategy(ParameterExtractionStrategy):
    """Strategy for topic modeling analysis"""
    
    async def extract(self, message: str, existing_params: Dict[str, Any]) -> Dict[str, Any]:
        """Extract parameters for topic modeling analysis (no location needed)"""
        extracted = {}
        message_lower = message.lower()
        
        # Extract method
        extracted.update(await self._extract_method(message_lower))
        
        # Extract number of topics
        extracted.update(await self._extract_n_topics(message_lower))
        
        return extracted
    
    async def _extract_method(self, message_lower: str) -> Dict[str, Any]:
        """Extract topic modeling method"""
        extracted = {}
        
        method_patterns = [
            r'\b(lda|nmf|bertopic)\b',
            r'method\s*:?\s*(lda|nmf|bertopic)'
        ]
        
        for pattern in method_patterns:
            match = re.search(pattern, message_lower)
            if match:
                extracted['method'] = match.group(1)
                break
        
        return extracted
    
    async def _extract_n_topics(self, message_lower: str) -> Dict[str, Any]:
        """Extract number of topics"""
        extracted = {}
        
        n_topics_patterns = [
            r'(\d+)\s*(?:topics|topic)',
            r'n_topics\s*:?\s*(\d+)'
        ]
        
        for pattern in n_topics_patterns:
            match = re.search(pattern, message_lower)
            if match:
                n_topics = int(match.group(1))
                if 2 <= n_topics <= 20:
                    extracted['n_topics'] = n_topics
                    break
        
        return extracted
    
    def get_required_params(self) -> List[str]:
        """Get required parameters for topic modeling"""
        return ["method", "n_topics"]
    
    def get_parameter_questions(self) -> Dict[str, str]:
        """Get parameter questions for topic modeling"""
        return {
            "method": "Which method would you like to use? (lda, nmf, bertopic)",
            "n_topics": "How many topics would you like to analyze? (e.g., 10, 15)"
        }

class ParameterCollector:
    """Main parameter collector using strategy pattern"""
    
    def __init__(self):
        # Initialize strategies for each analysis type
        self.strategies = {
            "sea_level_rise": LocationBasedStrategy("sea_level_rise"),
            "urban_analysis": LocationBasedStrategy("urban_analysis"),
            "infrastructure_analysis": LocationBasedStrategy("infrastructure_analysis"),
            "topic_modeling": TopicModelingStrategy(),
        }
    
    async def _extract_parameters(self, message: str, analysis_type: str, existing_params: Dict[str, Any] = None) -> Dict[str, Any]:
        """Extract parameters from user message using appropriate strategy"""
        if existing_params is None:
            existing_params = {}
        
        # Get the appropriate strategy
        strategy = self.strategies.get(analysis_type)
        if not strategy:
            raise ValueError(f"No strategy found for analysis type: {analysis_type}")
        
        # Extract parameters using the strategy
        extracted = await strategy.extract(message, existing_params)
        
        return extracted
    
    def _validate_parameters(self, params: Dict[str, Any], analysis_type: str) -> Dict[str, Any]:
        """Validate parameters using strategy's required params"""
        strategy = self.strategies.get(analysis_type)
        if not strategy:
            raise ValueError(f"No strategy found for analysis type: {analysis_type}")
        
        required = strategy.get_required_params()
        missing = []
        invalid = []
        
        for param in required:
            if param not in params or params[param] is None:
                missing.append(param)
            elif param == "year" and params[param] not in list(range(2000, 2025)):
                invalid.append(f"year must be between 2000-2024, got {params[param]}")
            elif param == "start_year" and params[param] not in list(range(2000, 2025)):
                invalid.append(f"start_year must be between 2000-2024, got {params[param]}")
            elif param == "end_year" and params[param] not in list(range(2000, 2025)):
                invalid.append(f"end_year must be between 2000-2024, got {params[param]}")
            elif param == "threshold" and not (0.5 <= params[param] <= 5.0):
                invalid.append(f"threshold must be between 0.5-5.0, got {params[param]}")
        
        # urban_analysis의 경우 start_year <= end_year 검증
        if analysis_type == "urban_analysis" and "start_year" in params and "end_year" in params:
            if params["start_year"] and params["end_year"] and params["start_year"] > params["end_year"]:
                invalid.append(f"start_year ({params['start_year']}) must be <= end_year ({params['end_year']})")
        
        # If location_error exists but both city_name and country_name are present, ignore location_error
        if 'location_error' in params and 'city_name' in params and 'country_name' in params:
            if 'location' in missing:
                missing.remove('location')
            if 'location_error' in missing:
                missing.remove('location_error')

        return {
            "valid": len(missing) == 0 and len(invalid) == 0,
            "missing": missing,
            "invalid": invalid,
            "params": params
        }
    
    def are_all_parameters_collected(self, params: Dict[str, Any], analysis_type: str) -> bool:
        """Check if all required parameters are collected"""
        validation = self._validate_parameters(params, analysis_type)
        return validation["valid"] and len(validation["missing"]) == 0

    async def collect_parameters(self, message: str, analysis_type: str, existing_params: Dict[str, Any] = None) -> Dict[str, Any]:
        """Main parameter collection method"""
        if existing_params is None:
            existing_params = {}
        
        # Newly extracted parameters
        extracted = await self._extract_parameters(message, analysis_type, existing_params)
        
        # Merge with existing parameters
        all_params = {**existing_params, **extracted}
        
        # Remove location_error if both city_name and country_name are present
        if ('location_error' in all_params and 
            'city_name' in all_params and 'country_name' in all_params and
            all_params['city_name'] and all_params['country_name']):
            del all_params['location_error']
        
        # Validate
        validation = self._validate_parameters(all_params, analysis_type)
        
        return {
            "params": all_params,
            "validation": validation,
            "needs_more_info": not validation["valid"]
        }
    
    def generate_questions(self, missing_params: List[str], analysis_type: str) -> str:
        """Generate questions for missing parameters using strategy"""
        strategy = self.strategies.get(analysis_type)
        if not strategy:
            return "Additional information is needed."
        
        questions = strategy.get_parameter_questions()
        
        if missing_params:
            missing_param = missing_params[0]
            if missing_param in questions:
                return questions[missing_param]
        
        # Default questions
        default_questions = {
            "year": "What year would you like to analyze? (2001-2020) (e.g., 2020, 2018)",
            "start_year": "Please enter the start year (2001-2020) (e.g., 2014, 2015)",
            "end_year": "Please enter the end year (2001-2020) (e.g., 2020, 2019)",
            "threshold": "Please set the sea level rise threshold (e.g., 1.0m, 2.5m)",
            "city_name": "Which city would you like to analyze? (e.g., Seoul, Busan, New York)",
            "country_name": "Which country would you like to analyze? (e.g., South Korea, United States)",
            "method": "Please select the topic modeling method (lda, nmf, bertopic)",
            "n_topics": "How many topics would you like to analyze? (e.g., 5, 10)"
        }
        
        if missing_params:
            return default_questions.get(missing_params[0], f"Please provide {missing_params[0]} information.")
        return "Additional information is needed."

# Create global instance
parameter_collector = ParameterCollector()