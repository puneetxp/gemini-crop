import { ModelService } from "./Service";
import { Active_role } from "../Interface/Model/Active_role";
import { Advance_booking } from "../Interface/Model/Advance_booking";
import { Ai_usage_quota } from "../Interface/Model/Ai_usage_quota";
import { Annual_strategy } from "../Interface/Model/Annual_strategy";
import { Breeding_record } from "../Interface/Model/Breeding_record";
import { Buyer_interest } from "../Interface/Model/Buyer_interest";
import { Crop } from "../Interface/Model/Crop";
import { Crop_diagnosis } from "../Interface/Model/Crop_diagnosis";
import { Crop_expense } from "../Interface/Model/Crop_expense";
import { Crop_market_data } from "../Interface/Model/Crop_market_data";
import { Crop_milestone } from "../Interface/Model/Crop_milestone";
import { Crop_profitability } from "../Interface/Model/Crop_profitability";
import { Farm } from "../Interface/Model/Farm";
import { Farm_plot } from "../Interface/Model/Farm_plot";
import { Fertilizer_application } from "../Interface/Model/Fertilizer_application";
import { Historical_yield } from "../Interface/Model/Historical_yield";
import { Livestock } from "../Interface/Model/Livestock";
import { Livestock_health_record } from "../Interface/Model/Livestock_health_record";
import { Livestock_listing } from "../Interface/Model/Livestock_listing";
import { Livestock_marketplace_listing } from "../Interface/Model/Livestock_marketplace_listing";
import { Livestock_roi_prediction } from "../Interface/Model/Livestock_roi_prediction";
import { Livestock_transaction } from "../Interface/Model/Livestock_transaction";
import { Market_price } from "../Interface/Model/Market_price";
import { Marketplace_listing } from "../Interface/Model/Marketplace_listing";
import { Msp_rate } from "../Interface/Model/Msp_rate";
import { Ndap_downloaded_file } from "../Interface/Model/Ndap_downloaded_file";
import { Ndap_ingestion_run } from "../Interface/Model/Ndap_ingestion_run";
import { Offspring } from "../Interface/Model/Offspring";
import { Opportunity_cost } from "../Interface/Model/Opportunity_cost";
import { Payment_milestone } from "../Interface/Model/Payment_milestone";
import { Pest_disease_alert } from "../Interface/Model/Pest_disease_alert";
import { Pest_disease_data } from "../Interface/Model/Pest_disease_data";
import { Price_prediction } from "../Interface/Model/Price_prediction";
import { Push_subscription } from "../Interface/Model/Push_subscription";
import { Quality_verification } from "../Interface/Model/Quality_verification";
import { Role } from "../Interface/Model/Role";
import { Satellite_observation } from "../Interface/Model/Satellite_observation";
import { Seasonal_trend } from "../Interface/Model/Seasonal_trend";
import { Service } from "../Interface/Model/Service";
import { Shc_state_district_code } from "../Interface/Model/Shc_state_district_code";
import { Slusi_ingestion_run } from "../Interface/Model/Slusi_ingestion_run";
import { Slusi_lcc_report } from "../Interface/Model/Slusi_lcc_report";
import { Slusi_microwatershed_map } from "../Interface/Model/Slusi_microwatershed_map";
import { Soil_amendment } from "../Interface/Model/Soil_amendment";
import { Soil_moisture_data } from "../Interface/Model/Soil_moisture_data";
import { Soil_test } from "../Interface/Model/Soil_test";
import { Soil_test_result } from "../Interface/Model/Soil_test_result";
import { Supply_match } from "../Interface/Model/Supply_match";
import { Supply_request } from "../Interface/Model/Supply_request";
import { System_setting } from "../Interface/Model/System_setting";
import { Transport_booking } from "../Interface/Model/Transport_booking";
import { Transport_provider } from "../Interface/Model/Transport_provider";
import { User } from "../Interface/Model/User";
import { User_notification } from "../Interface/Model/User_notification";
import { Veterinarian } from "../Interface/Model/Veterinarian";
import { Voice_assist_log } from "../Interface/Model/Voice_assist_log";
import { Weather_alert } from "../Interface/Model/Weather_alert";
import { Weather_forecast } from "../Interface/Model/Weather_forecast";

export const Active_roleService = (new ModelService<Active_role>())
    .seTable("active_role")
    .seturl("/islogin/active_role/");
