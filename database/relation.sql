ALTER TABLE active_roles ADD CONSTRAINT active_role_user_id_foreign FOREIGN KEY ("user_id") REFERENCES users ("id");
ALTER TABLE active_roles ADD CONSTRAINT active_role_role_id_foreign FOREIGN KEY ("role_id") REFERENCES roles ("id");

ALTER TABLE advance_bookings ADD CONSTRAINT advance_booking_listing_id_foreign FOREIGN KEY ("listing_id") REFERENCES marketplace_listings ("id");
ALTER TABLE advance_bookings ADD CONSTRAINT advance_booking_buyer_id_foreign FOREIGN KEY ("buyer_id") REFERENCES users ("id");
ALTER TABLE advance_bookings ADD CONSTRAINT advance_booking_farmer_id_foreign FOREIGN KEY ("farmer_id") REFERENCES users ("id");

ALTER TABLE ai_usage_quota ADD CONSTRAINT ai_usage_quota_user_id_foreign FOREIGN KEY ("user_id") REFERENCES users ("id");

ALTER TABLE annual_strategies ADD CONSTRAINT annual_strategy_farm_id_foreign FOREIGN KEY ("farm_id") REFERENCES farms ("id");
ALTER TABLE annual_strategies ADD CONSTRAINT annual_strategy_farmer_id_foreign FOREIGN KEY ("farmer_id") REFERENCES users ("id");

ALTER TABLE breeding_records ADD CONSTRAINT breeding_record_livestock_id_foreign FOREIGN KEY ("livestock_id") REFERENCES livestock ("id");
ALTER TABLE breeding_records ADD CONSTRAINT breeding_record_farmer_id_foreign FOREIGN KEY ("farmer_id") REFERENCES users ("id");
ALTER TABLE breeding_records ADD CONSTRAINT breeding_record_mate_id_foreign FOREIGN KEY ("mate_id") REFERENCES livestock ("id");

ALTER TABLE buyer_interests ADD CONSTRAINT buyer_interest_listing_id_foreign FOREIGN KEY ("listing_id") REFERENCES marketplace_listings ("id");

ALTER TABLE crops ADD CONSTRAINT crop_farm_plot_id_foreign FOREIGN KEY ("farm_plot_id") REFERENCES farm_plots ("id");
ALTER TABLE crops ADD CONSTRAINT crop_strategy_id_foreign FOREIGN KEY ("strategy_id") REFERENCES annual_strategies ("id");

ALTER TABLE crop_diagnoses ADD CONSTRAINT crop_diagnosis_user_id_foreign FOREIGN KEY ("user_id") REFERENCES users ("id");

ALTER TABLE crop_expenses ADD CONSTRAINT crop_expense_crop_id_foreign FOREIGN KEY ("crop_id") REFERENCES crops ("id");

ALTER TABLE crop_milestones ADD CONSTRAINT crop_milestone_crop_id_foreign FOREIGN KEY ("crop_id") REFERENCES crops ("id");

ALTER TABLE farms ADD CONSTRAINT farm_user_id_foreign FOREIGN KEY ("user_id") REFERENCES users ("id");
ALTER TABLE farms ADD CONSTRAINT farm_owner_id_foreign FOREIGN KEY ("owner_id") REFERENCES users ("id");

ALTER TABLE farm_plots ADD CONSTRAINT farm_plot_farm_id_foreign FOREIGN KEY ("farm_id") REFERENCES farms ("id");

