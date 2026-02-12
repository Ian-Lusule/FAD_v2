"""
Module for fetching app details and reviews from Google Play Store.
Adapted from original Streamlit version.
"""

from google_play_scraper import app, reviews, Sort, search
import pandas as pd
from typing import Dict, List, Optional
import logging

logger = logging.getLogger(__name__)

def fetch_app_details(app_id: str, country: str) -> Optional[Dict]:
    """
    Fetches details for a given app ID from Google Play Store.

    Args:
        app_id (str): The ID of the app (e.g., 'com.example.app').
        country (str): The country code for the Play Store (e.g., 'us', 'ke').

    Returns:
        dict: A dictionary containing app details, or None if an error occurs.
    """
    try:
        return app(app_id, lang='en', country=country)
    except Exception as e:
        logger.error(f"Error fetching app details for {app_id}: {str(e)}")
        return None

def fetch_reviews(app_id: str, country: str, max_reviews: int = 200) -> List[Dict]:
    """
    Fetches a specified maximum number of reviews for a given app ID.

    Args:
        app_id (str): The ID of the app.
        country (str): The country code for the Play Store.
        max_reviews (int): The maximum number of reviews to fetch.

    Returns:
        list: A list of review dictionaries.
    """
    try:
        all_reviews = []
        continuation_token = None
        
        # Fetch reviews in batches until max_reviews is reached or no more reviews
        while len(all_reviews) < max_reviews:
            count_to_fetch = min(200, max_reviews - len(all_reviews))  # Fetch up to 200 reviews per call
            if count_to_fetch <= 0:
                break

            result, new_token = reviews(
                app_id,
                lang='en',
                country=country,
                count=count_to_fetch,
                sort=Sort.NEWEST,  # Sort by newest reviews
                continuation_token=continuation_token
            )
            all_reviews.extend(result)
            
            if not new_token or len(result) < count_to_fetch:  # Stop if no more token or fewer reviews than requested
                break
            continuation_token = new_token
        
        return all_reviews[:max_reviews]  # Return exactly max_reviews or fewer if not available
    except Exception as e:
        logger.error(f"Error fetching reviews for {app_id}: {str(e)}")
        return []

def search_apps(query: str, country: str = 'us', limit: int = 10) -> List[Dict]:
    """
    Search for apps on Google Play Store.
    
    Args:
        query (str): Search query (app name).
        country (str): Country code.
        limit (int): Maximum number of results to return.
        
    Returns:
        List[Dict]: List of app search results.
    """
    try:
        results = search(query, lang='en', country=country, n_hits=limit)
        return results
    except Exception as e:
        logger.error(f"Error searching for apps with query '{query}': {str(e)}")
        return []

def fetch_multiple_apps(app_ids: List[str], country: str) -> Dict[str, Optional[Dict]]:
    """
    Fetches details for multiple apps.
    
    Args:
        app_ids (List[str]): List of app IDs.
        country (str): Country code.
        
    Returns:
        Dict[str, Optional[Dict]]: Dictionary mapping app_id to app details.
    """
    results = {}
    for app_id in app_ids:
        results[app_id] = fetch_app_details(app_id, country)
    return results