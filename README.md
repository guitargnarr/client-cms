# Client CMS

Simple content management system for client demo sites.

## Architecture

```
client-cms/
├── api/           # FastAPI backend (deploy to Render)
│   ├── main.py
│   └── requirements.txt
└── admin/         # React admin panel (deploy to Vercel)
    └── src/App.tsx
```

## Quick Start

### 1. Run API locally

```bash
cd api
pip install -r requirements.txt
python main.py
# Running at http://localhost:8000
# Docs at http://localhost:8000/docs
```

### 2. Run Admin Panel locally

```bash
cd admin
npm install
npm run dev
# Running at http://localhost:5173
```

### 3. Login

- Site ID: `clater-jewelers` (or any configured site)
- Password: `demo123` (default for development)

## Deployment

### Deploy API to Render

1. Create new Web Service on Render
2. Connect GitHub repo
3. Root Directory: `client-cms/api`
4. Build Command: `pip install -r requirements.txt`
5. Start Command: `uvicorn main:app --host 0.0.0.0 --port $PORT`
6. Add environment variables for passwords:
   - `CLATER_PASSWORD=securepassword123`
   - `FRITZ_PASSWORD=securepassword456`

### Deploy Admin to Vercel

1. `cd admin && vercel --prod`
2. Set environment variable:
   - `VITE_API_URL=https://your-api.onrender.com`

## Adding a New Client Site

1. Add password to `SITE_PASSWORDS` dict in `api/main.py`
2. Or set environment variable: `{SITE_ID}_PASSWORD=xxx`

## Client Site Integration

In your client's React app, fetch content from the API:

```tsx
// In client site (e.g., clater-jewelers)
const API_URL = 'https://your-cms-api.onrender.com'

function App() {
  const [content, setContent] = useState(null)

  useEffect(() => {
    fetch(`${API_URL}/api/sites/clater-jewelers`)
      .then(res => res.json())
      .then(setContent)
  }, [])

  if (!content) return <Loading />

  return (
    <div>
      <h1>{content.business_name}</h1>
      {content.services.map(svc => (
        <ServiceCard key={svc.id} {...svc} />
      ))}
    </div>
  )
}
```

## API Endpoints

### Public (for client sites)
- `GET /api/sites/{site_id}` - Get all content
- `GET /api/sites/{site_id}/hours` - Get hours only
- `GET /api/sites/{site_id}/services` - Get services only
- `GET /api/sites/{site_id}/menu` - Get menu only

### Admin (requires X-Auth-Token header)
- `POST /api/auth/login` - Login, get token
- `PUT /api/admin/{site_id}` - Update all content
- `PUT /api/admin/{site_id}/hours` - Update hours
- `PUT /api/admin/{site_id}/services` - Update services
- `PUT /api/admin/{site_id}/menu` - Update menu
- `PUT /api/admin/{site_id}/staff` - Update staff
- `PUT /api/admin/{site_id}/promotions` - Update promotions

## Content Structure

```json
{
  "site_id": "clater-jewelers",
  "business_name": "Clater Jewelers",
  "tagline": "Where Louisville Finds Forever",
  "phone": "(502) 426-0077",
  "email": "info@claterjewelers.com",
  "address": "123 Main St, Louisville, KY",
  "hours": {
    "monday": "10am - 6pm",
    "tuesday": "10am - 6pm",
    ...
  },
  "services": [
    { "id": "svc-0", "title": "Custom Design", "description": "...", "price": "Starting at $500" }
  ],
  "staff": [
    { "id": "staff-0", "name": "John Smith", "role": "Owner", "bio": "..." }
  ],
  "menu_items": [],
  "promotions": [
    { "id": "promo-0", "title": "Holiday Sale", "description": "20% off", "active": true }
  ]
}
```

## Future Enhancements

- [ ] Image uploads (use Cloudinary or S3)
- [ ] PostgreSQL instead of JSON files
- [ ] Multi-user per site
- [ ] Preview before publish
- [ ] Revision history