ALTER TABLE fertilizer_applications ADD CONSTRAINT fertilizer_application_farm_id_foreign FOREIGN KEY ("farm_id") REFERENCES farms ("id");
ALTER TABLE fertilizer_applications ADD CONSTRAINT fertilizer_application_plot_id_foreign FOREIGN KEY ("plot_id") REFERENCES farm_plots ("id");
ALTER TABLE fertilizer_applications ADD CONSTRAINT fertilizer_application_crop_id_foreign FOREIGN KEY ("crop_id") REFERENCES crops ("id");
ALTER TABLE fertilizer_applications ADD CONSTRAINT fertilizer_application_soil_test_before_id_foreign FOREIGN KEY ("soil_test_before_id") REFERENCES soil_test_results ("id");
ALTER TABLE fertilizer_applications ADD CONSTRAINT fertilizer_application_soil_test_after_id_foreign FOREIGN KEY ("soil_test_after_id") REFERENCES soil_test_results ("id");

ALTER TABLE livestock ADD CONSTRAINT livestock_farm_id_foreign FOREIGN KEY ("farm_id") REFERENCES farms ("id");
ALTER TABLE livestock ADD CONSTRAINT livestock_farmer_id_foreign FOREIGN KEY ("farmer_id") REFERENCES users ("id");

ALTER TABLE livestock_health_records ADD CONSTRAINT livestock_health_record_livestock_id_foreign FOREIGN KEY ("livestock_id") REFERENCES livestock ("id");

ALTER TABLE livestock_listings ADD CONSTRAINT livestock_listing_livestock_id_foreign FOREIGN KEY ("livestock_id") REFERENCES livestock ("id");
ALTER TABLE livestock_listings ADD CONSTRAINT livestock_listing_farmer_id_foreign FOREIGN KEY ("farmer_id") REFERENCES users ("id");

ALTER TABLE livestock_marketplace_listings ADD CONSTRAINT livestock_marketplace_listing_livestock_id_foreign FOREIGN KEY ("livestock_id") REFERENCES livestock ("id");
ALTER TABLE livestock_marketplace_listings ADD CONSTRAINT livestock_marketplace_listing_farmer_id_foreign FOREIGN KEY ("farmer_id") REFERENCES users ("id");

ALTER TABLE livestock_roi_predictions ADD CONSTRAINT livestock_roi_prediction_animal_id_foreign FOREIGN KEY ("animal_id") REFERENCES livestock ("id");
ALTER TABLE livestock_roi_predictions ADD CONSTRAINT livestock_roi_prediction_user_id_foreign FOREIGN KEY ("user_id") REFERENCES users ("id");

ALTER TABLE livestock_transactions ADD CONSTRAINT livestock_transaction_listing_id_foreign FOREIGN KEY ("listing_id") REFERENCES livestock_listings ("id");
ALTER TABLE livestock_transactions ADD CONSTRAINT livestock_transaction_seller_id_foreign FOREIGN KEY ("seller_id") REFERENCES users ("id");
ALTER TABLE livestock_transactions ADD CONSTRAINT livestock_transaction_buyer_id_foreign FOREIGN KEY ("buyer_id") REFERENCES users ("id");

ALTER TABLE market_prices ADD CONSTRAINT market_price_listing_id_foreign FOREIGN KEY ("listing_id") REFERENCES marketplace_listings ("id");
ALTER TABLE market_prices ADD CONSTRAINT market_price_booking_id_foreign FOREIGN KEY ("booking_id") REFERENCES advance_bookings ("id");
ALTER TABLE market_prices ADD CONSTRAINT market_price_transaction_id_foreign FOREIGN KEY ("transaction_id") REFERENCES livestock_transactions ("id");

ALTER TABLE marketplace_listings ADD CONSTRAINT marketplace_listing_farm_id_foreign FOREIGN KEY ("farm_id") REFERENCES farms ("id");
ALTER TABLE marketplace_listings ADD CONSTRAINT marketplace_listing_farmer_id_foreign FOREIGN KEY ("farmer_id") REFERENCES users ("id");

ALTER TABLE offspring ADD CONSTRAINT offspring_breeding_record_id_foreign FOREIGN KEY ("breeding_record_id") REFERENCES breeding_records ("id");
ALTER TABLE offspring ADD CONSTRAINT offspring_livestock_id_foreign FOREIGN KEY ("livestock_id") REFERENCES livestock ("id");
ALTER TABLE offspring ADD CONSTRAINT offspring_farmer_id_foreign FOREIGN KEY ("farmer_id") REFERENCES users ("id");

