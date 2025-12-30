"""
Google Trends API using pytrends
Provides keyword trend data for product opportunities
"""

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime, timedelta
import asyncio
from pytrends.request import TrendReq
import pandas as pd

app = FastAPI(title="Product Browser Trends API")

# CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:3001"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class TrendDataPoint(BaseModel):
    date: str
    value: int
    
class KeywordTrendResponse(BaseModel):
    keyword: str
    data: List[TrendDataPoint]
    current_volume: int  # Estimated from relative values
    growth_rate: float   # YoY growth percentage
    avg_volume: int
    max_volume: int
    min_volume: int
    timeframe: str

class MultiKeywordResponse(BaseModel):
    keywords: List[KeywordTrendResponse]
    comparison_data: List[dict]  # For overlaying multiple keywords


def get_pytrends_client():
    """Initialize pytrends client with retries"""
    return TrendReq(
        hl='en-US',
        tz=360,
        timeout=(10, 25),
        retries=2,
        backoff_factor=0.1
    )


def calculate_growth_rate(df: pd.DataFrame, keyword: str) -> float:
    """Calculate year-over-year growth rate"""
    if df.empty or len(df) < 12:
        return 0.0
    
    # Get last 12 months average vs previous 12 months
    recent_avg = df[keyword].tail(12).mean()
    previous_avg = df[keyword].head(12).mean() if len(df) >= 24 else df[keyword].head(len(df)//2).mean()
    
    if previous_avg == 0:
        return 0.0
    
    growth = ((recent_avg - previous_avg) / previous_avg) * 100
    return round(growth, 1)


def estimate_search_volume(relative_value: int, keyword: str) -> int:
    """
    Estimate actual search volume from relative Google Trends value.
    This is an approximation - for accurate volumes, use paid APIs like SEMrush.
    
    Base multiplier varies by keyword popularity. Using a conservative estimate.
    """
    # Base multiplier (this would ideally come from calibration with real data)
    base_multiplier = 100
    return int(relative_value * base_multiplier)


@app.get("/api/trends/keyword", response_model=KeywordTrendResponse)
async def get_keyword_trend(
    keyword: str = Query(..., description="Keyword to get trends for"),
    timeframe: str = Query("today 3-y", description="Timeframe: 'today 3-y', 'today 12-m', 'today 3-m'")
):
    """
    Get Google Trends data for a single keyword.
    
    Timeframes:
    - 'today 3-y': Last 3 years (weekly data)
    - 'today 12-m': Last 12 months (weekly data)
    - 'today 3-m': Last 3 months (daily data)
    """
    try:
        pytrends = get_pytrends_client()
        
        # Build payload
        pytrends.build_payload(
            kw_list=[keyword],
            timeframe=timeframe,
            geo='US'  # US market focus
        )
        
        # Get interest over time
        df = pytrends.interest_over_time()
        
        if df.empty:
            raise HTTPException(status_code=404, detail=f"No trend data found for '{keyword}'")
        
        # Remove isPartial column if exists
        if 'isPartial' in df.columns:
            df = df.drop('isPartial', axis=1)
        
        # Convert to response format
        data_points = []
        for date, row in df.iterrows():
            data_points.append(TrendDataPoint(
                date=date.strftime('%Y-%m-%d'),
                value=int(row[keyword])
            ))
        
        # Calculate metrics
        values = df[keyword].tolist()
        current_volume = estimate_search_volume(values[-1] if values else 0, keyword)
        avg_volume = estimate_search_volume(int(sum(values) / len(values)) if values else 0, keyword)
        max_volume = estimate_search_volume(max(values) if values else 0, keyword)
        min_volume = estimate_search_volume(min(values) if values else 0, keyword)
        growth_rate = calculate_growth_rate(df, keyword)
        
        return KeywordTrendResponse(
            keyword=keyword,
            data=data_points,
            current_volume=current_volume,
            growth_rate=growth_rate,
            avg_volume=avg_volume,
            max_volume=max_volume,
            min_volume=min_volume,
            timeframe=timeframe
        )
        
    except Exception as e:
        if "429" in str(e):
            raise HTTPException(status_code=429, detail="Rate limited by Google. Please try again later.")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/trends/compare", response_model=MultiKeywordResponse)
async def compare_keywords(
    keywords: str = Query(..., description="Comma-separated keywords (max 5)"),
    timeframe: str = Query("today 12-m", description="Timeframe for comparison")
):
    """
    Compare multiple keywords on the same chart.
    Google Trends allows max 5 keywords per comparison.
    """
    keyword_list = [k.strip() for k in keywords.split(",")][:5]
    
    if len(keyword_list) < 1:
        raise HTTPException(status_code=400, detail="At least one keyword required")
    
    try:
        pytrends = get_pytrends_client()
        
        pytrends.build_payload(
            kw_list=keyword_list,
            timeframe=timeframe,
            geo='US'
        )
        
        df = pytrends.interest_over_time()
        
        if df.empty:
            raise HTTPException(status_code=404, detail="No trend data found")
        
        if 'isPartial' in df.columns:
            df = df.drop('isPartial', axis=1)
        
        # Build response for each keyword
        keyword_responses = []
        for kw in keyword_list:
            if kw not in df.columns:
                continue
                
            data_points = []
            for date, row in df.iterrows():
                data_points.append(TrendDataPoint(
                    date=date.strftime('%Y-%m-%d'),
                    value=int(row[kw])
                ))
            
            values = df[kw].tolist()
            keyword_responses.append(KeywordTrendResponse(
                keyword=kw,
                data=data_points,
                current_volume=estimate_search_volume(values[-1] if values else 0, kw),
                growth_rate=calculate_growth_rate(df, kw),
                avg_volume=estimate_search_volume(int(sum(values) / len(values)) if values else 0, kw),
                max_volume=estimate_search_volume(max(values) if values else 0, kw),
                min_volume=estimate_search_volume(min(values) if values else 0, kw),
                timeframe=timeframe
            ))
        
        # Build comparison data for chart overlay
        comparison_data = []
        for date, row in df.iterrows():
            point = {"date": date.strftime('%Y-%m-%d')}
            for kw in keyword_list:
                if kw in df.columns:
                    point[kw] = int(row[kw])
            comparison_data.append(point)
        
        return MultiKeywordResponse(
            keywords=keyword_responses,
            comparison_data=comparison_data
        )
        
    except Exception as e:
        if "429" in str(e):
            raise HTTPException(status_code=429, detail="Rate limited by Google. Please try again later.")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/trends/related", response_model=dict)
async def get_related_queries(
    keyword: str = Query(..., description="Keyword to find related queries for")
):
    """Get related queries and rising queries for a keyword"""
    try:
        pytrends = get_pytrends_client()
        
        pytrends.build_payload(
            kw_list=[keyword],
            timeframe='today 12-m',
            geo='US'
        )
        
        related = pytrends.related_queries()
        
        result = {
            "keyword": keyword,
            "top_queries": [],
            "rising_queries": []
        }
        
        if keyword in related and related[keyword]['top'] is not None:
            top_df = related[keyword]['top']
            result["top_queries"] = top_df.head(10).to_dict('records')
        
        if keyword in related and related[keyword]['rising'] is not None:
            rising_df = related[keyword]['rising']
            result["rising_queries"] = rising_df.head(10).to_dict('records')
        
        return result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "trends-api"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)

