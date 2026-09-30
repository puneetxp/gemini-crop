# API Registry Usage Guide

The API registry provides a centralized, type-safe way to access all backend endpoints.

## Quick Start

```typescript
import { buildUrl, getEndpoint, apiRegistry } from './api-registry';

// Example 1: Get user's crop strategies
const url = buildUrl('crops', 'myStrategies');
// Result: "http://localhost:8000/api/v1/annual-strategy/list"

// Example 2: Get a specific farm with ID
const farmUrl = buildUrl('crops', 'getStrategy', { id: '123' });
// Result: "http://localhost:8000/api/v1/annual-strategy/123"

// Example 3: Direct endpoint access
const endpoint = getEndpoint('auth', 'login');
// Result: "/api/v1/auth/login"
```

## Available Categories

- `auth` - Authentication endpoints
- `users` - User profile management
- `farms` - Farm management
- `crops` - Crop strategies and recommendations
- `cropMilestones` - Crop milestone tracking
- `marketplace` - Marketplace listings
- `advanceBooking` - Advance booking system
- `marketData` - Market prices and trends
- `marketIntelligence` - Price tracking and analytics
- `weather` - Weather data and alerts
- `soil` - Soil testing and health
- `fertilizer` - Fertilizer recommendations
- `pestDisease` - Pest and disease management
- `livestock` - Livestock management
- `livestockTransactions` - Livestock buying/selling
- `transport` - Transport coordination
- `plotAnalysis` - Plot analysis and profitability
- `aiQuota` - AI usage quota tracking
- `address` - Address lookup and validation
- `analytics` - Platform analytics
- `upload` - File uploads
- `health` - Health check endpoints

## Integration with Existing Services

### Before (Hardcoded URLs):
```typescript
// ❌ Old way - hardcoded and error-prone
const response = await fetch('http://localhost:8000/api/v1/crops/my-strategies');
```

### After (Using Registry):
```typescript
// ✅ New way - centralized and type-safe
import { buildUrl } from '@/config/api-registry';

const url = buildUrl('crops', 'myStrategies');
const response = await fetch(url);
```

## Updating Service Files

### Example: crop.service.ts

```typescript
import { buildUrl } from '@/config/api-registry';

export const cropService = {
  async getMyStrategies() {
    const url = buildUrl('crops', 'myStrategies');
    return apiClient.get(url);
  },
  
  async getStrategy(id: string) {
    const url = buildUrl('crops', 'getStrategy', { id });
    return apiClient.get(url);
  },
  
  async createStrategy(data: any) {
    const url = buildUrl('crops', 'saveStrategy');
    return apiClient.post(url, data);
  }
};
```

## Regenerating the Registry

When backend endpoints change, regenerate the registry:

```bash
cd rural-farming-platform/python
python3 scripts/generate_api_registry_simple.py
```

This will update:
- `solidjs/src/config/api-registry.json` - The endpoint definitions
- `solidjs/src/config/api-registry.ts` - TypeScript helpers

## Benefits

1. **Single Source of Truth**: All endpoints defined in one place
2. **Type Safety**: TypeScript knows all available endpoints
3. **Easy Refactoring**: Change baseUrl in one place
4. **Auto-completion**: IDE suggests available endpoints
5. **Error Prevention**: Typos caught at compile time
6. **Documentation**: Self-documenting API structure