ALTER TABLE payment_milestones ADD CONSTRAINT payment_milestone_booking_id_foreign FOREIGN KEY ("booking_id") REFERENCES advance_bookings ("id");

ALTER TABLE pest_disease_alerts ADD CONSTRAINT pest_disease_alert_crop_id_foreign FOREIGN KEY ("crop_id") REFERENCES crops ("id");
ALTER TABLE pest_disease_alerts ADD CONSTRAINT pest_disease_alert_farm_id_foreign FOREIGN KEY ("farm_id") REFERENCES farms ("id");

ALTER TABLE quality_verifications ADD CONSTRAINT quality_verification_booking_id_foreign FOREIGN KEY ("booking_id") REFERENCES advance_bookings ("id");

ALTER TABLE satellite_observations ADD CONSTRAINT satellite_observation_farm_id_foreign FOREIGN KEY ("farm_id") REFERENCES farms ("id");

ALTER TABLE soil_amendments ADD CONSTRAINT soil_amendment_plot_id_foreign FOREIGN KEY ("plot_id") REFERENCES farm_plots ("id");
ALTER TABLE soil_amendments ADD CONSTRAINT soil_amendment_follow_up_soil_test_id_foreign FOREIGN KEY ("follow_up_soil_test_id") REFERENCES soil_tests ("id");

ALTER TABLE soil_tests ADD CONSTRAINT soil_test_plot_id_foreign FOREIGN KEY ("plot_id") REFERENCES farm_plots ("id");

ALTER TABLE soil_test_results ADD CONSTRAINT soil_test_result_farm_id_foreign FOREIGN KEY ("farm_id") REFERENCES farms ("id");
ALTER TABLE soil_test_results ADD CONSTRAINT soil_test_result_plot_id_foreign FOREIGN KEY ("plot_id") REFERENCES farm_plots ("id");

ALTER TABLE supply_matches ADD CONSTRAINT supply_match_request_id_foreign FOREIGN KEY ("request_id") REFERENCES supply_requests ("id");
ALTER TABLE supply_matches ADD CONSTRAINT supply_match_listing_id_foreign FOREIGN KEY ("listing_id") REFERENCES marketplace_listings ("id");
ALTER TABLE supply_matches ADD CONSTRAINT supply_match_farmer_id_foreign FOREIGN KEY ("farmer_id") REFERENCES users ("id");

ALTER TABLE supply_requests ADD CONSTRAINT supply_request_buyer_id_foreign FOREIGN KEY ("buyer_id") REFERENCES users ("id");

ALTER TABLE transport_bookings ADD CONSTRAINT transport_booking_transaction_id_foreign FOREIGN KEY ("transaction_id") REFERENCES livestock_transactions ("id");
ALTER TABLE transport_bookings ADD CONSTRAINT transport_booking_provider_id_foreign FOREIGN KEY ("provider_id") REFERENCES transport_providers ("id");
ALTER TABLE transport_bookings ADD CONSTRAINT transport_booking_requester_id_foreign FOREIGN KEY ("requester_id") REFERENCES users ("id");

ALTER TABLE transport_providers ADD CONSTRAINT transport_provider_user_id_foreign FOREIGN KEY ("user_id") REFERENCES users ("id");

ALTER TABLE user_notifications ADD CONSTRAINT user_notification_user_id_foreign FOREIGN KEY ("user_id") REFERENCES users ("id");

ALTER TABLE voice_assist_logs ADD CONSTRAINT voice_assist_log_user_id_foreign FOREIGN KEY ("user_id") REFERENCES users ("id");

ALTER TABLE weather_alerts ADD CONSTRAINT weather_alert_farm_id_foreign FOREIGN KEY ("farm_id") REFERENCES farms ("id");