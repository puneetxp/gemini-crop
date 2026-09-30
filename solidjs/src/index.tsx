/* @refresh reload */
import { render } from "solid-js/web";
import { Router, Route } from "@solidjs/router";
import "./index.css";

import { App } from "./App";
import { Home } from "./pages/Home";
import { Dashboard } from "./pages/Dashboard";
import { SignIn } from "./pages/auth/SignIn";
import { SignUp } from "./pages/auth/SignUp";
import { FarmIndex } from "./pages/farm/Index";
import { FarmRegister } from "./pages/farm/Register";
import { FarmDashboard } from "./pages/farm/FarmDashboard";
import { FarmAnalytics } from "./pages/farm/FarmAnalytics";
import { PlotCreate } from "./pages/plots/Create";
import { PlantCrop } from "./pages/crops/PlantCrop";
import { MyCrops } from "./pages/crops/MyCrops";
import { Diagnose } from "./pages/crops/Diagnose";
import { AnnualStrategyDetail } from "./pages/crops/AnnualStrategyDetail";
import { SelectFarm } from "./pages/strategy/SelectFarm";
import { RequestStrategy } from "./pages/strategy/Request";
import { PashuHome } from "./pages/livestock/PashuHome";
import { LivestockHub } from "./pages/livestock/LivestockHub";
import { DietPlan } from "./pages/livestock/DietPlan";
import { VeterinaryDoctors } from "./pages/livestock/VeterinaryDoctors";
import { ClimateHub } from "./pages/climate/ClimateHub";
import { SoilFertilizerHub } from "./pages/soil/SoilFertilizerHub";
import { PestDiseaseHub } from "./pages/pest-disease/PestDiseaseHub";
import { MarketplaceBrowse } from "./pages/marketplace/Browse";
import { MarketplaceDetail } from "./pages/marketplace/Detail";
import { MyListings } from "./pages/marketplace/MyListings";
import { BuyerDashboard } from "./pages/marketplace/BuyerDashboard";
import { Bookings } from "./pages/marketplace/Bookings";
import { BookingDetails } from "./pages/marketplace/BookingDetails";
import { MarketIntelligence } from "./pages/marketplace/MarketIntelligence";
import { SupplyPlanning } from "./pages/marketplace/SupplyPlanning";
import { LivestockMarketplaceBrowse } from "./pages/livestock-marketplace/Browse";
import { TransportTracking } from "./pages/transport/TransportTracking";
import { PlatformAnalytics } from "./pages/admin/PlatformAnalytics";
import { QuotaMonitoring } from "./pages/admin/QuotaMonitoring";
import { Assistant } from "./pages/Assistant";
import { Configuration } from "./pages/Configuration";
import { Profile } from "./pages/users/Profile";
import { Security } from "./pages/users/Security";
import { Notifications } from "./pages/notifications/Notifications";
import { AllServices } from "./pages/AllServices";
import { ServicesDirectory } from "./pages/services/ServicesDirectory";
import { QuotaHistory } from "./pages/quota/QuotaHistory";
import { ProtectedRoute } from "./components/common/ProtectedRoute";

const root = document.getElementById("root");

if (import.meta.env.DEV && !(root instanceof HTMLElement)) {
  throw new Error("Root element not found.");
}