export const Advance_bookingService = (new ModelService<Advance_booking>())
    .seTable("advance_booking")
    .seturl("/islogin/advance_booking/");
export const Ai_usage_quotaService = (new ModelService<Ai_usage_quota>())
    .seTable("ai_usage_quota")
    .seturl("/islogin/ai_usage_quota/");
export const Annual_strategyService = (new ModelService<Annual_strategy>())
    .seTable("annual_strategy")
    .seturl("/islogin/annual_strategy/");
export const Breeding_recordService = (new ModelService<Breeding_record>())
    .seTable("breeding_record")
    .seturl("/islogin/breeding_record/");
export const Buyer_interestService = (new ModelService<Buyer_interest>())
    .seTable("buyer_interest")
    .seturl("/islogin/buyer_interest/");
export const CropService = (new ModelService<Crop>())
    .seTable("crop")
    .seturl("/islogin/crop/");
export const Crop_diagnosisService = (new ModelService<Crop_diagnosis>())
    .seTable("crop_diagnosis")
    .seturl("/islogin/crop_diagnosis/");
export const Crop_expenseService = (new ModelService<Crop_expense>())
    .seTable("crop_expense")
    .seturl("/islogin/crop_expense/");
export const Crop_market_dataService = (new ModelService<Crop_market_data>())
    .seTable("crop_market_data")
    .seturl("/islogin/crop_market_data/");
export const Crop_milestoneService = (new ModelService<Crop_milestone>())
    .seTable("crop_milestone")
    .seturl("/islogin/crop_milestone/");
export const Crop_profitabilityService = (new ModelService<Crop_profitability>())
    .seTable("crop_profitability")
    .seturl("/islogin/crop_profitability/");
export const FarmService = (new ModelService<Farm>())
    .seTable("farm")
    .seturl("/islogin/farm/");
export const Farm_plotService = (new ModelService<Farm_plot>())
    .seTable("farm_plot")
    .seturl("/islogin/farm_plot/");
export const Fertilizer_applicationService = (new ModelService<Fertilizer_application>())
    .seTable("fertilizer_application")
    .seturl("/islogin/fertilizer_application/");
export const Historical_yieldService = (new ModelService<Historical_yield>())
    .seTable("historical_yield")
    .seturl("/islogin/historical_yield/");
export const LivestockService = (new ModelService<Livestock>())
    .seTable("livestock")
    .seturl("/islogin/livestock/");
export const Livestock_health_recordService = (new ModelService<Livestock_health_record>())
    .seTable("livestock_health_record")
    .seturl("/islogin/livestock_health_record/");
export const Livestock_listingService = (new ModelService<Livestock_listing>())
    .seTable("livestock_listing")
    .seturl("/islogin/livestock_listing/");
export const Livestock_marketplace_listingService = (new ModelService<Livestock_marketplace_listing>())
    .seTable("livestock_marketplace_listing")
    .seturl("/islogin/livestock_marketplace_listing/");
export const Livestock_roi_predictionService = (new ModelService<Livestock_roi_prediction>())
    .seTable("livestock_roi_prediction")
    .seturl("/islogin/livestock_roi_prediction/");
export const Livestock_transactionService = (new ModelService<Livestock_transaction>())
    .seTable("livestock_transaction")
    .seturl("/islogin/livestock_transaction/");
export const Market_priceService = (new ModelService<Market_price>())
    .seTable("market_price")
    .seturl("/islogin/market_price/");
export const Marketplace_listingService = (new ModelService<Marketplace_listing>())
    .seTable("marketplace_listing")
    .seturl("/islogin/marketplace_listing/");
export const Msp_rateService = (new ModelService<Msp_rate>())
    .seTable("msp_rate")
    .seturl("/islogin/msp_rate/");
export const Ndap_downloaded_fileService = (new ModelService<Ndap_downloaded_file>())
    .seTable("ndap_downloaded_file")
    .seturl("/islogin/ndap_downloaded_file/");
export const Ndap_ingestion_runService = (new ModelService<Ndap_ingestion_run>())
    .seTable("ndap_ingestion_run")
    .seturl("/islogin/ndap_ingestion_run/");
export const OffspringService = (new ModelService<Offspring>())
    .seTable("offspring")
    .seturl("/islogin/offspring/");
export const Opportunity_costService = (new ModelService<Opportunity_cost>())
    .seTable("opportunity_cost")
    .seturl("/islogin/opportunity_cost/");
