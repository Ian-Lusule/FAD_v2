"""
Module for sentiment analysis using TextBlob with negative keyword override.
Preserved from original Streamlit version.
"""

from textblob import TextBlob
import pandas as pd
from typing import Dict, Tuple, List  # Added List import here

# Define a list of words that should explicitly flag sentiment as negative
NEGATIVE_KEYWORDS = [
    "scam", "scum", "useless", "fraud", "fake", "deceptive", "ripoff",
    "unresponsive", "broken", "glitch", "buggy", "crash", "malware",
    "phishing", "steal", "stolen", "lie", "lying", "cheat", "cheating",
    "misleading", "unreliable", "waste of time", "terrible", "horrible",
    "worst", "bad experience", "do not install", "uninstall", "delete",
    "warning", "beware", "deceitful", "untrustworthy"
]

def analyze_sentiment(text: str) -> float:
    """
    Analyzes the sentiment polarity of a given text.
    Includes a check for explicit negative keywords to ensure strong negative flagging.

    Args:
        text (str): The input text.

    Returns:
        float: The sentiment polarity, ranging from -1.0 (negative) to 1.0 (positive).
               Returns 0 if the input is not a string.
    """
    if not isinstance(text, str):
        return 0

    lower_text = text.lower()
    for keyword in NEGATIVE_KEYWORDS:
        if keyword in lower_text:
            # If a negative keyword is found, force a strong negative polarity
            return -0.8  # A strong negative value, but not necessarily -1.0 to allow for nuance

    # If no explicit negative keywords, proceed with TextBlob analysis
    return TextBlob(text).sentiment.polarity

def calculate_sentiment_metrics(filtered_df: pd.DataFrame, app_details: Dict) -> Tuple:
    """
    Calculates various sentiment-related metrics for an app.

    Args:
        filtered_df (pd.DataFrame): DataFrame of filtered reviews with 'sentiment' column.
        app_details (Dict): Dictionary containing app details, including 'score'.

    Returns:
        tuple: (sentiment_counts, positive_pct, negative_pct, neutral_pct, app_rating_score, playstore_score)
    """
    sentiment_counts = filtered_df['sentiment'].value_counts()
    total_reviews = len(filtered_df)

    positive_pct = (sentiment_counts.get('Positive', 0) / total_reviews) * 100 if total_reviews > 0 else 0
    negative_pct = (sentiment_counts.get('Negative', 0) / total_reviews) * 100 if total_reviews > 0 else 0
    neutral_pct = (sentiment_counts.get('Neutral', 0) / total_reviews) * 100 if total_reviews > 0 else 0

    # Play Store score is usually out of 5, convert to percentage out of 100
    playstore_score = (app_details.get('score', 0.0)) * 20 if app_details and app_details.get('score') is not None else 0

    # Calculate app rating score based on sentiment distribution
    total_sentiment_reviews = sentiment_counts.get('Positive', 0) + sentiment_counts.get('Negative', 0) + sentiment_counts.get('Neutral', 0)
    if total_sentiment_reviews > 0:
        # A weighted average, giving more weight to positive, and some credit for neutral
        # This formula tries to approximate a score out of 100
        pos_score_calc = positive_pct + (neutral_pct * (positive_pct / (positive_pct + negative_pct)) if (positive_pct + negative_pct) > 0 else 0)
        app_rating_score = min(100, pos_score_calc)
    else:
        app_rating_score = 0  # No reviews to calculate score

    return sentiment_counts, positive_pct, negative_pct, neutral_pct, app_rating_score, playstore_score

def get_score_color(score: float, threshold: float = 30.0) -> str:
    """
    Get color for score based on threshold.
    
    Args:
        score (float): The score percentage.
        threshold (float): Fraud threshold.
        
    Returns:
        str: Bootstrap color class.
    """
    if score > threshold:
        return "danger"  # red
    elif score > threshold * 0.7:
        return "warning"  # yellow
    else:
        return "success"  # green

def detect_risk_keywords(text: str) -> List[str]:
    """
    Detect negative keywords in text.
    
    Args:
        text (str): The input text.
        
    Returns:
        List[str]: List of negative keywords found.
    """
    if not isinstance(text, str):
        return []
    
    found_keywords = []
    lower_text = text.lower()
    for keyword in NEGATIVE_KEYWORDS:
        if keyword in lower_text:
            found_keywords.append(keyword)
    
    return found_keywords


def compute_classification_metrics(filtered_df: pd.DataFrame, sample_each: int = 5) -> dict:
    """Compute simple classification metrics (accuracy, precision, recall, f1)

    Uses presence of NEGATIVE_KEYWORDS in the review text as a weak "ground truth"
    for negative reviews and compares against the predicted `sentiment` label.

    Returns a dict with:
      - accuracy, precision, recall, f1
      - confusion: dict with tp/tn/fp/fn counts
      - examples: dict with lists of up to `sample_each` example rows for tp/fp/fn/tn
    """
    try:
        if filtered_df is None or filtered_df.empty:
            return {
                'accuracy': 0.0, 'precision': 0.0, 'recall': 0.0, 'f1': 0.0,
                'confusion': {'tp': 0, 'tn': 0, 'fp': 0, 'fn': 0},
                'examples': {'tp': [], 'tn': [], 'fp': [], 'fn': []}
            }

        # Ground truth: contains any negative keyword
        def gt_negative(text):
            if not isinstance(text, str):
                return False
            lower = text.lower()
            return any(k in lower for k in NEGATIVE_KEYWORDS)

        y_true = filtered_df['content'].fillna('').apply(gt_negative)
        y_pred = filtered_df['sentiment'].fillna('').apply(lambda s: s == 'Negative')

        tp_mask = (y_true) & (y_pred)
        tn_mask = (~y_true) & (~y_pred)
        fp_mask = (~y_true) & (y_pred)
        fn_mask = (y_true) & (~y_pred)

        tp = int(tp_mask.sum())
        tn = int(tn_mask.sum())
        fp = int(fp_mask.sum())
        fn = int(fn_mask.sum())

        total = tp + tn + fp + fn
        accuracy = (tp + tn) / total if total > 0 else 0.0
        precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
        recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
        f1 = (2 * precision * recall) / (precision + recall) if (precision + recall) > 0 else 0.0

        # Build example lists (limit to sample_each each)
        examples = {'tp': [], 'tn': [], 'fp': [], 'fn': []}
        try:
            # Use DataFrame indices to get example rows
            for name, mask in (('tp', tp_mask), ('tn', tn_mask), ('fp', fp_mask), ('fn', fn_mask)):
                idxs = filtered_df[mask].head(sample_each).index.tolist()
                for i in idxs:
                    row = filtered_df.loc[i]
                    examples[name].append({
                        'content': str(row.get('content', '')),
                        'predicted': str(row.get('sentiment', '')),
                        'contains_negative_keyword': bool(gt_negative(row.get('content', ''))),
                        'score': row.get('score', None),
                        'at': row.get('at', None)
                    })
        except Exception:
            pass

        return {
            'accuracy': accuracy,
            'precision': precision,
            'recall': recall,
            'f1': f1,
            'confusion': {'tp': tp, 'tn': tn, 'fp': fp, 'fn': fn},
            'examples': examples
        }
    except Exception:
        return {
            'accuracy': 0.0, 'precision': 0.0, 'recall': 0.0, 'f1': 0.0,
            'confusion': {'tp': 0, 'tn': 0, 'fp': 0, 'fn': 0},
            'examples': {'tp': [], 'tn': [], 'fp': [], 'fn': []}
        }