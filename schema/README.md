# Entity Schema Definitions (JSON)

JSON Schema definitions for platform entities stored in `data/*.json`.

Storage uses JSON files (not SQL). These schemas document the expected shape of each data file.

| Schema file | Data file |
|-------------|-----------|
| `users.schema.json` | `data/users.json` |
| `auth_sessions.schema.json` | Browser `localStorage.auth_sessions` (multi-role sessions) |
| `restaurants.schema.json` | `data/restaurants.json` |
| `delivery.schema.json` | `data/delivery.json` |
| `orders.schema.json` | Order create API + SQLite orders |
| `order_metadata.schema.json` | `data/order_metadata.json` |

### Delivery assignment lifecycle

`delivery_status` on assignments: `pending_acceptance` → `accepted` → `picked_up` → `in_transit` → `delivered`

Driver APIs: `POST /api/delivery/assignments/accept`, `POST /api/delivery/assignments/update-status`

### Live location tracking

- Driver shares GPS: `POST /api/delivery/location`
- Customer public map: `GET /api/delivery/live-track/{order_id}`
- Coordinates: `restaurants.json` (pickup), `order_metadata.json` (delivery_lat/lng), `delivery.json` driver_locations
