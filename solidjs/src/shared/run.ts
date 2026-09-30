
import { isLogin } from "./guard/all";
import { indexdb } from "./indexdb";
import { createSignal, createMemo } from "solid-js";
import { Active_roleService } from './Service/Services';
import { Advance_bookingService } from './Service/Services';
import { Ai_usage_quotaService } from './Service/Services';
import { Annual_strategyService } from './Service/Services';
import { Breeding_recordService } from './Service/Services';
import { Buyer_interestService } from './Service/Services';
import { CropService } from './Service/Services';
import { Crop_diagnosisService } from './Service/Services';
import { Crop_expenseService } from './Service/Services';
import { Crop_market_dataService } from './Service/Services';
import { Crop_milestoneService } from './Service/Services';
import { Crop_profitabilityService } from './Service/Services';
import { FarmService } from './Service/Services';
import { Farm_plotService } from './Service/Services';
import { Fertilizer_applicationService } from './Service/Services';
import { Historical_yieldService } from './Service/Services';
import { LivestockService } from './Service/Services';
import { Livestock_health_recordService } from './Service/Services';
import { Livestock_listingService } from './Service/Services';
import { Livestock_marketplace_listingService } from './Service/Services';
import { Livestock_roi_predictionService } from './Service/Services';
import { Livestock_transactionService } from './Service/Services';
import { Market_priceService } from './Service/Services';
import { Marketplace_listingService } from './Service/Services';
import { Msp_rateService } from './Service/Services';
import { Ndap_downloaded_fileService } from './Service/Services';
import { Ndap_ingestion_runService } from './Service/Services';
import { OffspringService } from './Service/Services';
import { Opportunity_costService } from './Service/Services';
import { Payment_milestoneService } from './Service/Services';
import { Pest_disease_alertService } from './Service/Services';
import { Pest_disease_dataService } from './Service/Services';
import { Price_predictionService } from './Service/Services';
import { Push_subscriptionService } from './Service/Services';
import { Quality_verificationService } from './Service/Services';
import { RoleService } from './Service/Services';
import { Satellite_observationService } from './Service/Services';
import { Seasonal_trendService } from './Service/Services';
import { ServiceService } from './Service/Services';
import { Shc_state_district_codeService } from './Service/Services';
import { Slusi_ingestion_runService } from './Service/Services';
import { Slusi_lcc_reportService } from './Service/Services';
import { Slusi_microwatershed_mapService } from './Service/Services';
import { Soil_amendmentService } from './Service/Services';
import { Soil_moisture_dataService } from './Service/Services';
import { Soil_testService } from './Service/Services';
import { Soil_test_resultService } from './Service/Services';
import { Supply_matchService } from './Service/Services';
import { Supply_requestService } from './Service/Services';
import { System_settingService } from './Service/Services';
import { Transport_bookingService } from './Service/Services';
import { Transport_providerService } from './Service/Services';
import { UserService } from './Service/Services';
import { User_notificationService } from './Service/Services';
import { VeterinarianService } from './Service/Services';
import { Voice_assist_logService } from './Service/Services';
import { Weather_alertService } from './Service/Services';
import { Weather_forecastService } from './Service/Services';
export const tables: string[] = ["active_role","advance_booking","ai_usage_quota","annual_strategy","breeding_record","buyer_interest","crop","crop_diagnosis","crop_expense","crop_market_data","crop_milestone","crop_profitability","farm","farm_plot","fertilizer_application","historical_yield","livestock","livestock_health_record","livestock_listing","livestock_marketplace_listing","livestock_roi_prediction","livestock_transaction","market_price","marketplace_listing","msp_rate","ndap_downloaded_file","ndap_ingestion_run","offspring","opportunity_cost","payment_milestone","pest_disease_alert","pest_disease_data","price_prediction","push_subscription","quality_verification","role","satellite_observation","seasonal_trend","service","shc_state_district_code","slusi_ingestion_run","slusi_lcc_report","slusi_microwatershed_map","soil_amendment","soil_moisture_data","soil_test","soil_test_result","supply_match","supply_request","system_setting","transport_booking","transport_provider","user","user_notification","veterinarian","voice_assist_log","weather_alert","weather_forecast"];

const [set, setSet] = createSignal<string | false>(false);
export class run {
  set = createMemo(() => set());
  constructor() {
    isLogin()
      ? this.dbset()
        .then(() => {
          setSet(false);
        })
      : (indexdb.The_clearData(), setSet(false));
  }
  async dbset() {
    await Promise.all([
      Active_roleService.checkinit(),
      Advance_bookingService.checkinit(),
      Ai_usage_quotaService.checkinit(),
      Annual_strategyService.checkinit(),
      Breeding_recordService.checkinit(),
      Buyer_interestService.checkinit(),
      CropService.checkinit(),
      Crop_diagnosisService.checkinit(),
      Crop_expenseService.checkinit(),
      Crop_market_dataService.checkinit(),
      Crop_milestoneService.checkinit(),
      Crop_profitabilityService.checkinit(),
      FarmService.checkinit(),
      Farm_plotService.checkinit(),
      Fertilizer_applicationService.checkinit(),
      Historical_yieldService.checkinit(),
      LivestockService.checkinit(),
      Livestock_health_recordService.checkinit(),
      Livestock_listingService.checkinit(),
      Livestock_marketplace_listingService.checkinit(),
      Livestock_roi_predictionService.checkinit(),
      Livestock_transactionService.checkinit(),
      Market_priceService.checkinit(),
      Marketplace_listingService.checkinit(),
      Msp_rateService.checkinit(),
      Ndap_downloaded_fileService.checkinit(),
      Ndap_ingestion_runService.checkinit(),
      OffspringService.checkinit(),
      Opportunity_costService.checkinit(),
      Payment_milestoneService.checkinit(),
      Pest_disease_alertService.checkinit(),
      Pest_disease_dataService.checkinit(),
      Price_predictionService.checkinit(),
      Push_subscriptionService.checkinit(),
      Quality_verificationService.checkinit(),
      RoleService.checkinit(),
      Satellite_observationService.checkinit(),
      Seasonal_trendService.checkinit(),
      ServiceService.checkinit(),
      Shc_state_district_codeService.checkinit(),
      Slusi_ingestion_runService.checkinit(),
      Slusi_lcc_reportService.checkinit(),
      Slusi_microwatershed_mapService.checkinit(),
      Soil_amendmentService.checkinit(),
      Soil_moisture_dataService.checkinit(),
      Soil_testService.checkinit(),
      Soil_test_resultService.checkinit(),
      Supply_matchService.checkinit(),
      Supply_requestService.checkinit(),
      System_settingService.checkinit(),
      Transport_bookingService.checkinit(),
      Transport_providerService.checkinit(),
      UserService.checkinit(),
      User_notificationService.checkinit(),
      VeterinarianService.checkinit(),
      Voice_assist_logService.checkinit(),
      Weather_alertService.checkinit(),
      Weather_forecastService.checkinit(),
      ])
    }
}