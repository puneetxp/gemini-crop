#!/usr/bin/env python3
"""
Seed Minimum Support Price (MSP) rates for Kharif and Rabi seasons.
Seeds 2024-25 and 2025-26 official Indian Government MSP values.
"""

import sys
import os
from pathlib import Path
from decimal import Decimal

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.orm.msp_rate import MspRate


def seed_msp():
    print("====================================================")
    print("Seeding Official Minimum Support Prices (MSP)")
    print("====================================================")

    msp_data = [
        # --- Rabi Crops 2025-26 ---
        {
            "crop_name": "Wheat",
            "year": 2025,
            "season": "rabi",
            "msp_per_quintal": 2425.00,
            "msp_per_kg": 24.25,
            "increase_over_previous": 6.59,
            "cost_of_production": 1128.00,
            "return_over_cost_percent": 115.0,
            "source": "CACP / PIB"
        },
        {
            "crop_name": "Barley",
            "year": 2025,
            "season": "rabi",
            "msp_per_quintal": 1980.00,
            "msp_per_kg": 19.80,
            "increase_over_previous": 7.03,
            "cost_of_production": 1119.00,
            "return_over_cost_percent": 77.0,
            "source": "CACP / PIB"
        },
        {
            "crop_name": "Gram",
            "year": 2025,
            "season": "rabi",
            "msp_per_quintal": 5650.00,
            "msp_per_kg": 56.50,
            "increase_over_previous": 3.86,
            "cost_of_production": 3460.00,
            "return_over_cost_percent": 63.0,
            "source": "CACP / PIB"
        },
        {
            "crop_name": "Lentil (Masur)",
            "year": 2025,
            "season": "rabi",
            "msp_per_quintal": 6700.00,
            "msp_per_kg": 67.00,
            "increase_over_previous": 4.28,
            "cost_of_production": 3470.00,
            "return_over_cost_percent": 93.0,
            "source": "CACP / PIB"
        },
        {
            "crop_name": "Rapeseed & Mustard",
            "year": 2025,
            "season": "rabi",
            "msp_per_quintal": 5950.00,
            "msp_per_kg": 59.50,
            "increase_over_previous": 5.31,
            "cost_of_production": 3025.00,
            "return_over_cost_percent": 97.0,
            "source": "CACP / PIB"
        },
        {
            "crop_name": "Safflower",
            "year": 2025,
            "season": "rabi",
            "msp_per_quintal": 6100.00,
            "msp_per_kg": 61.00,
            "increase_over_previous": 5.17,
            "cost_of_production": 3935.00,
            "return_over_cost_percent": 55.0,
            "source": "CACP / PIB"
        },

        # --- Rabi Crops 2024-25 ---
        {
            "crop_name": "Wheat",
            "year": 2024,
            "season": "rabi",
            "msp_per_quintal": 2275.00,
            "msp_per_kg": 22.75,
            "increase_over_previous": 6.82,
            "cost_of_production": 1128.00,
            "return_over_cost_percent": 102.0,
            "source": "CACP / PIB"
        },
        {
            "crop_name": "Barley",
            "year": 2024,
            "season": "rabi",
            "msp_per_quintal": 1850.00,
            "msp_per_kg": 18.50,
            "increase_over_previous": 6.63,
            "cost_of_production": 1119.00,
            "return_over_cost_percent": 65.0,
            "source": "CACP / PIB"
        },
        {
            "crop_name": "Gram",
            "year": 2024,
            "season": "rabi",
            "msp_per_quintal": 5440.00,
            "msp_per_kg": 54.40,
            "increase_over_previous": 1.97,
            "cost_of_production": 3400.00,
            "return_over_cost_percent": 60.0,
            "source": "CACP / PIB"
        },

        # --- Kharif Crops 2024 ---
        {
            "crop_name": "Paddy",
            "year": 2024,
            "season": "kharif",
            "msp_per_quintal": 2300.00,
            "msp_per_kg": 23.00,
            "increase_over_previous": 5.35,
            "cost_of_production": 1420.00,
            "return_over_cost_percent": 62.0,
            "source": "CACP / PIB"
        },
        {
            "crop_name": "Bajra",
            "year": 2024,
            "season": "kharif",
            "msp_per_quintal": 2625.00,
            "msp_per_kg": 26.25,
            "increase_over_previous": 5.00,
            "cost_of_production": 1470.00,
            "return_over_cost_percent": 79.0,
            "source": "CACP / PIB"
        },
        {
            "crop_name": "Maize",
            "year": 2024,
            "season": "kharif",
            "msp_per_quintal": 2225.00,
            "msp_per_kg": 22.25,
            "increase_over_previous": 6.46,
            "cost_of_production": 1445.00,
            "return_over_cost_percent": 54.0,
            "source": "CACP / PIB"
        },
        {
            "crop_name": "Arhar",
            "year": 2024,
            "season": "kharif",
            "msp_per_quintal": 7550.00,
            "msp_per_kg": 75.50,
            "increase_over_previous": 7.86,
            "cost_of_production": 4580.00,
            "return_over_cost_percent": 65.0,
            "source": "CACP / PIB"
        },
        {
            "crop_name": "Moong",
            "year": 2024,
            "season": "kharif",
            "msp_per_quintal": 8682.00,
            "msp_per_kg": 86.82,
            "increase_over_previous": 1.45,
            "cost_of_production": 5780.00,
            "return_over_cost_percent": 50.0,
            "source": "CACP / PIB"
        },
        {
            "crop_name": "Urad",
            "year": 2024,
            "season": "kharif",
            "msp_per_quintal": 7400.00,
            "msp_per_kg": 74.00,
            "increase_over_previous": 6.47,
            "cost_of_production": 4720.00,
            "return_over_cost_percent": 57.0,
            "source": "CACP / PIB"
        },
        {
            "crop_name": "Groundnut",
            "year": 2024,
            "season": "kharif",
            "msp_per_quintal": 6783.00,
            "msp_per_kg": 67.83,
            "increase_over_previous": 6.37,
            "cost_of_production": 4485.00,
            "return_over_cost_percent": 51.0,
            "source": "CACP / PIB"
        },
        {
            "crop_name": "Soybean",
            "year": 2024,
            "season": "kharif",
            "msp_per_quintal": 4892.00,
            "msp_per_kg": 48.92,
            "increase_over_previous": 6.35,
            "cost_of_production": 3260.00,
            "return_over_cost_percent": 50.0,
            "source": "CACP / PIB"
        },
        {
            "crop_name": "Cotton",
            "year": 2024,
            "season": "kharif",
            "msp_per_quintal": 7121.00,
            "msp_per_kg": 71.21,
            "increase_over_previous": 7.57,
            "cost_of_production": 4747.00,
            "return_over_cost_percent": 50.0,
            "source": "CACP / PIB"
        }
    ]

    success = 0
    for record in msp_data:
        try:
            # Delete if exists to avoid conflicts
            MspRate.delete({
                'crop_name': record['crop_name'],
                'year': record['year'],
                'season': record['season']
            })
            # Create new record
            MspRate.create({**record, "enable": 1})
            print(f"✅ Seeded MSP for {record['crop_name']} ({record['year']} {record['season']})")
            success += 1
        except Exception as e:
            print(f"❌ Failed to seed {record['crop_name']}: {e}")

    print(f"\nSeeding complete! Successfully seeded {success} MSP records.")


if __name__ == "__main__":
    seed_msp()