render(
  () => (
    <Router root={App}>
      {/* Public Routes */}
      <Route path="/" component={Home} />
      <Route path="/menu" component={AllServices} />
      <Route path="/auth/signin" component={SignIn} />
      <Route path="/auth/signup" component={SignUp} />
      <Route path="/marketplace" component={MarketplaceBrowse} />
      <Route
        path="/marketplace/my-listings"
        component={() => (
          <ProtectedRoute>
            <MyListings />
          </ProtectedRoute>
        )}
      />
      <Route
        path="/marketplace/buyer-dashboard"
        component={() => (
          <ProtectedRoute>
            <BuyerDashboard />
          </ProtectedRoute>
        )}
      />
      <Route
        path="/marketplace/intelligence"
        component={() => (
          <ProtectedRoute>
            <MarketIntelligence />
          </ProtectedRoute>
        )}
      />
      <Route
        path="/marketplace/supply-planning"
        component={() => (
          <ProtectedRoute>
            <SupplyPlanning />
          </ProtectedRoute>
        )}
      />
      <Route path="/marketplace/:id" component={MarketplaceDetail} />
      <Route path="/livestock-marketplace" component={LivestockMarketplaceBrowse} />
      <Route
        path="/transport/tracking"
        component={() => (
          <ProtectedRoute>
            <TransportTracking />
          </ProtectedRoute>
        )}
      />
      <Route
        path="/admin/analytics"
        component={() => (
          <ProtectedRoute>
            <PlatformAnalytics />
          </ProtectedRoute>
        )}
      />
      <Route
        path="/admin/quota"
        component={() => (
          <ProtectedRoute>
            <QuotaMonitoring />
          </ProtectedRoute>
        )}
      />

      {/* Protected Routes */}
      <Route
        path="/dashboard"
        component={() => (
          <ProtectedRoute>
            <Dashboard />
          </ProtectedRoute>
        )}
      />
      <Route
        path="/farm"
        component={() => (
          <ProtectedRoute>
            <FarmIndex />
          </ProtectedRoute>
        )}
      />
      <Route
        path="/farm/register"
        component={() => (
          <ProtectedRoute>
            <FarmRegister />
          </ProtectedRoute>
        )}
      />
      <Route
        path="/farm/:id"
        component={() => (
          <ProtectedRoute>
            <FarmDashboard />
          </ProtectedRoute>
        )}
      />
      <Route
        path="/analytics/farm/:id"
        component={() => (
          <ProtectedRoute>
            <FarmAnalytics />
          </ProtectedRoute>
        )}
      />
      <Route
        path="/plots/create"
        component={() => (
          <ProtectedRoute>
            <PlotCreate />
          </ProtectedRoute>
        )}
      />
      <Route
        path="/crops/plant"
        component={() => (
          <ProtectedRoute>
            <PlantCrop />
          </ProtectedRoute>
        )}
      />
      <Route
        path="/crops/my-crops"
        component={() => (
          <ProtectedRoute>
            <MyCrops />
          </ProtectedRoute>
        )}
      />
      <Route
        path="/diagnose"
        component={() => (
          <ProtectedRoute>
            <Diagnose />
          </ProtectedRoute>
        )}
      />
      <Route
        path="/crops/annual-strategy/:id"
        component={() => (
          <ProtectedRoute>
            <AnnualStrategyDetail />
          </ProtectedRoute>
        )}
      />
      <Route
        path="/strategy/select-farm"
        component={() => (
          <ProtectedRoute>
            <SelectFarm />
          </ProtectedRoute>
        )}
      />
      <Route
        path="/strategy/request"
        component={() => (
          <ProtectedRoute>
            <RequestStrategy />
          </ProtectedRoute>
        )}
      />
      <Route
        path="/strategy"
        component={() => (
          <ProtectedRoute>
            <SelectFarm />
          </ProtectedRoute>
        )}
      />
      <Route
        path="/livestock"
        component={() => (
          <ProtectedRoute>
            <PashuHome />
          </ProtectedRoute>
        )}
      />
      <Route
        path="/livestock/hub"
        component={() => (
          <ProtectedRoute>
            <LivestockHub />
          </ProtectedRoute>
        )}
      />
      <Route
        path="/livestock/diet-plan"
        component={() => (
          <ProtectedRoute>
            <DietPlan />
          </ProtectedRoute>
        )}
      />
      <Route
        path="/livestock/doctors"
        component={() => (
          <ProtectedRoute>
            <VeterinaryDoctors />
          </ProtectedRoute>
        )}
      />
      <Route
        path="/climate/hub"
        component={() => (
          <ProtectedRoute>
            <ClimateHub />
          </ProtectedRoute>
        )}
      />
      <Route
        path="/soil/hub"
        component={() => (
          <ProtectedRoute>
            <SoilFertilizerHub />
          </ProtectedRoute>
        )}
      />
      <Route
        path="/pest-disease/hub"
        component={() => (
          <ProtectedRoute>
            <PestDiseaseHub />
          </ProtectedRoute>
        )}
      />
      <Route
        path="/services"
        component={() => (
          <ProtectedRoute>
            <ServicesDirectory />
          </ProtectedRoute>
        )}
      />
      <Route
        path="/marketplace/bookings"
        component={() => (
          <ProtectedRoute>
            <Bookings />
          </ProtectedRoute>
        )}
      />
      <Route
        path="/marketplace/bookings/:id"
        component={() => (
          <ProtectedRoute>
            <BookingDetails />
          </ProtectedRoute>
        )}
      />
      <Route
        path="/assistant"
        component={() => (
          <ProtectedRoute>
            <Assistant />
          </ProtectedRoute>
        )}
      />
      <Route
        path="/settings"
        component={() => (
          <ProtectedRoute>
            <Configuration />
          </ProtectedRoute>
        )}
      />
      <Route
        path="/users/profile"
        component={() => (
          <ProtectedRoute>
            <Profile />
          </ProtectedRoute>
        )}
      />
      <Route
        path="/users/security"
        component={() => (
          <ProtectedRoute>
            <Security />
          </ProtectedRoute>
        )}
      />
      <Route
        path="/notifications"
        component={() => (
          <ProtectedRoute>
            <Notifications />
          </ProtectedRoute>
        )}
      />
      <Route
        path="/quota/history"
        component={() => (
          <ProtectedRoute>
            <QuotaHistory />
          </ProtectedRoute>
        )}
      />
    </Router>
  ),
  root!
);

// Register Progressive Web App Service Worker if supported
if ("serviceWorker" in navigator && !import.meta.env.DEV) {
  window.addEventListener("load", () => {
    navigator.serviceWorker.register("/sw.js").catch((err) => {
      console.warn("ServiceWorker registration failed:", err);
    });
  });
}
