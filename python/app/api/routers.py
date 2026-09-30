"""Router registry for the generated FastAPI application."""
from __future__ import annotations

from app.api.isuper.active_role.active_role import router as isuper_active_role_router
from app.api.islogin.active_role.active_role import router as islogin_active_role_router
from app.api.isuper.advance_booking.advance_booking import router as isuper_advance_booking_router
from app.api.islogin.advance_booking.advance_booking import router as islogin_advance_booking_router
from app.api.isuper.ai_usage_quota.ai_usage_quota import router as isuper_ai_usage_quota_router
from app.api.islogin.ai_usage_quota.ai_usage_quota import router as islogin_ai_usage_quota_router
from app.api.isuper.annual_strategy.annual_strategy import router as isuper_annual_strategy_router
from app.api.islogin.annual_strategy.annual_strategy import router as islogin_annual_strategy_router
from app.api.isuper.breeding_record.breeding_record import router as isuper_breeding_record_router
from app.api.islogin.breeding_record.breeding_record import router as islogin_breeding_record_router
from app.api.isuper.buyer_interest.buyer_interest import router as isuper_buyer_interest_router
from app.api.islogin.buyer_interest.buyer_interest import router as islogin_buyer_interest_router
from app.api.isuper.crop.crop import router as isuper_crop_router
from app.api.islogin.crop.crop import router as islogin_crop_router
from app.api.isuper.crop_diagnosis.crop_diagnosis import router as isuper_crop_diagnosis_router
from app.api.islogin.crop_diagnosis.crop_diagnosis import router as islogin_crop_diagnosis_router
from app.api.isuper.crop_expense.crop_expense import router as isuper_crop_expense_router
from app.api.islogin.crop_expense.crop_expense import router as islogin_crop_expense_router
from app.api.isuper.crop_market_data.crop_market_data import router as isuper_crop_market_data_router
from app.api.ipublic.crop_market_data.crop_market_data import router as ipublic_crop_market_data_router
from app.api.isuper.crop_milestone.crop_milestone import router as isuper_crop_milestone_router
from app.api.islogin.crop_milestone.crop_milestone import router as islogin_crop_milestone_router
from app.api.isuper.crop_profitability.crop_profitability import router as isuper_crop_profitability_router
from app.api.islogin.crop_profitability.crop_profitability import router as islogin_crop_profitability_router
from app.api.ipublic.crop_profitability.crop_profitability import router as ipublic_crop_profitability_router
from app.api.isuper.farm.farm import router as isuper_farm_router
from app.api.islogin.farm.farm import router as islogin_farm_router
from app.api.isuper.farm_plot.farm_plot import router as isuper_farm_plot_router
from app.api.islogin.farm_plot.farm_plot import router as islogin_farm_plot_router
from app.api.isuper.fertilizer_application.fertilizer_application import router as isuper_fertilizer_application_router
from app.api.islogin.fertilizer_application.fertilizer_application import router as islogin_fertilizer_application_router
from app.api.isuper.historical_yield.historical_yield import router as isuper_historical_yield_router
from app.api.islogin.historical_yield.historical_yield import router as islogin_historical_yield_router
from app.api.ipublic.historical_yield.historical_yield import router as ipublic_historical_yield_router
from app.api.isuper.livestock.livestock import router as isuper_livestock_router
from app.api.islogin.livestock.livestock import router as islogin_livestock_router
from app.api.isuper.livestock_health_record.livestock_health_record import router as isuper_livestock_health_record_router
from app.api.islogin.livestock_health_record.livestock_health_record import router as islogin_livestock_health_record_router
from app.api.isuper.livestock_listing.livestock_listing import router as isuper_livestock_listing_router
from app.api.islogin.livestock_listing.livestock_listing import router as islogin_livestock_listing_router
from app.api.ipublic.livestock_listing.livestock_listing import router as ipublic_livestock_listing_router
from app.api.isuper.livestock_marketplace_listing.livestock_marketplace_listing import router as isuper_livestock_marketplace_listing_router
from app.api.islogin.livestock_marketplace_listing.livestock_marketplace_listing import router as islogin_livestock_marketplace_listing_router
from app.api.isuper.livestock_roi_prediction.livestock_roi_prediction import router as isuper_livestock_roi_prediction_router
from app.api.islogin.livestock_roi_prediction.livestock_roi_prediction import router as islogin_livestock_roi_prediction_router
from app.api.isuper.livestock_transaction.livestock_transaction import router as isuper_livestock_transaction_router
from app.api.islogin.livestock_transaction.livestock_transaction import router as islogin_livestock_transaction_router
from app.api.isuper.market_price.market_price import router as isuper_market_price_router
from app.api.islogin.market_price.market_price import router as islogin_market_price_router
from app.api.ipublic.market_price.market_price import router as ipublic_market_price_router
from app.api.isuper.marketplace_listing.marketplace_listing import router as isuper_marketplace_listing_router
from app.api.islogin.marketplace_listing.marketplace_listing import router as islogin_marketplace_listing_router
from app.api.ipublic.marketplace_listing.marketplace_listing import router as ipublic_marketplace_listing_router
from app.api.isuper.msp_rate.msp_rate import router as isuper_msp_rate_router
from app.api.islogin.msp_rate.msp_rate import router as islogin_msp_rate_router
from app.api.ipublic.msp_rate.msp_rate import router as ipublic_msp_rate_router
from app.api.isuper.ndap_ingestion_run.ndap_ingestion_run import router as isuper_ndap_ingestion_run_router
from app.api.isuper.offspring.offspring import router as isuper_offspring_router
from app.api.islogin.offspring.offspring import router as islogin_offspring_router
from app.api.isuper.opportunity_cost.opportunity_cost import router as isuper_opportunity_cost_router
from app.api.islogin.opportunity_cost.opportunity_cost import router as islogin_opportunity_cost_router
from app.api.ipublic.opportunity_cost.opportunity_cost import router as ipublic_opportunity_cost_router
from app.api.isuper.payment_milestone.payment_milestone import router as isuper_payment_milestone_router
from app.api.islogin.payment_milestone.payment_milestone import router as islogin_payment_milestone_router
from app.api.isuper.pest_disease_alert.pest_disease_alert import router as isuper_pest_disease_alert_router
from app.api.islogin.pest_disease_alert.pest_disease_alert import router as islogin_pest_disease_alert_router
from app.api.isuper.pest_disease_data.pest_disease_data import router as isuper_pest_disease_data_router
from app.api.islogin.pest_disease_data.pest_disease_data import router as islogin_pest_disease_data_router
from app.api.isuper.price_prediction.price_prediction import router as isuper_price_prediction_router
from app.api.islogin.price_prediction.price_prediction import router as islogin_price_prediction_router
from app.api.ipublic.price_prediction.price_prediction import router as ipublic_price_prediction_router
from app.api.isuper.push_subscription.push_subscription import router as isuper_push_subscription_router
from app.api.isuper.quality_verification.quality_verification import router as isuper_quality_verification_router
from app.api.islogin.quality_verification.quality_verification import router as islogin_quality_verification_router
from app.api.isuper.role.role import router as isuper_role_router
from app.api.isuper.satellite_observation.satellite_observation import router as isuper_satellite_observation_router
from app.api.islogin.satellite_observation.satellite_observation import router as islogin_satellite_observation_router
from app.api.isuper.seasonal_trend.seasonal_trend import router as isuper_seasonal_trend_router
from app.api.islogin.seasonal_trend.seasonal_trend import router as islogin_seasonal_trend_router
from app.api.ipublic.seasonal_trend.seasonal_trend import router as ipublic_seasonal_trend_router
from app.api.roles.service_provider.service.service import router as service_provider_service_router
from app.api.isuper.service.service import router as isuper_service_router
from app.api.islogin.service.service import router as islogin_service_router
from app.api.ipublic.service.service import router as ipublic_service_router
from app.api.isuper.shc_state_district_code.shc_state_district_code import router as isuper_shc_state_district_code_router
from app.api.islogin.shc_state_district_code.shc_state_district_code import router as islogin_shc_state_district_code_router
from app.api.isuper.slusi_ingestion_run.slusi_ingestion_run import router as isuper_slusi_ingestion_run_router
from app.api.isuper.slusi_lcc_report.slusi_lcc_report import router as isuper_slusi_lcc_report_router
from app.api.islogin.slusi_lcc_report.slusi_lcc_report import router as islogin_slusi_lcc_report_router
from app.api.isuper.slusi_microwatershed_map.slusi_microwatershed_map import router as isuper_slusi_microwatershed_map_router
from app.api.islogin.slusi_microwatershed_map.slusi_microwatershed_map import router as islogin_slusi_microwatershed_map_router
from app.api.isuper.soil_amendment.soil_amendment import router as isuper_soil_amendment_router
from app.api.islogin.soil_amendment.soil_amendment import router as islogin_soil_amendment_router
from app.api.isuper.soil_moisture_data.soil_moisture_data import router as isuper_soil_moisture_data_router
from app.api.islogin.soil_moisture_data.soil_moisture_data import router as islogin_soil_moisture_data_router
from app.api.ipublic.soil_moisture_data.soil_moisture_data import router as ipublic_soil_moisture_data_router
from app.api.isuper.soil_test.soil_test import router as isuper_soil_test_router
from app.api.islogin.soil_test.soil_test import router as islogin_soil_test_router
from app.api.isuper.soil_test_result.soil_test_result import router as isuper_soil_test_result_router
from app.api.islogin.soil_test_result.soil_test_result import router as islogin_soil_test_result_router
from app.api.isuper.supply_match.supply_match import router as isuper_supply_match_router
from app.api.islogin.supply_match.supply_match import router as islogin_supply_match_router
from app.api.isuper.supply_request.supply_request import router as isuper_supply_request_router
from app.api.islogin.supply_request.supply_request import router as islogin_supply_request_router
from app.api.isuper.system_setting.system_setting import router as isuper_system_setting_router
from app.api.isuper.transport_booking.transport_booking import router as isuper_transport_booking_router
from app.api.islogin.transport_booking.transport_booking import router as islogin_transport_booking_router
from app.api.isuper.transport_provider.transport_provider import router as isuper_transport_provider_router
from app.api.islogin.transport_provider.transport_provider import router as islogin_transport_provider_router
from app.api.ipublic.transport_provider.transport_provider import router as ipublic_transport_provider_router
from app.api.isuper.user.user import router as isuper_user_router
from app.api.islogin.user.user import router as islogin_user_router
from app.api.isuper.user_notification.user_notification import router as isuper_user_notification_router
from app.api.islogin.user_notification.user_notification import router as islogin_user_notification_router
from app.api.isuper.veterinarian.veterinarian import router as isuper_veterinarian_router
from app.api.islogin.veterinarian.veterinarian import router as islogin_veterinarian_router
from app.api.ipublic.veterinarian.veterinarian import router as ipublic_veterinarian_router
from app.api.isuper.voice_assist_log.voice_assist_log import router as isuper_voice_assist_log_router
from app.api.islogin.voice_assist_log.voice_assist_log import router as islogin_voice_assist_log_router
from app.api.isuper.weather_alert.weather_alert import router as isuper_weather_alert_router
from app.api.islogin.weather_alert.weather_alert import router as islogin_weather_alert_router
from app.api.isuper.weather_forecast.weather_forecast import router as isuper_weather_forecast_router
from app.api.islogin.weather_forecast.weather_forecast import router as islogin_weather_forecast_router
from app.api.ipublic.weather_forecast.weather_forecast import router as ipublic_weather_forecast_router