export const Payment_milestoneService = (new ModelService<Payment_milestone>())
    .seTable("payment_milestone")
    .seturl("/islogin/payment_milestone/");
export const Pest_disease_alertService = (new ModelService<Pest_disease_alert>())
    .seTable("pest_disease_alert")
    .seturl("/islogin/pest_disease_alert/");
export const Pest_disease_dataService = (new ModelService<Pest_disease_data>())
    .seTable("pest_disease_data")
    .seturl("/islogin/pest_disease_data/");
export const Price_predictionService = (new ModelService<Price_prediction>())
    .seTable("price_prediction")
    .seturl("/islogin/price_prediction/");
export const Push_subscriptionService = (new ModelService<Push_subscription>())
    .seTable("push_subscription")
    .seturl("/islogin/push_subscription/");
export const Quality_verificationService = (new ModelService<Quality_verification>())
    .seTable("quality_verification")
    .seturl("/islogin/quality_verification/");
export const RoleService = (new ModelService<Role>())
    .seTable("role")
    .seturl("/islogin/role/");
export const Satellite_observationService = (new ModelService<Satellite_observation>())
    .seTable("satellite_observation")
    .seturl("/islogin/satellite_observation/");
export const Seasonal_trendService = (new ModelService<Seasonal_trend>())
    .seTable("seasonal_trend")
    .seturl("/islogin/seasonal_trend/");
export const ServiceService = (new ModelService<Service>())
    .seTable("service")
    .seturl("/islogin/service/");
export const Shc_state_district_codeService = (new ModelService<Shc_state_district_code>())
    .seTable("shc_state_district_code")
    .seturl("/islogin/shc_state_district_code/");
export const Slusi_ingestion_runService = (new ModelService<Slusi_ingestion_run>())
    .seTable("slusi_ingestion_run")
    .seturl("/islogin/slusi_ingestion_run/");
export const Slusi_lcc_reportService = (new ModelService<Slusi_lcc_report>())
    .seTable("slusi_lcc_report")
    .seturl("/islogin/slusi_lcc_report/");
export const Slusi_microwatershed_mapService = (new ModelService<Slusi_microwatershed_map>())
    .seTable("slusi_microwatershed_map")
    .seturl("/islogin/slusi_microwatershed_map/");
export const Soil_amendmentService = (new ModelService<Soil_amendment>())
    .seTable("soil_amendment")
    .seturl("/islogin/soil_amendment/");
export const Soil_moisture_dataService = (new ModelService<Soil_moisture_data>())
    .seTable("soil_moisture_data")
    .seturl("/islogin/soil_moisture_data/");
export const Soil_testService = (new ModelService<Soil_test>())
    .seTable("soil_test")
    .seturl("/islogin/soil_test/");
export const Soil_test_resultService = (new ModelService<Soil_test_result>())
    .seTable("soil_test_result")
    .seturl("/islogin/soil_test_result/");
export const Supply_matchService = (new ModelService<Supply_match>())
    .seTable("supply_match")
    .seturl("/islogin/supply_match/");
export const Supply_requestService = (new ModelService<Supply_request>())
    .seTable("supply_request")
    .seturl("/islogin/supply_request/");
export const System_settingService = (new ModelService<System_setting>())
    .seTable("system_setting")
    .seturl("/islogin/system_setting/");
export const Transport_bookingService = (new ModelService<Transport_booking>())
    .seTable("transport_booking")
    .seturl("/islogin/transport_booking/");
export const Transport_providerService = (new ModelService<Transport_provider>())
    .seTable("transport_provider")
    .seturl("/islogin/transport_provider/");
export const UserService = (new ModelService<User>())
    .seTable("user")
    .seturl("/islogin/user/");
export const User_notificationService = (new ModelService<User_notification>())
    .seTable("user_notification")
    .seturl("/islogin/user_notification/");
export const VeterinarianService = (new ModelService<Veterinarian>())
    .seTable("veterinarian")
    .seturl("/islogin/veterinarian/");
export const Voice_assist_logService = (new ModelService<Voice_assist_log>())
    .seTable("voice_assist_log")
    .seturl("/islogin/voice_assist_log/");
export const Weather_alertService = (new ModelService<Weather_alert>())
    .seTable("weather_alert")
    .seturl("/islogin/weather_alert/");
export const Weather_forecastService = (new ModelService<Weather_forecast>())
    .seTable("weather_forecast")
    .seturl("/islogin/weather_forecast/");
