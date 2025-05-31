from typing import Dict, Any, List
from datetime import datetime, timedelta

from src.server.config import (
    VP_1M_BARS_INTERVAL, VP_1M_LOOKBACK_HOURS,
    VP_5M_BARS_INTERVAL, VP_5M_LOOKBACK_DAYS,
    VP_1D_BARS_INTERVAL, VP_1D_LOOKBACK_MONTHS,
    TA_1M_INDICATOR_INTERVAL, TA_5M_INDICATOR_INTERVAL, TA_1D_INDICATOR_INTERVAL,
    TWELVE_DATA_OUTPUT_SIZE, PRICE_BANDING_WIDTH
)
from src.server.data import twelvedata_fetcher
from src.server.compute import technical_analysis


async def financial_technical_zones(symbol: str) -> Dict[str, Any]:
    """
    Retrieves calculated high-probability support and resistance price zones derived from methods like Volume Profile and volatility extensions for default granular timeframes (1m, 5m).
    Useful for identifying precise entry, exit, and stop-loss levels.
    """
    # Define the default timeframes and their specific data acquisition/calculation settings
    timeframes_config = {
        "1m": {
            "vp_bars_interval": VP_1M_BARS_INTERVAL,
            "vp_lookback_hours": VP_1M_LOOKBACK_HOURS,
            "ta_indicator_interval": TA_1M_INDICATOR_INTERVAL
        },
        "5m": {
            "vp_bars_interval": VP_5M_BARS_INTERVAL,
            "vp_lookback_days": VP_5M_LOOKBACK_DAYS,
            "ta_indicator_interval": TA_5M_INDICATOR_INTERVAL
        },
        "1d": {
            "vp_bars_interval": VP_1D_BARS_INTERVAL,
            "vp_lookback_months": VP_1D_LOOKBACK_MONTHS,
            "ta_indicator_interval": TA_1D_INDICATOR_INTERVAL
        }
    }

    response_time_utc = datetime.utcnow()
    adjusted_timestamp_utc = response_time_utc
    if adjusted_timestamp_utc.weekday() == 5: # Saturday
        adjusted_timestamp_utc -= timedelta(days=1)
    elif adjusted_timestamp_utc.weekday() == 6: # Sunday
        adjusted_timestamp_utc -= timedelta(days=2)

    timeframe_zones_data: Dict[str, Any] = {}
    overall_status = "success"
    overall_message = "Technical zones processed."

    for timeframe_key, tf_settings in timeframes_config.items():
        vp_bars_interval = tf_settings.get("vp_bars_interval")
        ta_indicator_interval = tf_settings.get("ta_indicator_interval")

        # Determine lookback duration based on timeframe config
        if "vp_lookback_hours" in tf_settings:
            vp_lookback_td = timedelta(hours=tf_settings["vp_lookback_hours"])
            lookback_description = f"Last ~{tf_settings['vp_lookback_hours']} hours"
        elif "vp_lookback_days" in tf_settings:
            vp_lookback_td = timedelta(days=tf_settings["vp_lookback_days"])
            lookback_description = f"Last ~{tf_settings['vp_lookback_days']} trading days"
        elif "vp_lookback_months" in tf_settings:
            vp_lookback_td = timedelta(days=tf_settings["vp_lookback_months"] * 30.44)
            lookback_description = f"Last ~{tf_settings['vp_lookback_months']} months"
        else:
            print(f"Error: No valid lookback defined for timeframe {timeframe_key}. Skipping {timeframe_key} zones.")
            overall_status = "partial_success" if overall_status == "success" else overall_status
            continue # Skip this timeframe

        start_date_utc = adjusted_timestamp_utc - vp_lookback_td
        start_date_str = start_date_utc.strftime("%Y-%m-%d %H:%M:%S")
        end_date_str = adjusted_timestamp_utc.strftime("%Y-%m-%d %H:%M:%S")

        technical_zones_list: List[Dict[str, Any]] = []
        frame_status = "success"
        frame_message = "Zones generated."
        frame_fetch_failed = False

        # --- 1. Fetch Raw Bar Data (for VP and Fibonacci) ---
        df_bars = twelvedata_fetcher.fetch_time_series(
            symbol=symbol,
            interval=vp_bars_interval,
            start_date=start_date_str,
            end_date=end_date_str,
            outputsize=TWELVE_DATA_OUTPUT_SIZE
        )

        if df_bars is None: # Critical fetch error
            print(f"Error fetching bars for {symbol} / {timeframe_key}. Calculations skipped.")
            frame_fetch_failed = True
        elif df_bars.empty: # Twelve Data returned no data for the period
            print(f"No bar data found for {symbol} / {timeframe_key}. Calculations skipped.")
            frame_status = "warning" if frame_status == "success" else frame_status
            frame_message = "No bar data available."
        else:
            # --- 2. Perform Local Volume Profile Calculation and Identify Zones ---
            vp_result = technical_analysis.calculate_volume_profile(df_bars, price_precision=2)

            if vp_result is None:
                print(f"Warning: Volume Profile calculation failed for {symbol} / {timeframe_key}. No VP zones.")
                frame_status = "partial_success" if frame_status == "success" else frame_status
                frame_message = "VP calculation failed."
            else:
                volume_profile_structure = vp_result

                # Add VP zones if calculation was successful
                if volume_profile_structure.get("point_of_control") is not None:
                    technical_zones_list.append({
                        "type": "NEUTRAL",
                        "name": f"{timeframe_key.upper()} POC",
                        "level": volume_profile_structure["point_of_control"],
                        "source": f"Volume Profile ({vp_bars_interval} Bars)"
                    })
                if volume_profile_structure.get("value_area_high") is not None:
                    range_end_approx = volume_profile_structure["value_area_high"] + (PRICE_BANDING_WIDTH / 2) if PRICE_BANDING_WIDTH else volume_profile_structure["value_area_high"]
                    technical_zones_list.append({
                        "type": "RESISTANCE",
                        "name": f"{timeframe_key.upper()} VAH",
                        "range_start": volume_profile_structure["value_area_high"],
                        "range_end": range_end_approx,
                        "source": f"Volume Profile ({vp_bars_interval} Bars)"
                    })
                if volume_profile_structure.get("value_area_low") is not None:
                    range_start_approx = volume_profile_structure["value_area_low"] - (PRICE_BANDING_WIDTH / 2) if PRICE_BANDING_WIDTH else volume_profile_structure["value_area_low"]
                    technical_zones_list.append({
                        "type": "SUPPORT",
                        "name": f"{timeframe_key.upper()} VAL",
                        "range_start": range_start_approx,
                        "range_end": volume_profile_structure["value_area_low"],
                        "source": f"Volume Profile ({vp_bars_interval} Bars)"
                    })
                # Add HVNs/LVNs if your calculate_volume_profile returns them
                for hvn in volume_profile_structure.get("high_volume_nodes", []):
                    hvn_end_approx = hvn["end"]
                    technical_zones_list.append({
                        "type": "RESISTANCE" if hvn["start"] > volume_profile_structure.get("point_of_control", -1) else "SUPPORT",
                        "name": f"{timeframe_key.upper()} HVN {round(hvn['start'], 2)}",
                        "range_start": hvn["start"],
                        "range_end": hvn_end_approx,
                        "source": f"Volume Profile ({vp_bars_interval} Bars)"
                    })
                for lvn in volume_profile_structure.get("low_volume_nodes", []):
                    lvn_end_approx = lvn["end"]
                    technical_zones_list.append({
                        "type": "NEUTRAL",
                        "name": f"{timeframe_key.upper()} LVN {round(lvn['start'], 2)}",
                        "range_start": lvn["start"],
                        "range_end": lvn_end_approx,
                        "source": f"Volume Profile ({vp_bars_interval} Bars)"
                    })

            # --- Calculate Fibonacci Zones ---
            fib_zones_list = technical_analysis.calculate_fibonacci_levels(df_bars, price_precision=2)

            if not fib_zones_list:
                print(f"Warning: Fibonacci calculation failed or returned no zones for {symbol} / {timeframe_key}. No Fib zones.")
                frame_status = "warning" if frame_status == "success" else frame_status
                if frame_message == "Zones generated." : frame_message = "VP zones generated, no Fib zones."
                elif frame_message == "VP calculation failed.": pass
                else: frame_message += " No Fib zones."
            else:
                # Add Fibonacci zones to the list
                technical_zones_list.extend(fib_zones_list)
                if frame_status == "success": frame_message = "VP and Fib zones generated."

        # --- 3. Fetch Standard TA Indicators needed for other zones (like ATR) ---
        atr_data = twelvedata_fetcher.fetch_atr(symbol, ta_indicator_interval, 14)

        atr_value = None
        if atr_data is None:
            print(f"Error fetching ATR for {symbol}/{timeframe_key}.")
            frame_fetch_failed = True
        elif not atr_data:
            print(f"No ATR data points returned for {symbol}/{timeframe_key}. Skipping ATR zones.")
        else:
            try:
                # Get the latest ATR value
                atr_value = float(atr_data[-1].get('atr'))
                if atr_value is None:
                    print(f"Warning: Last ATR data item for {symbol}/{timeframe_key} missing or invalid 'atr' value. Skipping ATR zones.")
                    frame_status = "partial_success" if frame_status == "success" else frame_status
                    if frame_message == "Zones generated.": frame_message = "VP/Fib zones generated, ATR error."
                    else: frame_message += " ATR error."
                    atr_value = None
            except (ValueError, TypeError, AttributeError) as e:
                print(f"Parse error ATR for {symbol}/{timeframe_key}: {e}. Skipping ATR zones.")
                frame_status = "partial_success" if frame_status == "success" else frame_status
                if frame_message == "Zones generated.": frame_message = "VP/Fib zones generated, ATR parse error."
                else: frame_message += " ATR parse error."
                atr_value = None

        # --- 4. Identify other zones (e.g., ATR extensions, Previous Day High/Low) ---
        # Example: ATR Extensions (using a fixed base like last close from VP bars or current price)
        if atr_value is not None and df_bars is not None and not df_bars.empty:
            # Use the last close price from df_bars as a base for ATR extensions
            base_price = float(df_bars['close'].iloc[-1]) if 'close' in df_bars.columns else None
            if base_price is not None:
                # Add 1x ATR extensions as potential targets/boundaries
                technical_zones_list.append({
                    "type": "TARGET_UPSIDE",
                    "name": f"{timeframe_key.upper()} +1 ATR",
                    "level": round(base_price + atr_value, 2),
                    "source": f"ATR Calculation ({ta_indicator_interval})"
                })
                technical_zones_list.append({
                    "type": "TARGET_DOWNSIDE",
                    "name": f"{timeframe_key.upper()} -1 ATR",
                    "level": round(base_price - atr_value, 2),
                    "source": f"ATR Calculation ({ta_indicator_interval})"
                })

        # Example: Previous Day High/Low (PDH/PDL) - Requires daily bar data
        if timeframe_key in ["1m", "5m"]: # These timeframes benefit from daily levels
            # Fetch the previous day's bar
            prev_day_start = adjusted_timestamp_utc - timedelta(days=2)
            prev_day_df = twelvedata_fetcher.fetch_time_series(
                symbol=symbol,
                interval="1day",
                start_date=prev_day_start.strftime("%Y-%m-%d %H:%M:%S"),
                end_date=adjusted_timestamp_utc.strftime("%Y-%m-%d %H:%M:%S"),
                outputsize=2
            )
            if prev_day_df is None:
                print(f"Error fetching previous day data for {symbol}/{timeframe_key}. Skipping PDH/PDL.")
                frame_fetch_failed = True
            elif prev_day_df.empty or len(prev_day_df) < 2:
                print(f"Not enough previous day data found for {symbol}/{timeframe_key}. Skipping PDH/PDL.")
            else:
                # The second to last bar is the previous trading day's completed bar
                prev_day_bar = prev_day_df.iloc[-2]
                pdh = float(prev_day_bar.get('high')) if prev_day_bar.get('high') is not None else None
                pdl = float(prev_day_bar.get('low')) if prev_day_bar.get('low') is not None else None

                if pdh is not None:
                    technical_zones_list.append({
                        "type": "RESISTANCE",
                        "name": "Previous Day High",
                        "level": round(pdh, 2),
                        "source": "Price Action (Daily Bar)"
                    })
                if pdl is not None:
                    technical_zones_list.append({
                        "type": "SUPPORT",
                        "name": "Previous Day Low",
                        "level": round(pdl, 2),
                        "source": "Price Action (Daily Bar)"
                    })

        # --- Store Results for this Timeframe ---
        if frame_fetch_failed:
            final_frame_status = "error"
            final_frame_message = "Critical fetch error for one or more data sources."
        elif not technical_zones_list:
            final_frame_status = "warning"
            final_frame_message = "No technical zones could be generated for this timeframe."
        else:
            final_frame_status = frame_status
            if frame_status == "partial_success":
                partial_messages = []
                if "VP calculation failed." in frame_message: partial_messages.append("VP failed.")
                if "No Fib zones." in frame_message: partial_messages.append("No Fib zones.")
                if "ATR error." in frame_message or ("ATR parse error." in frame_message and atr_value is None): partial_messages.append("ATR failed.")
                if partial_messages:
                    final_frame_message = "Some zones generated. Issues: " + ", ".join(partial_messages)
                else:
                    final_frame_message = "Zones generated successfully with minor issues."
            else:
                final_frame_message = "Zones generated successfully."

        timeframe_zones_data[timeframe_key] = {
            "calculation_context": {
                "bars_interval": vp_bars_interval,
                "lookback_description": lookback_description,
                "ta_indicator_interval": ta_indicator_interval,
            },
            "technical_zones": technical_zones_list,
            "status": final_frame_status,
            "message": final_frame_message
        }

        # Update overall status
        if final_frame_status == "error":
            overall_status = "error"
        elif final_frame_status in ["partial_success", "warning"] and overall_status == "success":
            overall_status = "partial_success"

    # --- 5. Construct Final Response ---
    if overall_status == "error":
        overall_message = "Critical errors occurred fetching/processing data for one or more timeframes. Check timeframe statuses."
    elif overall_status == "partial_success":
        overall_message = "Technical zones generated for some timeframes or some data/calculations failed. Check timeframe statuses."
    elif overall_status == "success" and not timeframe_zones_data:
        overall_status = "warning"
        overall_message = "No technical zones processed for any timeframe."
    elif overall_status == "success":
        overall_message = "All timeframes processed successfully."

    response_data: Dict[str, Any] = {
        "symbol": symbol,
        "timestamp_utc": response_time_utc.isoformat() + 'Z',
        "status": overall_status,
        "message": overall_message,
        "timeframe_zones": timeframe_zones_data
    }

    return response_data