all_routers = [
    isuper_active_role_router,
    islogin_active_role_router,
    isuper_advance_booking_router,
    islogin_advance_booking_router,
    isuper_ai_usage_quota_router,
    islogin_ai_usage_quota_router,
    isuper_annual_strategy_router,
    islogin_annual_strategy_router,
    isuper_breeding_record_router,
    islogin_breeding_record_router,
    isuper_buyer_interest_router,
    islogin_buyer_interest_router,
    isuper_crop_router,
    islogin_crop_router,
    isuper_crop_diagnosis_router,
    islogin_crop_diagnosis_router,
    isuper_crop_expense_router,
    islogin_crop_expense_router,
    isuper_crop_market_data_router,
    ipublic_crop_market_data_router,
    isuper_crop_milestone_router,
    islogin_crop_milestone_router,
    isuper_crop_profitability_router,
    islogin_crop_profitability_router,
    ipublic_crop_profitability_router,
    isuper_farm_router,
    islogin_farm_router,
    isuper_farm_plot_router,
    islogin_farm_plot_router,
    isuper_fertilizer_application_router,
    islogin_fertilizer_application_router,
    isuper_historical_yield_router,
    islogin_historical_yield_router,
    ipublic_historical_yield_router,
    isuper_livestock_router,
    islogin_livestock_router,
    isuper_livestock_health_record_router,
    islogin_livestock_health_record_router,
    isuper_livestock_listing_router,
    islogin_livestock_listing_router,
    ipublic_livestock_listing_router,
    isuper_livestock_marketplace_listing_router,
    islogin_livestock_marketplace_listing_router,
    isuper_livestock_roi_prediction_router,
    islogin_livestock_roi_prediction_router,
    isuper_livestock_transaction_router,
    islogin_livestock_transaction_router,
    isuper_market_price_router,
    islogin_market_price_router,
    ipublic_market_price_router,
    isuper_marketplace_listing_router,
    islogin_marketplace_listing_router,
    ipublic_marketplace_listing_router,
    isuper_msp_rate_router,
    islogin_msp_rate_router,
    ipublic_msp_rate_router,
    isuper_ndap_ingestion_run_router,
    isuper_offspring_router,
    islogin_offspring_router,
    isuper_opportunity_cost_router,
    islogin_opportunity_cost_router,
    ipublic_opportunity_cost_router,
    isuper_payment_milestone_router,
    islogin_payment_milestone_router,
    isuper_pest_disease_alert_router,
    islogin_pest_disease_alert_router,
    isuper_pest_disease_data_router,
    islogin_pest_disease_data_router,
    isuper_price_prediction_router,
    islogin_price_prediction_router,
    ipublic_price_prediction_router,
    isuper_push_subscription_router,
    isuper_quality_verification_router,
    islogin_quality_verification_router,
    isuper_role_router,
    isuper_satellite_observation_router,
    islogin_satellite_observation_router,
    isuper_seasonal_trend_router,
    islogin_seasonal_trend_router,
    ipublic_seasonal_trend_router,
    service_provider_service_router,
    isuper_service_router,
    islogin_service_router,
    ipublic_service_router,
    isuper_shc_state_district_code_router,
    islogin_shc_state_district_code_router,
    isuper_slusi_ingestion_run_router,
    isuper_slusi_lcc_report_router,
    islogin_slusi_lcc_report_router,
    isuper_slusi_microwatershed_map_router,
    islogin_slusi_microwatershed_map_router,
    isuper_soil_amendment_router,
    islogin_soil_amendment_router,
    isuper_soil_moisture_data_router,
    islogin_soil_moisture_data_router,
    ipublic_soil_moisture_data_router,
    isuper_soil_test_router,
    islogin_soil_test_router,
    isuper_soil_test_result_router,
    islogin_soil_test_result_router,
    isuper_supply_match_router,
    islogin_supply_match_router,
    isuper_supply_request_router,
    islogin_supply_request_router,
    isuper_system_setting_router,
    isuper_transport_booking_router,
    islogin_transport_booking_router,
    isuper_transport_provider_router,
    islogin_transport_provider_router,
    ipublic_transport_provider_router,
    isuper_user_router,
    islogin_user_router,
    isuper_user_notification_router,
    islogin_user_notification_router,
    isuper_veterinarian_router,
    islogin_veterinarian_router,
    ipublic_veterinarian_router,
    isuper_voice_assist_log_router,
    islogin_voice_assist_log_router,
    isuper_weather_alert_router,
    islogin_weather_alert_router,
    isuper_weather_forecast_router,
    islogin_weather_forecast_router,
    ipublic_weather_forecast_router,
]
