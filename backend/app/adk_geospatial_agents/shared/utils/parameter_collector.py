"""
ADK Parameter Collection Utility
"""

import re
from typing import Dict, Any, List, Optional
from .location_matcher import location_matcher

class ParameterCollector:
    """Utility class for collecting parameters needed for analysis"""
    
    def __init__(self):
        # Define required parameters and collection order for each task
        self.required_params = {
            "sea_level_rise": ["country_name", "city_name", "year", "threshold"],
            "urban_analysis": ["country_name", "city_name", "start_year", "end_year", "threshold"],
            "infrastructure_analysis": ["country_name", "city_name", "year", "threshold"],
            "topic_modeling": ["method", "n_topics"]
        }
        
        # Parameter question templates for each task
        self.parameter_questions = {
            "sea_level_rise": {
                "country_name": "Which country would you like to analyze? (e.g., South Korea, United States)",
                "city_name": "Which city would you like to analyze? (e.g., Seoul, Busan, New York)",
                "year": "What year would you like to analyze? (2001-2020) (e.g., 2020, 2018)",
                "threshold": "Please set the sea level rise threshold (e.g., 2.0m, 1.5m)"
            },
            "urban_analysis": {
                "country_name": "Which country would you like to analyze? (e.g., South Korea, United States)",
                "city_name": "Which city would you like to analyze? (e.g., Seoul, Busan, New York)",
                "start_year": "Please enter the start year (2001-2020) (e.g., 2014, 2015)",
                "end_year": "Please enter the end year (2001-2020) (e.g., 2020, 2019)",
                "threshold": "Please set the sea level rise threshold (e.g., 2.0m, 1.5m)"
            },
            "infrastructure_analysis": {
                "country_name": "Which country would you like to analyze? (e.g., South Korea, United States)",
                "city_name": "Which city would you like to analyze? (e.g., Seoul, Busan, New York)",
                "year": "What year would you like to analyze? (2001-2020) (e.g., 2020, 2018)",
                "threshold": "Please set the sea level rise threshold (e.g., 2.0m, 1.5m)"
            },
            "topic_modeling": {
                "method": "Which method would you like to use? (lda, nmf, bertopic)",
                "n_topics": "How many topics would you like to analyze? (e.g., 10, 15)"
            }
        }
        
        self.valid_years = list(range(2000, 2025))
        self.valid_thresholds = (0.5, 5.0)
    
    async def _extract_parameters(self, message: str, analysis_type: str, existing_params: Dict[str, Any] = None) -> Dict[str, Any]:
        """Extract parameters from user message"""
        extracted = {}
        message_lower = message.lower()
        
        # Extract year
        year_patterns = [
            r'(\d{4})',
            r'year\s*:?\s*(\d{4})',
            r'in\s+(\d{4})',
            r'(\d{4})\s*year',
            r'(\d{4})\s*년'  # Korean "년" pattern added
        ]
        
        # Extract year for each analysis type
        if analysis_type == "urban_analysis":
            # urban_analysis collects start_year and end_year individually
            # Year range patterns (e.g., "2014-2020", "2014 to 2020", "2014부터 2020까지")
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
                        print(f"🔍 [ParameterCollector] Urban analysis range: start_year={start_year}, end_year={end_year}")
                        break
            
            # Extract individual year (when only start_year or end_year is present)
            if 'start_year' not in extracted and 'end_year' not in extracted:
                for pattern in year_patterns:
                    match = re.search(pattern, message_lower)
                    if match:
                        year = int(match.group(1))
                        if year in self.valid_years:
                            # If start_year exists, set as end_year; otherwise set as start_year
                            if 'start_year' in existing_params:
                                extracted['end_year'] = year
                                print(f"🔍 [ParameterCollector] Urban analysis: extracted end_year={year}")
                            else:
                                extracted['start_year'] = year
                                print(f"🔍 [ParameterCollector] Urban analysis: extracted start_year={year}")
                            break
        else:
            # Extract year for other analysis types
            for pattern in year_patterns:
                match = re.search(pattern, message_lower)
                if match:
                    year = int(match.group(1))
                    if year in self.valid_years:
                        extracted['year'] = year
                        break
        
        # Extract threshold
        threshold_patterns = [
            r'(\d+(?:\.\d+)?)\s*(?:meter|m|meters|미터)', # Korean "미터" pattern added
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
        
        # Extract location information (city/country)
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
        
        # Topic modeling parameters
        if analysis_type == "topic_modeling":
            # Extract method
            method_patterns = [
                r'\b(lda|nmf|bertopic)\b',
                r'method\s*:?\s*(lda|nmf|bertopic)'
            ]
            for pattern in method_patterns:
                match = re.search(pattern, message_lower)
                if match:
                    extracted['method'] = match.group(1)
                    break
            
            # Extract number of topics
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
    
    def _validate_parameters(self, params: Dict[str, Any], analysis_type: str) -> Dict[str, Any]:
        """Validate parameters"""
        required = self.required_params.get(analysis_type, [])
        missing = []
        invalid = []
        
        for param in required:
            if param not in params or params[param] is None:
                missing.append(param)
            elif param == "year" and params[param] not in self.valid_years:
                invalid.append(f"year must be between 2000-2024, got {params[param]}")
            elif param == "start_year" and params[param] not in self.valid_years:
                invalid.append(f"start_year must be between 2000-2024, got {params[param]}")
            elif param == "end_year" and params[param] not in self.valid_years:
                invalid.append(f"end_year must be between 2000-2024, got {params[param]}")
            elif param == "threshold" and not (self.valid_thresholds[0] <= params[param] <= self.valid_thresholds[1]):
                invalid.append(f"threshold must be between {self.valid_thresholds[0]}-{self.valid_thresholds[1]}, got {params[param]}")
        
        # For urban_analysis, validate start_year <= end_year
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
        """Generate questions for missing parameters"""
        if missing_params and analysis_type in self.parameter_questions:
            missing_param = missing_params[0]
            if missing_param in self.parameter_questions[analysis_type]:
                return self.parameter_questions[analysis_type][missing_param]
        
        # Default questions
        questions = {
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
            return questions.get(missing_params[0], f"Please provide {missing_params[0]} information.")
        return "Additional information is needed."

# Create global instance
parameter_collector = ParameterCollector()
