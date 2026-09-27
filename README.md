# TeamBoard

B2B API for a curated technical knowledge base. Companies register, receive an API key and a JWT, and search Q&A entries. Every search is logged. Platform admins can read a usage summary.

## Setup

Requires Python 3.12+ and Docker.

```bash
cd teamboard
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

`.env` holds the Django secret and the Postgres credentials. `settings.py` reads them with `python-dotenv` and does not hardcode database passwords.

## Database

Start Postgres (and pgAdmin) from the project root:

```bash
docker compose up -d
```

Postgres is on `localhost:5432`. pgAdmin is at [http://localhost:5050](http://localhost:5050).

| | |
| --- | --- |
| pgAdmin email | `admin@teamboard.local` |
| pgAdmin password | `admin` |
| Postgres host | `db` from inside Docker, `localhost` from your machine |
| Postgres db / user / password | `teamboard` / `teamboard` / `teamboard` |

In pgAdmin, register a server with host `db`, port `5432`, and the credentials above.

Apply migrations:

```bash
python manage.py makemigrations api
python manage.py migrate
```

You should see `api_company`, `api_kbentry`, and `api_querylog`.

## Run the server

```bash
python manage.py runserver
```

The API is at `http://127.0.0.1:8000`.

## Seed knowledge-base entries

```bash
python manage.py seed_kb
```

This inserts 13 Q&A rows across the `api`, `database`, `cloud`, `framework`, and `general` categories. Several share keywords (`select_related`, `transaction.atomic`, `JWT`, `Q objects`, `signals`) so a search can return more than one hit. Running the command again does not duplicate rows.

## Endpoints

| Method | URL | Auth |
| --- | --- | --- |
| `POST` | `/api/auth/register/` | Public |
| `POST` | `/api/auth/login/` | Public |
| `POST` | `/api/kb/query/` | JWT |
| `GET` | `/api/admin/usage-summary/` | JWT, company role `admin` |

Register and login set `authentication_classes = []` and `permission_classes = []`. Every other endpoint uses the global JWT default.

### Register

```json
{
  "username": "acmecorp",
  "password": "securepass123",
  "company_name": "Acme Corp",
  "email": "dev@acmecorp.com"
}
```

`201` returns `username`, `company_name`, `api_key`, and `access`. A `post_save` signal on `User` creates the `Company` and sets `api_key` with `secrets.token_urlsafe(32)`. The view only writes `company_name`. `role` always stays `client`. A duplicate username returns `400`.

### Login

```json
{
  "username": "acmecorp",
  "password": "securepass123"
}
```

`200` returns `access`, `company_name`, and `api_key`. Invalid credentials return `401`.

### Query

```json
{ "search": "select_related" }
```

Send `Authorization: Bearer <access>`. The search matches `question` or `answer` with a case-insensitive `icontains`. The search and the `QueryLog` row are written in one `transaction.atomic()` block. A blank `search` returns `400`. No matches return `200` with `count: 0` and an empty `results` list, and the query is still logged. A missing token returns `401`.

### Usage summary

`GET /api/admin/usage-summary/` returns `total_queries`, `active_companies`, and the top 5 `top_search_terms`.

A client token returns `403`. `IsAdminUser` checks `request.user.company.role == "admin"`.

Promote a company in pgAdmin, or:

```bash
python manage.py shell -c "from django.contrib.auth.models import User; c=User.objects.get(username='acmecorp').company; c.role='admin'; c.save()"
```

Log in again after changing the role, then call the usage endpoint with the new access token.

## Postman

Import [`postman/TeamBoard.postman_collection.json`](postman/TeamBoard.postman_collection.json). Seed the knowledge base first, then run the requests from the top. The register and login requests store the access token in the collection variable `token`.

The last request, **Usage summary as admin — 200**, needs the company role changed to `admin` and a fresh login so `token` is an admin token.

## Tests

With Docker Postgres running:

```bash
python manage.py test
```
